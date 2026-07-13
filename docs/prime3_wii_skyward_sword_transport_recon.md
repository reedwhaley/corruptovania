# Prime 3 Wii Skyward Sword Transport Recon

## Scope

This document records the source-backed Wii UDP transport evidence gathered from the Skyward Sword Archipelago codebase and compares it against the current Prime 3 Wii runtime constraints.

This recon is transport-focused only. It does not justify copying Skyward Sword gameplay protocol commands, write-memory behavior, item delivery, mailbox behavior, or normal exporter integration into Prime 3.

Prime 3 correction:

- Skyward Sword remains structural provenance only
- Prime 3 NTSC must call its own retail IOS wrapper cluster rather than a project-owned raw submit path
- the currently verified Prime 3 NTSC retail `IOS_OpenAsync` candidate is `0x80504668`, with neighboring `IOS_Open`, `IOS_CloseAsync`, `IOS_Close`, `IOS_IoctlAsync`, `IOS_Ioctl`, `IOS_IoctlvAsync`, and `IOS_Ioctlv` wrappers forming a coherent cluster

## External repositories and revisions inspected

Repositories:

- `Battlecats59/sslib`
- `Battlecats59/SSArchipelago`
- `Battlecats59/SS_APWorld`

Current default branches inspected:

- `Battlecats59/sslib` default branch `main` at `029545b5e1d73ef515a1d61fc69b572946d45399`
- `Battlecats59/SSArchipelago` default branch `main` at `dc911399fbec508333387439373fdd015663add0`
- `Battlecats59/SS_APWorld` default branch `ss` at `a6e5daed861be683ca791063e947334df83b48cb`

Pull requests inspected:

- `Battlecats59/sslib` PR 14 `Console AP Support with UDP Server`
  - merge commit `0712e40a790321b71c9c9d9d8b50bb8fe0aaa22c`
  - head branch fetched locally as `pr14-console-support` at `73ec2d035cead0db7522aada2e21aa372054af37`
- `Battlecats59/sslib` PR 19 `Network protocol overhaul`
  - head branch fetched locally as `pr19-console-net-rework` at `d2083cff5701ae5d34b0fa341e8df3470bfcbbca`
- `Battlecats59/SSArchipelago` PR 27 `Add console connection support`
  - merge commit `b7b64e443b839affc2d7f651edafb486bfaa0c91`
  - head branch fetched locally as `pr27-console-socket` at `ae2a504b4f5132bad27435b1f86221847200e1a1`
- `Battlecats59/SSArchipelago` PR 53 `Console net rework`
  - head branch fetched locally as `pr53-console-net-rework` at `d7ff141da7991e4f7feb551a16f25ae6a982305d`

## Relevant source files

Current or newer Wii-side transport source:

- `sslib` PR 19: `asm/custom-functions/src/rando/networking.rs`
- `sslib` PR 19: `asm/custom-functions/src/system/ios.rs`
- `sslib` PR 19: `asm/custom-functions/src/rvl_mem.rs`
- `sslib` PR 19: `asm/custom-functions/src/system/alarm.rs`
- `sslib` PR 19: `asm/original_symbols.txt`
- `sslib` PR 19: `asm/custom-functions/src/rando/multiworld.rs`

Historical Wii-side transport source:

- `sslib` PR 14: `asm/custom-functions/src/rando/networking.rs`
- `sslib` PR 14: `asm/custom-functions/src/system/ios.rs`
- `sslib` PR 14: `asm/custom-functions/src/rvl_mem.rs`
- `sslib` PR 14: `asm/original_symbols.txt`

Historical PC client:

- `SSArchipelago` PR 27: `worlds/ss/SSClient.py`

Newer PC client:

- `SSArchipelago` PR 53: `worlds/ss/SSClient.py`
- `SSArchipelago` PR 53: `worlds/ss/SSClientUtils.py`

Current default-branch PC client still carrying the earlier protocol shape:

- `SS_APWorld` default branch `ss`: `SSClient.py`
- `SS_APWorld` default branch `ss`: `docs/setup_en.md`

## License and provenance

`Battlecats59/sslib` declares the MIT License. The Wii transport source added in PR 14 and modified in PR 19 lives inside that repository, so direct reuse is license-permitted if attribution is preserved.

`Battlecats59/SSArchipelago` reports repository license `Other` through GitHub. Its Python client is still useful as behavioral evidence, but the Wii-side transport implementation itself lives in `sslib`, not in `SSArchipelago`.

`Battlecats59/SS_APWorld` currently exposes no declared repository license through GitHub and no local top-level `LICENSE` file was present in the inspected clone. Its client and setup docs are therefore treated here as behavioral reference only, not code-reuse candidates.

The direct transport provenance conclusion is:

