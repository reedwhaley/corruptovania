# Prime 3 Wii Connection Protocol

Corruptovania uses this protocol to read Metroid Prime 3 memory from physical Wii hardware over UDP.

Version 1 is intentionally read-only. It supports:

- `HELLO`
- `READ_MEMORY`
- `PING`
- `DISCONNECT`

It also reserves a future structured mailbox command for bidirectional gameplay communication. Version 1 does not support arbitrary memory writes, incoming item delivery, or outgoing location reporting.

## Packet format

All integer fields are big-endian.

| Field | Size | Notes |
| --- | --- | --- |
| magic | 4 bytes | ASCII `CP3W` |
| protocol_version | 1 byte | `1` for this revision |
| packet_kind | 1 byte | `1=request`, `2=response` |
| command | 1 byte | See command table below |
| response_status | 1 byte | `0=OK`, `1=ERROR` |
| request_id | 4 bytes | Non-zero request correlation ID |
| payload_length | 4 bytes | Number of payload bytes |
| payload | variable | Command-specific bytes |
| crc32 | 4 bytes | CRC32 over all prior packet bytes |

## Commands

| Value | Command | Request payload | Successful response payload |
| --- | --- | --- | --- |
| `1` | `HELLO` | empty | `protocol_version:u16`, `max_read_size:u32`, `capabilities:u32` |
| `2` | `READ_MEMORY` | `address:u32`, `size:u32` | raw memory bytes |
| `3` | `PING` | empty | empty |
| `4` | `DISCONNECT` | empty | empty |
| `127` | `RESERVED_MAILBOX` | reserved | reserved |

## Capabilities

| Bit | Meaning |
| --- | --- |
| `0x00000001` | `READ_MEMORY` |
| `0x00000002` | `STRUCTURED_MAILBOX` |

Version 1 requires `READ_MEMORY`. `STRUCTURED_MAILBOX` is reserved for future gameplay communication with acknowledgements and duplicate protection.

## Error responses

Error responses reuse the standard packet header with `response_status=1`. Their payload is:

| Field | Size |
| --- | --- |
| error_code | 2 bytes |
| command | 2 bytes |
| message_length | 2 bytes |
| message | variable UTF-8 bytes |

Relevant error conditions include malformed packets, bad magic, unsupported protocol versions, unknown commands, invalid payload lengths, checksum mismatches, mismatched request IDs, and server-side protocol errors.
