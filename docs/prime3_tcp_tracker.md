# Prime 3 TCP Tracker Baseline

The Prime 3 tracker listener is disabled unless `server_config.prime3_tracker.enabled`
is true. Its defaults are `bind_host=0.0.0.0`, `bind_port=43674`,
`idle_timeout_seconds=30`, `maximum_clients=8`, and
`maximum_frame_queue_depth=4`.

The listener accepts only CP3W version 1 frames from game ID `RM3E`. It emits
`prime3_tracker_update` Socket.IO events and exposes status at
`/api/prime3-tracker/<client_nonce>`. It never accepts gameplay commands.

The client tracker snapshot is read-only. Its first schema uses the existing,
validated Prime 3 inventory-root accessor: game state pointer `0x8067DC0C`,
inventory root at offset `0x24`, and the first powerup record at
`root + 0x54 + item_id * 0x0C`. The three reported words are amount, capacity,
and the record's third word. The snapshot is emitted only after the TCP HELLO
acknowledgement and requires a TRACKER_ACK before tracking is considered ready.

The TCP endpoint is a build configuration: `PRIME3_TCP_SERVER_IPV4` and
`PRIME3_TCP_SERVER_PORT`. Production builds leave `ENABLE_TCP_DIAGNOSTICS=0`.
No source file contains a machine-specific filesystem path, credential, or
token.
