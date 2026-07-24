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
and read the retail SO descriptor. The retail bootstrap can return zero after logging and
swallowing an internal KD/network setup failure. Live Dolphin evidence showed both 20
`SOGetHostID` results of `-101` after trusting that result and an IOS `-101` result when
`SOStartup` was submitted immediately on the retained descriptor.

The diagnostic recovery retains that descriptor, reruns the proven low-level KD open,
NWC24 startup, and KD close sequence, and only then submits the verified SOStartup command.
If that duplicate startup still completes with the observed `-101`, the diagnostic preserves
it as a startup warning and proceeds only to the bounded host-ID readiness gate. It does not
create a socket unless SOGetHostID subsequently returns a valid nonzero address.
If all 20 reads fail, one explicit low-level recovery closes only the unusable retained SO
descriptor, opens a fresh `/dev/net/ip/top` descriptor, and repeats KD startup, KD close,
SOStartup, and the bounded readiness gate. The native bootstrap itself is not called again.
A startup failure or second host-ID timeout after descriptor replacement is terminal.
It then polls SOGetHostID, creates a socket, and sends diagnostic UDP beacons. It does not
enter friend-list, mailbox, voucher, recipient-selection, or menu code. Calls use the
game's verified `r2` and `r13` values through the existing retail-call veneer ABI.

The NWC24 base contains mutexes at offsets `0x00` and `0x18` and 32-byte work buffers at
offsets `0x40` and `0x60`. Initialization and reference state also use SDA offsets
`-6272`, `-6268`, and `-6264`. The native bootstrap state uses values 1 (initializing) and
2 (initialized). Failure cleanup inside the retail bootstrap closes SO through the native
close path; successful diagnostic ownership is retained instead.

## Shared production readiness

`cp3w_inventory_service` and `native_wc24_bootstrap_beacon_once` use the same
native readiness gate through the first valid host ID. Production then enters
the existing socket, `INADDR_ANY:43674` bind, receive, CP3W session, identity,
and inventory path; it does not prepare or submit the diagnostic beacon.

After a later production socket failure, the runtime closes the UDP socket,
increments its startup generation, ages the pending callback generation and
receive/send callback token, resets only the CP3W session negotiation fields,
closes the SO descriptor owned by the old generation, and reruns native
readiness. Identity and inventory counters remain intact. Each generation
starts with a fresh one-replacement allowance. The initial descriptor and its
historical readiness error remain in diagnostics across later recoveries.

## Diagnostic mode

`native_wc24_bootstrap_beacon_once` waits for the recurring hook's normal initial delay and
runs the native sequence once. It polls SOGetHostID at intervals of at least 30 recurring-hook
calls and 0.5 seconds for up to 20 attempts. The timebase requirement is necessary because the
selected retail hook can execute thousands of times per second, so poll counts alone do not
provide a useful network-readiness window. A valid nonzero host ID advances to socket creation;
otherwise the mode remains terminally in `NATIVE_HOST_ID_TIMEOUT`. It then
submits 10 UDP beacons, waits for each asynchronous completion, and waits at least 30
recurring-hook polls and 0.5 seconds after each completion before the next submission. Successful completion
enters `NATIVE_BEACON_COMPLETE`. Submission, asynchronous completion, socket, and bootstrap
failures enter terminal `FAILED` without routing through generic receive-mode recovery.

The mode does not bind or install the CP3W listener. Successful NWC24, SO, and socket
resources remain alive for inspection through readiness waits, beacon intervals, success,
and failure.

Packaged assets contain `192.168.50.248` as a guarded placeholder. The export dialog requires
an IPv4 destination and patches only that copied four-byte field. UDP port `43674` is fixed and
cannot be overridden.

An allocation-free 3x5 debug font is available in native diagnostic and production modes. The renderer reads
the VI top/bottom XFB registers, honors the register's page-offset bit, derives width and stride
from VI picture configuration, derives field height from VI vertical timing, accepts validated
MEM1 and MEM2 ranges, and draws every distinct active field (plus right-eye fields when 3D mode
is active). It changes only the Y bytes in Wii YCbCr 4:2:2 pairs, clips every write, and flushes
the complete modified row range. A bordered upper-left marker reports the execution stage and
poll count before the full diagnostic text. The overlay defaults off. Its post-copy wrapper
checks the guarded enable state before `GXDrawDone`; while hidden it does not resolve XFBs,
write framebuffer memory, or flush framebuffer ranges. Hold Minus+1+2 for 30 consecutive
recurring-hook polls to toggle it. The runtime reads the current channel-0 `KPADStatus.hold`
word directly at `0x805F5088`; it does not call `KPADRead` or alter KPAD's buffered-input
counters. One toggle is allowed per hold, and releasing any button rearms the chord.
While enabled, the guarded post-copy renderer runs at most once per 30 recurring-hook polls;
intervening post-copy calls use the same immediate continuation as the disabled path. This
prevents repeated `GXDrawDone` and full-XFB cache work from starving the game or CP3W service.

The recurring hook at `0x800BB71C` is a high-frequency game accessor and runs before Prime 3's
frame copy, so its direct XFB writes can be replaced by the later EFB-to-XFB operation. The
retail SDK `GXCopyDisp` implementation is `0x804D3624`; its sole wrapper calls it at
`0x8037245C`, then executes `lwz r0, 0x14(r1)` at `0x80372460`. Native mode verifies that exact
instruction before replacing it with a branch to the relocated post-copy overlay wrapper. The
wrapper draws both fields of the copied destination and every live VI XFB, executes the
verified synchronous `GXDrawDone` path at `0x804D2644` before drawing, executes the displaced
instruction, and resumes at `0x80372464`. Waiting for draw completion is required because
`GXCopyDisp` only submits the GPU copy; drawing immediately after submission races and can be
overwritten by the later copy-to-RAM operation. Installation flushes the changed data-cache
line and invalidates the corresponding instruction-cache line. A mismatch fails closed without
patching retail code. The wrapper is compiled and installed only for mode 22 and mode 23.

The relocated runtime's manifest-declared `CP3D` block remains version 1 and size `0x100`.
`0x817E0100` is the separate entry-bootstrap canary block; it is not the network diagnostics
block. Fields unused by this non-listening mode have the following mode-specific meanings:

- IOS version: execution canary `NAT1` (`0x4E415431`)
- IOS revision: execution stage (`1` through `10`, or `15` for terminal failure)
- shutdown call count: recurring-hook execution count
- overlay page: signed post-copy hook result (`1` installed, `-1` instruction mismatch,
  `-2` unreachable or unaligned wrapper)
- initialization attempt count: startup generation
- successful initialization count: descriptor replacement count
- last shutdown descriptor: initial retained SO descriptor
- last heartbeat result: historical initial-descriptor readiness error
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
- cleanup call count: successful cleanup suppressions or deferrals
- current phase and error fields: exact terminal or failed operation state

The execution stages are:

| Value | Stage |
| ---: | --- |
| 1 | relocated runtime initialized |
| 2 | recurring hook entered |
| 3 | native mode recognized |
| 4 | startup delay active |
| 5 | native bootstrap entered |
| 6 | native bootstrap returned |
| 7 | host-ID polling |
| 8 | socket creation |
| 9 | beacon submission |
| 10 | beacon completion |
| 15 | terminal failure |

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