- Wii-side transport implementation: reusable with attribution from `sslib` under MIT
- Python client framing examples in `SSArchipelago` and `SS_APWorld`: behavioral reference only for this milestone
- no libogc networking source was copied into this repository during recon

## High-level answer

Skyward Sword does not call libogc `net_*` functions at runtime.

It also does not use guessed retail socket wrapper addresses from the game.

Instead, the console transport is a custom Rust wrapper over direct IOS entry points already present in the retail game image:

- `IOS_OpenAsync`
- `IOS_CloseAsync`
- `IOS_IoctlAsync`
- `IOS_IoctlvAsync`
- `IOS_Open`
- `IOS_Close`
- `IOS_Ioctl`
- `IOS_Ioctlv`

Those symbols are listed explicitly in `sslib` PR 14 and PR 19 `asm/original_symbols.txt`, along with `OSInsertAlarm`, `OSYieldThread`, `iosAllocAligned`, `iosFree`, and `IOS_HEAP`.

## Current versus historical implementation

### Historical transport: PR 14

PR 14 implements:

- direct open of `/dev/net/kd/request`
- direct open of `/dev/net/ip/top`
- `IOCTL_NWC24_STARTUP` on the request device
- `IOCTL_SO_STARTUP` on the socket device
- `IOCTL_SO_GETHOSTID`
- `IOCTL_SO_SOCKET` with `AF_INET`, `SOCK_DGRAM`, `IPPROTO_IP`
- `IOCTL_SO_BIND`
- `IOCTL_SO_SEND`
- `IOCTL_SO_RECV`

Protocol behavior in PR 14 is address-based:

- `0x00`: establish
- `0x01`: raw read-memory
- `0x02`: raw write-memory
- `0x05`: disconnect

The Wii binds to its own reported host IP and port `43673`.

### Newer transport: PR 19 plus PC PR 53

PR 19 keeps the same low-level IOS transport path:

- same device files
- same IOS APIs
- same socket startup path
- same async `IOS_IoctlAsync` and `IOS_IoctlvAsync` transport shape

But it changes protocol framing and some socket details:

- two-byte sequence prefix added to each packet
- payload command follows the sequence
- send path prepends sequence before transmitting
- receive path expects the first two bytes to be the sequence
- bind switches from `bind_socket(sock, ip.into(), CONNECTION_PORT)` to `bind_socket(sock, 0, CONNECTION_PORT)`
- client commands move away from generic read and write toward specialized game-specific requests
- diagnostic display state is expanded with `show_ip` and `last_read_err`

The newer PC client in `SSArchipelago` PR 53 matches this sequence-prefixed transport. The current `SS_APWorld` default branch still reflects the earlier pre-sequence command protocol.

## Call graph from injected code to IOS

Current PR 19 call graph:

1. hooked game code reaches `run_net_init`
2. `run_net_init` allocates an `IosAsyncContext` with `Box::pin_in(..., IosAllocator)`
3. `net_init_stuff` enters `server_loop`
4. `server_loop` opens `/dev/net/kd/request`
5. `server_loop` issues `IOCTL_NWC24_STARTUP`
6. `server_loop` opens `/dev/net/ip/top`
7. `server_loop` issues `IOCTL_SO_STARTUP`
8. `server_loop` issues `IOCTL_SO_GETHOSTID`
9. `server_loop` issues `IOCTL_SO_SOCKET` for UDP
10. `server_loop` issues `IOCTL_SO_BIND`
11. loop repeatedly issues `IOCTL_SO_RECV`
12. loop responds with `IOCTL_SO_SEND`
13. each async completion re-enters the pinned future through the IOS callback `post_ios`

Historical `rvl_os.rs` in PR 14 also includes a more elaborate async initialization chain plus a TCP accept path, but the transport actually used by the newer implementation is the simpler `rando/networking.rs` server loop.

## Device paths

Verified device paths used by Skyward Sword source:

- `/dev/net/kd/request`
- `/dev/net/ip/top`
- `/dev/net/ncd/manage`

Observed use:

- `/dev/net/kd/request`: `IOCTL_NWC24_STARTUP`
- `/dev/net/ip/top`: socket startup, host IP, socket create, bind, send, receive, close
- `/dev/net/ncd/manage`: only present in the broader support code path and initialization experiments; not required by the simpler PR 19 server loop

## IOS calls and command numbers

Verified direct IOS APIs used:

- `IOS_OpenAsync`
- `IOS_CloseAsync`
- `IOS_IoctlAsync`
- `IOS_IoctlvAsync`

Also declared in support code:

- `IOS_Open`
- `IOS_Close`
- `IOS_Ioctl`
- `IOS_Ioctlv`

Verified command numbers:

- request device `/dev/net/kd/request`
  - `6`: `IOCTL_NWC24_STARTUP`
