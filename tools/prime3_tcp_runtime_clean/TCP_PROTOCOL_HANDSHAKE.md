# CP3W TCP Protocol Handshake Baseline

Frames are fixed 64-byte big-endian records. The header is `CP3W`, version 1,
message type, total length, client/server sequence fields, payload length,
flags, 36 payload bytes, and a CRC32 over bytes 0 through 59.

The client sends `CLIENT_HELLO` (sequence 1), validates `SERVER_HELLO_ACK`,
sends one inert `CLIENT_TEST`, validates `SERVER_TEST`, then remains
established. Established sessions issue a CP3D diagnostic request every 60
recurring polls. No protocol message reads or writes gameplay state.

Outbound and inbound queues each contain four 76-byte slots: occupied flag,
message type, sequence, and the complete encoded frame. Queue insertion never
overwrites occupied slots; overflow increments a diagnostic counter and closes
the owned TCP socket through the existing failure path.
