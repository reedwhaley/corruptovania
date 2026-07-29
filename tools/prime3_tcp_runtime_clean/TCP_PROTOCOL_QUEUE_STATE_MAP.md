# CP3W Queue and State Map

The runtime uses `QUEUE_CLIENT_HELLO`, `SEND_QUEUED_FRAME`,
`WAIT_SERVER_HELLO_ACK`, `RECEIVE_FRAME`, `VALIDATE_FRAME`,
`QUEUE_CLIENT_TEST`, `WAIT_SERVER_TEST`, and `ESTABLISHED` after TCP connect.
The synchronous command-13 sender and asynchronous command-12 receiver remain
the same primitives used by the framed-echo baseline.

Link-map addresses are generated per artifact. The baseline build records both
queue arrays in its linker map and exports code/state high-water symbols.
