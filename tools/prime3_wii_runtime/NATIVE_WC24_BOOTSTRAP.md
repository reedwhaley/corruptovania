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
read the retail SO descriptor, poll SOGetHostID, create a socket, and send diagnostic UDP beacons. It does not
enter friend-list, mailbox, voucher, recipient-selection, or menu code. Calls use the
game's verified `r2` and `r13` values through the existing retail-call veneer ABI.

The NWC24 base contains mutexes at offsets `0x00` and `0x18` and 32-byte work buffers at
offsets `0x40` and `0x60`. Initialization and reference state also use SDA offsets
`-6272`, `-6268`, and `-6264`. The native bootstrap state uses values 1 (initializing) and
2 (initialized). Failure cleanup inside the retail bootstrap closes SO through the native
close path; successful diagnostic ownership is retained instead.

## Diagnostic mode

`native_wc24_bootstrap_beacon_once` waits for the recurring hook's normal initial delay and
runs the native sequence once. It polls SOGetHostID at 30-poll intervals for up to 20
attempts. A valid nonzero host ID advances to socket creation; otherwise the mode remains
terminally in `NATIVE_HOST_ID_TIMEOUT` after an additional 30-poll timeout interval. It then
submits 10 UDP beacons, waits for each asynchronous completion, and waits at least 30
recurring-hook polls after each completion before the next submission. Successful completion
enters `NATIVE_BEACON_COMPLETE`. Submission, asynchronous completion, socket, and bootstrap
failures enter terminal `FAILED` without routing through generic receive-mode recovery.

The mode does not bind or install the CP3W listener. Successful NWC24, SO, and socket
resources remain alive for inspection through readiness waits, beacon intervals, success,
and failure.

Packaged assets contain `192.168.50.248` as a guarded placeholder. The export dialog requires
an IPv4 destination and patches only that copied four-byte field. UDP port `43674` is fixed and
cannot be overridden.

An allocation-free 3x5 debug font is drawn at the upper-left of the active 640x480 XFB after
each recurring-hook poll. It changes luminance bytes only, uses a compact `448x144` background,
and remains visible in terminal success and failure phases. This renderer is compiled only
for mode 23; production and the other diagnostic modes contain no overlay code.

The existing fixed `CP3D` block at `0x817E0100` remains version 1 and size `0x100`. Fields
unused by this non-listening mode have the following mode-specific meanings:

- initialization attempt count: native bootstrap calls
- NWC24 result: native library-open result
- network initialization result: retail network-bootstrap result
- IP and socket descriptors: retained retail SO descriptor and beacon socket
- host ID result and host IP: last signed SOGetHostID result and first valid nonzero host ID
- receive call count: host-ID attempt count
- last packet receive poll: poll of the first valid host ID
- send call count and packets sent: beacon attempts and successful completions
- send failures: submission failures plus asynchronous completion failures
- malformed packet count: beacon submission failures
- transient receive errors: asynchronous beacon completion failures
- bind result: last beacon submission result
- getsockname result: last asynchronous beacon completion result
- last successful bind poll and last packet send poll: first and most recent successful beacon polls
- receive loop iteration count: fixed beacon limit (`10`)
- last heartbeat result: last asynchronous beacon completion result
- cleanup call count: successful cleanup suppressions or deferrals
- current phase and error fields: exact terminal or failed operation state

The appended native phases preserve every older numeric value:

| Value | Phase |
| ---: | --- |
| 108 | `NATIVE_BOOTSTRAP` |
| 109 | `NATIVE_WAIT_HOST_ID` |
| 110 | `NATIVE_HOST_ID_TIMEOUT` |
| 111 | `NATIVE_CREATE_BEACON_SOCKET` |
| 112 | `NATIVE_WAIT_BEACON_INTERVAL` |
| 113 | `NATIVE_SUBMIT_BEACON` |
| 114 | `NATIVE_WAIT_BEACON` |
| 115 | `NATIVE_BEACON_COMPLETE` |
