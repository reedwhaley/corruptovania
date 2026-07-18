# Prime 3 Wii and Wii U Connection

CDV supports **Dolphin** through Dolphin Memory Engine and **Wii / Wii U (Prime 3)** through the CP3W UDP runtime.
Prime 3 seed generation automatically validates the source DOL, applies the normal randomizer patches, injects the
canonical CP3W runtime, installs its startup and recurring poll hooks, validates the finished DOL, and then writes the
requested ISO or WBFS. There is no second networking patch command or manual injection step.

The hardware connection is read-only inventory synchronization. It does not track locations, write or grant items,
display messages in-game, or expose arbitrary memory reads or writes.

## Generate and Connect

1. Generate a normal Prime 3 seed from a supported NTSC-U Wii revision 3.436 source image.
2. Launch the generated ISO or WBFS on an original Wii or a Wii U in vWii mode.
3. Open CDV's game connection window and add **Wii / Wii U (Prime 3)**.
4. Enter only the console IPv4 address, for example `192.168.1.42`.

CDV binds an ephemeral local UDP port and sends to protocol-defined remote UDP port **43674**. The port is not
configurable or persisted. The console and computer must be on the same LAN without guest-network/client isolation,
and the host firewall must allow CDV's UDP traffic. CDV does not modify firewall rules or scan the network.

The client performs HELLO and capability negotiation, then `GET_GAME_IDENTITY`, then continuous `GET_INVENTORY`.
The supported identity is Prime 3 Corruption, Wii, NTSC-U, revision 3.436, profile `0x50334E41`, fingerprint
`0x67B00CE6`. Unsupported executables are rejected before patching, and unsupported runtime identities are rejected
before inventory polling.

## Connection Behavior

The connection reports connecting, negotiation, identity validation, connected, temporarily unavailable,
reconnecting, disconnecting, and error states. Diagnostics include the console IP, fixed port, identity, inventory
sequence and availability, round-trip time, timeout count, and last error.

A temporarily unavailable snapshot keeps the session connected and retains the previous inventory as stale. Runtime
restart, sequence reset, or `NOT_NEGOTIATED` triggers renegotiation. Three consecutive inventory timeouts trigger a
reconnect; builder reconnect delays are bounded at 1, 2, 4, 8, and 10 seconds. Packets from unexpected endpoints,
duplicate responses, malformed responses, and unrelated request IDs are rejected or ignored with diagnostics.

## Troubleshooting

- **Source rejected:** Use the supported Prime 3 Wii NTSC-U 3.436 executable. Profile checks are not bypassable.
- **Wii did not respond:** Verify the console IPv4 address, game state, firewall, UDP 43674, and LAN isolation settings.
- **Missing capability:** Regenerate the game with a current CDV build containing identity and inventory support.
- **Temporarily unavailable:** Return to a playable state; polling and recovery continue automatically.
- **Repeated reconnects:** Check packet loss, VPN/router boundaries, firewall behavior, and the connection diagnostics.

## Physical Validation

Software and Dolphin tests do not prove behavior on physical consoles. Validate separately on an original Wii and a
Wii U in vWii mode: boot the generated image, connect by IPv4, confirm identity and changing inventory, exercise title,
load, room transition, temporary unavailability, runtime restart, network interruption, reconnect, and clean shutdown.
Do not treat a loopback or Dolphin result as physical Wii or Wii U evidence.
