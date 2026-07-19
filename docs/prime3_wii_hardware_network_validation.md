# Prime 3 Wii CP3W Hardware Network Validation

CP3W owns UDP port `43674`. Port `43673` and the Skyward Sword protocol are not part of this runtime.

## Runtime behavior

The native runtime waits 300 recurring-hook polls before its first initialization attempt. It then opens the Wii network devices, starts NWC24 and `/dev/net/ip/top`, obtains the host ID, creates a UDP socket, binds `0.0.0.0:43674`, and verifies the result with IOS `SOGetSockName` before entering the receive loop. The receive is asynchronous and does not block the game thread.

Initialization and socket failures retain their native signed return code and error phase. With automatic retry enabled, failures enter a 120-poll delay. A failed active socket enters `SOCKET_LOST`, closes its descriptor, and recreates and rebinds the socket. A manual restart is deferred until no asynchronous operation is pending, then follows the same descriptor-safe recovery path.

## Diagnostic ABI

The payload manifest fields `network_diagnostics_address`, `network_diagnostics_size`, and `network_diagnostics_version` locate the big-endian `CP3D` structure. Version 1 is exactly `0x100` bytes (64 `u32` words). Signed result and descriptor fields use two's-complement `s32` values.

| Word range | Fields |
| --- | --- |
| 0-6 | magic, version, size, build ID, current phase, previous phase, transition count |
| 7-14 | IOS version/revision, initialization attempts/successes, restart/recovery counts, initial/retry delays |
| 15-24 | network, NWC24, and host-ID results; host IP; socket descriptor; socket, bind, getsockname, last-error results; error phase |
| 25-32 | requested address/port, actual address/port, byte-order flag, listening flag, receive-active flag, receive-call count |
| 33-42 | received/malformed/transient/fatal counts, send calls/packets/failures, close/shutdown/cleanup counts |
| 43-54 | network-device close count, last close/shutdown descriptors, last command/size/sender, heartbeat result, uptime, last bind/RX/TX polls |
| 55-63 | restart, heartbeat, overlay, page, auto-retry and reset controls; socket-loss, getsockname, and receive-loop counters |

Control words are written as big-endian `u32` values at these offsets from `network_diagnostics_address`:

- `0xDC`: request a safe network restart
- `0xE0`: send `CP3W-DIAG-HEARTBEAT\0<build-id><phase>` to the last CP3W peer
- `0xE4`: overlay-enabled state reserved for a Lua host
- `0xE8`: overlay page reserved for a Lua host
- `0xEC`: automatic retry (`1` by default)
- `0xF0`: reset packet/error counters

The repository does not contain the game's Lua 5.0.1 host bindings, controller-input API, or text-rendering API. Consequently, this change exposes the stable native structure and controls but does not invent Lua bindings or conflicting controller combinations. `observe_probe.py` reads and decodes the same structure for Dolphin testing. A future game-side Lua integration should only read these fields and write the control words; it must not own IOS networking.

New recovery phases are `INITIAL_DELAY=96`, `VERIFY_BOUND_ENDPOINT=97`, `WAIT_VERIFY_BOUND_ENDPOINT=98`, `LISTENING=99`, `RETRY_DELAY=100`, `RESTART_REQUESTED=101`, `SOCKET_LOST=102`, `CLOSE_SOCKET_FOR_RECOVERY=103`, `WAIT_CLOSE_SOCKET_FOR_RECOVERY=104`, `SUBMIT_HEARTBEAT=105`, `WAIT_HEARTBEAT=106`, and `FATAL_ERROR=107`.

## Desktop probe

Run a real CP3W HELLO against the hardware runtime:

```powershell
python tools/prime3_wii_runtime/udp_diagnostic_client.py --host 192.168.50.19 --timeout 1 --retries 5 --output cp3w-probe.json
```

The CLI accepts only port `43674`. A successful report includes the local and remote endpoints, UTC attempt timestamp, request and response lengths/hex, round-trip time, negotiated capabilities, session ID, runtime mode, and runtime build ID. Exit status `2` means timeout, `4` means malformed protocol data, and `5` means a socket error. Windows may surface an ICMP Port Unreachable as a timeout or a socket error depending on UDP stack behavior.

## Hardware procedure

1. Build the patched game from `prime3-wii-networking` and record the manifest and payload hashes.
2. Record `runtime_build_id` from the desktop HELLO response or the native diagnostic block.
3. Record IOS version/revision if the loader exposes them; the current native ABI reserves these fields but Prime 3 has no verified IOS-version accessor yet.
4. Record all native initialization return values and the last error phase.
5. Confirm requested endpoint `0.0.0.0:43674`, actual port `43674`, and `listening=1`.
6. Run the desktop probe while capturing traffic in Wireshark.
7. Record whether the console returns ICMP Port Unreachable, a CP3W response, or neither.
8. Set restart request word `0xDC` after the title screen, wait through recovery, and probe again.
9. Load a save, repeat restart and probe, and compare close/recovery/socket-loss counters.
10. After at least one client request, set heartbeat word `0xE0` and capture the diagnostic datagram.
11. Compare USB Loader GX and WiiFlow if practical.
12. Test the original Skyward Sword integration separately as an external control without changing CP3W.

The decisive hardware evidence is the transition sequence and exact signed result values. `bind_result=0`, `getsockname_result=0`, `actual_bind_port=43674`, and `listening=1` prove that the listener existed; a later socket-loss or close counter increase distinguishes subsequent teardown from failure to bind.