- socket device `/dev/net/ip/top`
  - `31`: `IOCTL_SO_STARTUP`
  - `16`: `IOCTL_SO_GETHOSTID`
  - `15`: `IOCTL_SO_SOCKET`
  - `3`: `IOCTL_SO_CLOSE`
  - `2`: `IOCTL_SO_BIND`
  - `4`: `IOCTL_SO_CONNECT` in helper code
  - `10`: `IOCTL_SO_LISTEN` in helper code
  - `1`: `IOCTL_SO_ACCEPT` in helper code
  - `13`: `IOCTL_SO_SEND`
  - `12`: `IOCTL_SO_RECV`
  - `14`: `IOCTL_SO_SHUTDOWN` in older support code
- manage device `/dev/net/ncd/manage`
  - `7`: link status in older support code
  - `8`: MAC fetch in older support code

No evidence was found that the active Skyward Sword UDP server relies on libogc `net_init`, `net_socket`, `net_bind`, `net_sendto`, `net_recvfrom`, `net_fcntl`, `FIONBIO`, or `MSG_DONTWAIT`.

## Socket lifecycle

Skyward Sword source-backed UDP lifecycle:

1. start NWC24
2. start socket layer
3. get host IP
4. create UDP socket
5. bind UDP socket to port `43673`
6. wait for establish packet
7. store the client source IP and port from the establish packet
8. use that saved destination for later sends
9. on disconnect, clear the saved client endpoint and remain bound

PR 14 binds to the console IP returned by `IOCTL_SO_GETHOSTID`.

PR 19 binds to address `0`, which is effectively a wildcard bind in this implementation and matches the newer client guidance more closely.

## Data structures and layout

Verified transport structs:

- `SocketConnectParams`
  - `socket: c_int`
  - `has_addr: u32`
  - `sin_len: u8`
  - `sin_family: u8`
  - `sin_port: u16`
  - `sin_addr: u32`
  - `sin_zero: [u8; 20]`
  - `#[repr(C, align(0x20))]`
- `SocketAddrIn`
  - `sin_len: u8`
  - `sin_family: u8`
  - `sin_port: u16`
  - `sin_addr: u32`
  - `#[repr(C, align(0x20))]`
- PR 14 `SocketSendToParams`
  - `socket`
  - `flags`
  - `has_destaddr`
  - `destaddr: [u8; 8]`
- PR 19 `SocketSendToParams`
  - `socket`
  - `flags`
  - `has_destaddr`
  - `destaddr: [u8; 28]`
- `SocketRecvFromParams`
  - `socket`
  - `flags`
  - `#[repr(C, align(0x20))]`

Destination address encoding is explicitly big-endian:

- byte `0`: `8`
- byte `1`: `2`
- bytes `2..4`: port in big-endian order
- bytes `4..8`: IPv4 address bytes

## Byte order

Verified byte order handling:

- packet sequence is big-endian
- ports are big-endian
- IPv4 addresses are packed and unpacked with `to_be_bytes` and `from_be_bytes`
- client establish packet stores `[ip bytes][port bytes]` in network order

## Buffer alignment and allocation

The transport does not use ordinary stack-only plain C buffers.

Verified allocation and alignment strategy:

- request structs are declared with `#[repr(C, align(0x20))]`
- IOS message vectors are stored in aligned buffers
- async context objects are heap-allocated with `Box::new_in(..., IosAllocator)`
- IOS payload copies and send request heads in the older support code are allocated with `iosAllocAligned(IOS_HEAP, size, align)`
- allocator backing comes from game-visible `IOS_HEAP`

This means the active implementation is not allocation-free.

## Initialization assumptions already satisfied before injection

The code assumes the retail game already provides callable symbols for:

- `IOS_*`
- `iosAllocAligned`
- `iosFree`
- `IOS_HEAP`
- `OSInsertAlarm`
- `OSYieldThread`

The code does not initialize those primitives itself.

It also assumes the title's runtime environment tolerates:

- pinned async futures
- callback re-entry from IOS async completions
- IOS heap allocation
- alarm scheduling
- thread yielding

## Dependencies truly required versus inherited

### Clearly required by the active PR 19 server loop

- direct IOS APIs
- `IOS_HEAP` backed allocation
- aligned request and vector storage
- `OSInsertAlarm`
- `OSYieldThread`
- core alloc support for boxed pinned futures

### Present in the broader support code but not proven necessary for the active UDP server loop

- `/dev/net/ncd/manage`
- link-status and MAC fetch ioctls
- TCP listen and accept support
- shutdown and accept manager path from older support code

### Explicitly avoided relative to blind libogc linking

- no call to libogc `net_init`
- no call to libogc `net_socket`
- no full libogc startup object
- no arena bootstrap performed by this transport layer itself
- no libogc LWP queue setup in transport source

### Still not compatible with the Prime 3 target constraints

