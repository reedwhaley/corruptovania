from __future__ import annotations

import hashlib
import sys
from importlib import util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT.joinpath("tools", "prime3_wii_runtime", "analyze_ios_wrappers.py")


def _load_module(module_name: str = "prime3_wii_runtime_analyze_ios_wrappers_test"):
    spec = util.spec_from_file_location(module_name, MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _encode_lis(register: int, immediate: int) -> int:
    return (15 << 26) | (register << 21) | (immediate & 0xFFFF)


def _encode_addi(rt: int, ra: int, immediate: int) -> int:
    return (14 << 26) | (rt << 21) | (ra << 16) | (immediate & 0xFFFF)


def _encode_ori(rt: int, ra: int, immediate: int) -> int:
    return (24 << 26) | (rt << 21) | (ra << 16) | (immediate & 0xFFFF)


def _encode_bl(source: int, target: int) -> int:
    delta = target - source
    return 0x48000001 | (delta & 0x03FFFFFC)


def _build_dol(*, text_address: int, text_words: list[int], data_address: int, data_bytes: bytes) -> bytes:
    text_blob = b"".join(word.to_bytes(4, "big") for word in text_words)
    text_offset = 0x100
    data_offset = text_offset + len(text_blob)
    header = bytearray(0x100)
    header[0:4] = text_offset.to_bytes(4, "big")
    header[0x1C:0x20] = data_offset.to_bytes(4, "big")
    header[0x48:0x4C] = text_address.to_bytes(4, "big")
    header[0x64:0x68] = data_address.to_bytes(4, "big")
    header[0x90:0x94] = len(text_blob).to_bytes(4, "big")
    header[0xAC:0xB0] = len(data_bytes).to_bytes(4, "big")
    header[0xE0:0xE4] = text_address.to_bytes(4, "big")
    return bytes(header) + text_blob + data_bytes


def test_find_device_paths() -> None:
    module = _load_module()
    dol = _build_dol(
        text_address=0x80004000,
        text_words=[0x60000000],
        data_address=0x80300000,
        data_bytes=b"/dev/net/kd/request\x00/dev/fs\x00",
    )

    paths = module.find_device_paths(dol)

    assert [path.text for path in paths] == ["/dev/net/kd/request", "/dev/fs"]


def test_find_lis_addi_reference_and_callsite() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_lis_addi")
    target = 0x80300020
    text_address = 0x80004000
    call_target = 0x80504780
    dol = _build_dol(
        text_address=text_address,
        text_words=[
            _encode_lis(3, (target >> 16) & 0xFFFF),
            _encode_addi(3, 3, target & 0xFFFF),
            _encode_bl(text_address + 8, call_target),
        ],
        data_address=0x80300000,
        data_bytes=b"A" * 0x20 + b"/dev/stm/immediate\x00",
    )

    refs = module.find_string_references(dol, target)
    calls = module.find_calls_following_string_reference(dol, refs[0])

    assert len(refs) == 1
    assert refs[0].form == "lis/addi"
    assert len(calls) == 1
    assert calls[0].target_address == call_target


def test_find_lis_ori_reference() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_lis_ori")
    target = 0x80300044
    dol = _build_dol(
        text_address=0x80004000,
        text_words=[
            _encode_lis(4, (target >> 16) & 0xFFFF),
            _encode_ori(4, 4, target & 0xFFFF),
            0x60000000,
        ],
        data_address=0x80300000,
        data_bytes=b"B" * 0x44 + b"/dev/es\x00",
    )

    refs = module.find_string_references(dol, target)

    assert len(refs) == 1
    assert refs[0].form == "lis/ori"


def test_false_reference_is_rejected() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_false_ref")
    target = 0x80300020
    dol = _build_dol(
        text_address=0x80004000,
        text_words=[
            _encode_lis(3, (target >> 16) & 0xFFFF),
            _encode_addi(3, 3, 0x30),
            0x60000000,
        ],
        data_address=0x80300000,
        data_bytes=b"C" * 0x20 + b"/dev/fs\x00",
    )

    assert module.find_string_references(dol, target) == []


def test_score_wrapper_cluster_accepts_coherent_cluster() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_cluster")
    candidates = [
        module.WrapperCandidate(0x1000, 1, 0x2000, 0x3000, (1, 2), "open_async"),
        module.WrapperCandidate(0x1010, 1, 0x2000, 0x3000, (1, 2), "open"),
        module.WrapperCandidate(0x1020, 2, 0x2000, 0x3000, (1, 2), "close_async"),
        module.WrapperCandidate(0x1030, 2, 0x2000, 0x3000, (1, 2), "close"),
        module.WrapperCandidate(0x1040, 3, 0x2000, 0x3000, (1, 2), "read_async"),
        module.WrapperCandidate(0x1050, 4, 0x2000, 0x3000, (1, 2), "write_async"),
    ]

    assert module.score_wrapper_cluster(candidates) == len(candidates)


def test_score_wrapper_cluster_rejects_isolated_prologue() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_isolated")
    candidates = [
        module.WrapperCandidate(0x1000, 1, 0x2000, 0x3000, (1,), "open_async"),
        module.WrapperCandidate(0x1010, 2, 0x2001, 0x3000, (1, 2), "close_async"),
    ]

    assert module.score_wrapper_cluster(candidates) == 0


def test_find_direct_branch_callers_reports_link_and_non_link_sites() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_direct_callers")
    target = 0x80504A08
    text_address = 0x80004000
    dol = _build_dol(
        text_address=text_address,
        text_words=[
            _encode_bl(text_address, target),
            0x48000000 | ((target - (text_address + 4)) & 0x03FFFFFC),
        ],
        data_address=0x80300000,
        data_bytes=b"\x00",
    )

    callers = module.find_direct_branch_callers(dol, target)

    assert callers == [
        {"caller_address": text_address, "link": True},
        {"caller_address": text_address + 4, "link": False},
    ]


@pytest.mark.parametrize(
    ("operation", "fields", "completion", "vectors", "expected"),
    [
        (3, {"fd", "buffer_physical", "length"}, True, False, "async_read"),
        (3, {"fd", "buffer_physical", "length"}, False, False, "sync_read"),
        (4, {"fd", "buffer_physical", "length"}, True, False, "async_write"),
        (5, {"fd", "seek_offset", "seek_origin"}, False, False, "sync_seek"),
        (
            6,
            {"fd", "command", "input_physical", "input_length", "output_physical", "output_length"},
            True,
            False,
            "async_ioctl",
        ),
        (
            7,
            {"fd", "command", "input_vector_count", "output_vector_count", "vector_array_physical"},
            True,
            True,
            "async_vector_ioctl",
        ),
    ],
)
def test_classify_request_shape(
    operation: int,
    fields: set[str],
    completion: bool,
    vectors: bool,
    expected: str,
) -> None:
    module = _load_module(f"prime3_wii_runtime_analyze_ios_wrappers_shape_{expected}")

    classification, reasons = module.classify_request_shape(
        operation=operation,
        request_fields=fields,
        completion_present=completion,
        vector_elements_processed=vectors,
    )

    assert classification == expected
    assert reasons == ()


def test_classify_request_shape_keeps_incomplete_vector_helper_neutral() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_incomplete_vector")

    classification, reasons = module.classify_request_shape(
        operation=7,
        request_fields={"fd", "command", "input_vector_count", "output_vector_count", "vector_array_physical"},
        completion_present=False,
        vector_elements_processed=False,
    )

    assert classification == "unknown_helper"
    assert reasons == ("vector element pointer and length processing is not proven",)


def test_classify_request_shape_rejects_false_positive_neighbor() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_false_neighbor")

    classification, reasons = module.classify_request_shape(
        operation=None,
        request_fields={"command"},
        completion_present=False,
    )

    assert classification == "unknown_helper"
    assert reasons == ("fd field is not proven",)


def test_validate_function_fingerprints_uses_virtual_range() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_fingerprint")
    text_address = 0x80004000
    word = 0x60000000
    dol = _build_dol(
        text_address=text_address,
        text_words=[word],
        data_address=0x80300000,
        data_bytes=b"\x00",
    )
    fingerprint = hashlib.sha256(word.to_bytes(4, "big")).hexdigest()
    spec = module.RetailWrapperSpec(
        "synthetic",
        text_address,
        text_address + 4,
        None,
        "s32 synthetic(void)",
        (),
        (),
        (),
        fingerprint,
    )

    assert module.validate_function_fingerprints(dol, (spec,)) == {"synthetic": fingerprint}


def test_validate_function_fingerprints_rejects_mismatch() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_fingerprint_mismatch")
    text_address = 0x80004000
    dol = _build_dol(
        text_address=text_address,
        text_words=[0x60000000],
        data_address=0x80300000,
        data_bytes=b"\x00",
    )
    spec = module.RetailWrapperSpec(
        "synthetic",
        text_address,
        text_address + 4,
        None,
        "s32 synthetic(void)",
        (),
        (),
        (),
        "0" * 64,
    )

    with pytest.raises(ValueError, match="Function fingerprint mismatch"):
        module.validate_function_fingerprints(dol, (spec,))


def test_known_retail_sequence_rejects_unsupported_dol() -> None:
    module = _load_module("prime3_wii_runtime_analyze_ios_wrappers_unsupported")
    dol = _build_dol(
        text_address=0x80004000,
        text_words=[0x60000000],
        data_address=0x80300000,
        data_bytes=b"\x00",
    )

    with pytest.raises(ValueError, match="Unsupported retail DOL SHA-256"):
        module.analyze_known_retail_wrapper_sequence(dol)
