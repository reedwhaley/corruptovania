#!/usr/bin/env python3
"""Fixed-size CP3W handshake and diagnostic-echo server for Wii TCP probes."""

from __future__ import annotations

import argparse
import binascii
import socket
import struct
import time

FRAME = struct.Struct(">4sBBH14I")
FRAME_SIZE = FRAME.size
MAGIC = b"CP3W"
VERSION = 1
CLIENT_HELLO = 0x01
SERVER_HELLO_ACK = 0x02
CLIENT_TEST = 0x03
SERVER_TEST = 0x04
DIAGNOSTIC_REQUEST = 0x10
DIAGNOSTIC_ECHO = 0x11
PAYLOAD_SIZE = 36
SERVER_NONCE = 0x53525631


def receive_exact(client: socket.socket, length: int) -> bytes | None:
    data = bytearray()
    while len(data) < length:
        chunk = client.recv(length - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)


def send_all(client: socket.socket, payload: bytes, split_size: int, delay_seconds: float) -> None:
    offset = 0
    while offset < len(payload):
        end = len(payload) if split_size == 0 else min(offset + split_size, len(payload))
        sent = client.send(payload[offset:end])
        if sent <= 0:
            raise ConnectionError("peer closed during send")
        offset += sent
        if delay_seconds and offset < len(payload):
            time.sleep(delay_seconds)


def decode_frame(payload: bytes) -> tuple[dict[str, int | bytes], bool]:
    magic, version, message_type, length, sequence, acknowledgement, payload_length, flags, *words = FRAME.unpack(
        payload
    )
    received_crc = words[-1]
    valid = (
        magic == MAGIC
        and version == VERSION
        and length == FRAME_SIZE
        and payload_length <= PAYLOAD_SIZE
        and received_crc == (binascii.crc32(payload[:60]) & 0xFFFFFFFF)
    )
    return {
        "magic": magic,
        "version": version,
        "type": message_type,
        "length": length,
        "sequence": sequence,
        "ack": acknowledgement,
        "payload_length": payload_length,
        "flags": flags,
        "payload": payload[24:60],
    }, valid


def encode_frame(message_type: int, sequence: int, acknowledgement: int, payload_words: list[int]) -> bytes:
    payload_words = (payload_words + [0] * 9)[:9]
    frame = bytearray(
        FRAME.pack(
            MAGIC, VERSION, message_type, FRAME_SIZE, sequence, acknowledgement, PAYLOAD_SIZE, 0, *payload_words, 0
        )
    )
    frame[60:64] = struct.pack(">I", binascii.crc32(frame[:60]) & 0xFFFFFFFF)
    return bytes(frame)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=43674)
    parser.add_argument("--split-size", type=int, default=0)
    parser.add_argument("--delay-ms", type=int, default=0)
    parser.add_argument("--drop-every", type=int, default=0)
    parser.add_argument("--close-after", type=int, default=0)
    parser.add_argument("--log-raw", action="store_true")
    args = parser.parse_args()
    if min(args.split_size, args.delay_ms, args.drop_every, args.close_after) < 0:
        parser.error("transport controls must be non-negative")
    delay_seconds = args.delay_ms / 1000
    with socket.create_server((args.host, args.port), reuse_port=False) as listener:
        print(f"{time.time():.3f} listening {args.host}:{args.port}", flush=True)
        while True:
            client, address = listener.accept()
            print(f"{time.time():.3f} connected {address}", flush=True)
            state = "hello"
            server_sequence = 1
            received_count = 0
            client_nonce = 0
            try:
                with client:
                    while True:
                        raw = receive_exact(client, FRAME_SIZE)
                        if raw is None:
                            print(f"{time.time():.3f} EOF {address}", flush=True)
                            break
                        frame, valid = decode_frame(raw)
                        received_count += 1
                        if args.log_raw:
                            print(f"{time.time():.3f} raw={raw.hex()}", flush=True)
                        if not valid:
                            print(f"{time.time():.3f} protocol-error {address} crc-or-envelope", flush=True)
                            break
                        message_type = int(frame["type"])
                        sequence = int(frame["sequence"])
                        payload = frame["payload"]
                        print(
                            f"{time.time():.3f} {address} state={state} type=0x{message_type:02X} seq={sequence}",
                            flush=True,
                        )
                        response: bytes | None = None
                        if state == "hello" and message_type == CLIENT_HELLO:
                            game_id, build_id, caps, client_nonce, *_ = struct.unpack(">9I", payload)
                            if game_id != 0x524D3345:
                                print(f"{time.time():.3f} protocol-error bad-game-id=0x{game_id:08X}", flush=True)
                                break
                            print(
                                f"{time.time():.3f} CLIENT_HELLO build=0x{build_id:08X} "
                                f"caps=0x{caps:08X} nonce=0x{client_nonce:08X}",
                                flush=True,
                            )
                            response = encode_frame(
                                SERVER_HELLO_ACK,
                                server_sequence,
                                sequence,
                                [client_nonce, SERVER_NONCE, 0, 0, caps, VERSION, 60],
                            )
                            server_sequence += 1
                            state = "test"
                            print(f"{time.time():.3f} SERVER_HELLO_ACK sent", flush=True)
                        elif state == "test" and message_type == CLIENT_TEST:
                            marker, echoed_nonce, *_ = struct.unpack(">9I", payload)
                            if marker != 0x43545354 or echoed_nonce != client_nonce:
                                print(f"{time.time():.3f} protocol-error invalid-client-test", flush=True)
                                break
                            response = encode_frame(
                                SERVER_TEST, server_sequence, sequence, [0x53545354, client_nonce, SERVER_NONCE]
                            )
                            server_sequence += 1
                            state = "established"
                            print(f"{time.time():.3f} CLIENT_TEST received; SERVER_TEST sent", flush=True)
                        elif state == "established" and message_type == DIAGNOSTIC_REQUEST:
                            response = encode_frame(
                                DIAGNOSTIC_ECHO, server_sequence, sequence, list(struct.unpack(">9I", payload))
                            )
                            server_sequence += 1
                            print(f"{time.time():.3f} CP3D seq={sequence} echoed", flush=True)
                        else:
                            print(f"{time.time():.3f} protocol-error unexpected-type", flush=True)
                            break
                        if args.drop_every and received_count % args.drop_every == 0:
                            continue
                        if response is not None:
                            send_all(client, response, args.split_size, delay_seconds)
                        if args.close_after and received_count >= args.close_after:
                            print(f"{time.time():.3f} close-after {address}", flush=True)
                            break
            except (ConnectionResetError, ConnectionError) as error:
                print(f"{time.time():.3f} disconnect {address}: {error}", flush=True)


if __name__ == "__main__":
    main()
