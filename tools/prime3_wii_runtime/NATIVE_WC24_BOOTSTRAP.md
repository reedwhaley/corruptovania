# Prime 3 native WiiConnect24 bootstrap diagnostic

This diagnostic is based on static analysis of the NTSC Prime 3 `main.dol` with SHA-256
`6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104`. Addresses below are
specific to that executable.

## Native layers

| Address | Interface | ABI and state |
| --- | --- | --- |
| `0x805541B8` | NWC24 library open | No arguments; signed result in `r3`. Initializes mutexes and work buffers rooted at `0x8064ECA0`, then increments the SDA reference count at `-6268(r13)`. |
| `0x8055436C` | NWC24 library close | No arguments; decrements the retained reference and performs native command 3 cleanup. The diagnostic deliberately does not call it. |
| `0x80554288` | Secondary NWC24 feature open | Used by game feature and UI state, including the call at `0x800E029C`. The diagnostic bypasses this layer. |
| `0x80554854` | Secondary NWC24 feature close | Paired with the secondary feature open. The diagnostic bypasses it. |
| `0x80508DD4` | Retail network bootstrap | No arguments; signed result in `r3`, where zero is success. Calls the retail SO initializer at `0x80500684`, initializes lower network state, and records native state at SDA offset `-6496(r13)`. |
| `0x80500684` | Retail SO initializer | Opens the SO resource, stores its descriptor at `-26024(r13)`, and initializes the retail SO work arena. |

The direct native call sequence is therefore NWC24 library open, retail network bootstrap,
read the retail SO descriptor, SOGetHostID, socket creation, and one UDP send. It does not
enter friend-list, mailbox, voucher, recipient-selection, or menu code. Calls use the
game's verified `r2` and `r13` values through the existing retail-call veneer ABI.

The NWC24 base contains mutexes at offsets `0x00` and `0x18` and 32-byte work buffers at
offsets `0x40` and `0x60`. Initialization and reference state also use SDA offsets
`-6272`, `-6268`, and `-6264`. The native bootstrap state uses values 1 (initializing) and
2 (initialized). Failure cleanup inside the retail bootstrap closes SO through the native
close path; successful diagnostic ownership is retained instead.

## Diagnostic mode

`native_wc24_bootstrap_beacon_once` waits for the recurring hook's normal initial delay,
runs the native sequence once, sends a single UDP beacon, and enters `DIAGNOSTIC_COMPLETE`.
It does not bind or install the CP3W listener. Successful NWC24, SO, and socket resources
remain alive for inspection; ordinary initialization, socket, host-ID, and send failures
still enter the runtime's existing error handling.

The endpoint defaults to `192.168.50.248:43674`. Development builds can override it with
`--native-beacon-ipv4` and `--native-beacon-port` in `tools/build_prime3_runtime_assets.py`.

The existing fixed `CP3D` block at `0x817E0100` records this mode without changing its ABI:

- initialization attempt count: native bootstrap calls
- NWC24 result: native library-open result
- network initialization result: retail network-bootstrap result
- IP and socket descriptors: retained retail SO descriptor and beacon socket
- host ID: SOGetHostID result
- last heartbeat result: beacon send result
- cleanup call count: successful cleanup suppressions or deferrals
- current phase and error fields: exact terminal or failed operation state