- dynamic allocation is used
- alarm support is used
- the loop is not single-step-per-poll
- the implementation performs an unbounded receive loop with `yield_thread()`
- the historical support layer includes extra runtime services that Prime 3 should not inherit

## Nonblocking and blocking behavior

No source-backed evidence shows Skyward Sword enabling socket nonblocking mode with `fcntl`, `ioctl`, `FIONBIO`, or `MSG_DONTWAIT`.

Instead, the implementation relies on asynchronous IOS requests:

- `IOS_IoctlAsync`
- `IOS_IoctlvAsync`

The receive path waits on an async completion and then loops again. That means the transport avoids blocking the game thread by using IOS async callbacks, not by turning the UDP socket itself into a conventional nonblocking descriptor.

This is a major difference from the current Prime 3 milestone requirement of one bounded nonblocking network step per recurring poll.

## Error handling and errno

Skyward Sword source does not implement a standard `errno` surface for the client.

Observed error handling:

- negative IOS return values are treated as errors
- `map_standard_result` converts negative results into `Err(...)`
- PR 19 stores the latest receive error in `SOCK_STATUS.last_read_err`
- older code comments identify `-8` as bad file descriptor during shutdown

No active source-backed use of `EWOULDBLOCK` was found.

## Dolphin and physical Wii behavior

Source-backed evidence:

- setup docs require the console and PC to be on the same network
- setup docs explicitly describe using the on-screen Wii IP with `/console`
- setup docs mention packet loss and client-side retry behavior
- PR 53 defaults client localhost behavior for Dolphin friendliness
- PR 19 adds `show_ip` state and bind-to-address-zero behavior that matches reconnect and on-screen IP guidance better than PR 14

This is evidence of intended support for both Dolphin and physical Wii, but it is not a substitute for Prime 3 live validation.

## Differences between Skyward Sword transport and Prime 3 CP3W

Skyward Sword protocol:

- port `43673`
- establish packet carries client IP and port
- PR 14 uses ad hoc command byte plus checksum for generic memory read and write
- PR 19 uses two-byte sequence prefix plus specialized gameplay commands
- gameplay protocol is game-specific and address-free in the newer form

Prime 3 CP3W:

- port `43674`
- protocol magic `CP3W`
- versioned framing
- negotiated capabilities
- read-only requirement in the current Prime 3 milestone
- no mailbox behavior in this milestone

Transport-relevant reusable ideas:

- direct IOS wrapper pattern
- aligned request struct pattern
- wildcard or explicit bind behavior
- explicit peer capture during establish
- async IOS rather than libogc socket wrappers

Protocol pieces that should not be transplanted:

- PR 14 memory write command
- PR 19 game-specific command set
- any address-free gameplay protocol
- any item or state mutation semantics

## Prime 3 architecture recommendation

Recommended Prime 3 transport architecture:

1. keep CP3W framing and host executor unchanged
2. write a clean project-owned direct IOS transport layer for Prime 3
3. use Skyward Sword only as MIT-licensed transport reference and ioctl provenance
4. do not import its dynamic allocation model
5. do not import its infinite async receive loop
6. do not import its gameplay protocol
7. keep Prime 3 transport developer-only and disabled by default
8. bind on UDP port `43674`
9. implement a fixed diagnostic datagram before CP3W parsing

Recommended minimal direct-IOS interface for Prime 3:

- open `/dev/net/kd/request`
- issue `IOCTL_NWC24_STARTUP`
- open `/dev/net/ip/top`
- issue `IOCTL_SO_STARTUP`
- optionally read host IP with `IOCTL_SO_GETHOSTID`
- issue `IOCTL_SO_SOCKET` for UDP
- issue `IOCTL_SO_BIND`
- issue at most one async receive or one async send completion per recurring runtime poll
- keep all transport state in runtime-owned fixed storage

## Reusable pieces versus clean-room pieces

### Safe to adapt directly with attribution

- command numbers
- device paths
- C-compatible socket struct layout
- destination address byte layout
- async IOS wrapper concept

### Should be independently implemented for Prime 3

- fixed-size runtime state machine
- no-allocation async bookkeeping
- bounded one-step-per-poll scheduler
- CP3W-specific receive and send path
- diagnostic packet format on port `43674`
- deterministic error reporting surface

## Exact blocker before CP3W integration

Skyward Sword proves that a Wii UDP transport can be built without blindly linking libogc, but its active implementation still violates several Prime 3 runtime constraints:

- it allocates from `IOS_HEAP`
- it uses boxed pinned futures
- it relies on `OSInsertAlarm`
- it performs a standing receive loop with `OSYieldThread`
- it is not structured as one bounded network step per Prime 3 recurring poll

So the blocker before CP3W integration is no longer transport provenance. The blocker is that Prime 3 still needs its own bounded, fixed-storage, no-allocation direct-IOS state machine built from this evidence.
