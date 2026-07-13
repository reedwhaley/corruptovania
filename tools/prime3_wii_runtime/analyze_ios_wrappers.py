from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[2]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

from randovania.games.prime3.exporter.dol_patcher import decode_ppc_unconditional_branch, parse_dol_header

PRIME3_NTSC_RETAIL_DOL_SHA256 = "6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104"
PRIME3_NTSC_RETAIL_CLUSTER = {
    "open_async": 0x80504668,
    "open": 0x80504780,
    "close_async": 0x805048A0,
    "close": 0x80504960,
    "ioctl_async": 0x80504A08,
    "ioctl": 0x80504B08,
    "ioctlv_async": 0x80504C10,
    "ioctlv": 0x80504D10,
}


@dataclasses.dataclass(frozen=True)
class DevicePath:
    text: str
    virtual_address: int
    file_offset: int


@dataclasses.dataclass(frozen=True)
class StringReference:
    target_address: int
    instruction_address: int
    register: int
    form: str


@dataclasses.dataclass(frozen=True)
class CallSite:
    call_address: int
    target_address: int
    path_register: int
    path_address: int


@dataclasses.dataclass(frozen=True)
class WrapperCandidate:
    address: int
    command_id: int
    alloc_helper_address: int
    submit_helper_address: int
    guard_words: tuple[int, ...]
    kind: str


def _read_word(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


def _decode_simm(word: int) -> int:
    value = word & 0xFFFF
    return value if value < 0x8000 else value - 0x10000


def find_device_paths(dol_bytes: bytes) -> list[DevicePath]:
    header = parse_dol_header(dol_bytes)
    found: list[DevicePath] = []
    seen: set[str] = set()
    for section in header.sections:
        if section.size <= 0:
            continue
        blob = dol_bytes[section.file_offset : section.file_offset + section.size]
        cursor = 0
        while True:
            start = blob.find(b"/dev/", cursor)
            if start < 0:
                break
            end = blob.find(b"\x00", start)
            if end < 0:
                break
            text = blob[start:end].decode("ascii", "replace")
            if text not in seen:
                seen.add(text)
                found.append(
                    DevicePath(
                        text=text,
                        virtual_address=section.address + start,
                        file_offset=section.file_offset + start,
                    )
                )
            cursor = end + 1
    return found


def find_string_references(
    dol_bytes: bytes,
    target_address: int,
    *,
    max_gap_instructions: int = 8,
) -> list[StringReference]:
    header = parse_dol_header(dol_bytes)
    results: list[StringReference] = []
    target_hi = (target_address >> 16) & 0xFFFF
    for section in header.text_sections():
        blob = dol_bytes[section.file_offset : section.file_offset + section.size]
        for offset in range(0, len(blob) - 4, 4):
            word = _read_word(blob, offset)
            if word >> 26 != 15 or (word & 0xFFFF) != target_hi:
                continue
            reg = (word >> 21) & 31
            base = (_decode_simm(word) << 16) & 0xFFFFFFFF
            for gap in range(1, max_gap_instructions + 1):
                next_offset = offset + gap * 4
                if next_offset >= len(blob):
                    break
                next_word = _read_word(blob, next_offset)
                op = next_word >> 26
                rt = (next_word >> 21) & 31
                ra = (next_word >> 16) & 31
                if rt != reg or ra != reg:
                    continue
                value = None
                form = None
                if op == 14:
                    value = (base + _decode_simm(next_word)) & 0xFFFFFFFF
                    form = "lis/addi"
                elif op == 24:
                    value = (base | (next_word & 0xFFFF)) & 0xFFFFFFFF
                    form = "lis/ori"
                if value == target_address and form is not None:
                    results.append(
                        StringReference(
                            target_address=target_address,
                            instruction_address=section.address + offset,
                            register=reg,
                            form=form,
                        )
                    )
                    break
    return results


def find_calls_following_string_reference(
    dol_bytes: bytes,
    reference: StringReference,
    *,
    search_span_instructions: int = 10,
) -> list[CallSite]:
    header = parse_dol_header(dol_bytes)
    section = header.section_for_address(reference.instruction_address)
    if section is None:
        return []
    results: list[CallSite] = []
    start = header.offset_for_address(reference.instruction_address)
    assert start is not None
    end = min(section.end_offset, start + (search_span_instructions + 1) * 4)
    for offset in range(start + 4, end, 4):
        address = header.address_for_offset(offset)
        assert address is not None
        decoded = decode_ppc_unconditional_branch(_read_word(dol_bytes, offset), address)
        if decoded is None or not decoded.link:
            continue
        results.append(
            CallSite(
                call_address=address,
                target_address=decoded.target_address,
                path_register=reference.register,
                path_address=reference.target_address,
            )
        )
    return results


def score_wrapper_cluster(candidates: list[WrapperCandidate]) -> int:
    if len(candidates) < 4:
        return 0
    command_ids = {candidate.command_id for candidate in candidates}
    if not {1, 2, 3, 4}.issubset(command_ids):
        return 0
    alloc_helpers = {candidate.alloc_helper_address for candidate in candidates}
    submit_helpers = {candidate.submit_helper_address for candidate in candidates}
    if len(alloc_helpers) != 1 or len(submit_helpers) != 1:
        return 0
    if any(len(candidate.guard_words) < 2 for candidate in candidates):
        return 0
    async_kinds = {candidate.kind for candidate in candidates if candidate.kind.endswith("_async")}
    sync_kinds = {candidate.kind for candidate in candidates if not candidate.kind.endswith("_async")}
    if len(async_kinds) < 2 or len(sync_kinds) < 2:
        return 0
    return len(candidates)


def _default_report(dol_bytes: bytes) -> dict[str, object]:
    digest = hashlib.sha256(dol_bytes).hexdigest()
    device_paths = [dataclasses.asdict(path) for path in find_device_paths(dol_bytes)]
    report: dict[str, object] = {
        "dol_sha256": digest,
        "device_paths": device_paths,
        "verified_cluster": None,
    }
    if digest == PRIME3_NTSC_RETAIL_DOL_SHA256:
        report["verified_cluster"] = {
            "supported_dol_sha256": PRIME3_NTSC_RETAIL_DOL_SHA256,
            "functions": PRIME3_NTSC_RETAIL_CLUSTER,
            "submit_helper_address": 0x8050441C,
            "request_allocator_address": 0x80505960,
            "callback_signature": "s32 callback(s32 result, void *userdata)",
            "evidence": [
                "coherent command-1..6 wrapper cluster",
                "real Prime 3 async-open callsite at 0x80501858",
                "neighboring sync open callsites for /dev/stm/*",
            ],
        }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("dol_path", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = _default_report(args.dol_path.read_bytes())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(text)
    else:
        args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
