.section .text.payload, "ax", @progbits

.global payload_entry
.type payload_entry, @function

#ifdef PRIME3_RUNTIME_PROBE_MODE
.global payload_canary_start
.global payload_canary_end
.global payload_execution_counter

# This startup probe runs under the DOL entry stub, not a normal game ABI call.
# It preserves volatile machine state explicitly, increments only its payload-local
# execution counter, reproduces the displaced `li r0, 0`, and returns to the hook caller.
payload_entry:
    stwu    1, -0x90(1)
    mflr    0
    stw     0, 0x94(1)
    stmw    3, 0x08(1)
    mfcr    12
    stw     12, 0x04(1)
    mfctr   0
    stw     0, 0x80(1)
    mfxer   0
    stw     0, 0x84(1)

    bl      1f
1:
    mflr    12
    addi    11, 12, payload_execution_counter - 1b
    lwz     10, 0(11)
    addi    10, 10, 1
    stw     10, 0(11)

    lwz     0, 0x84(1)
    mtxer   0
    lwz     0, 0x80(1)
    mtctr   0
    lwz     12, 0x04(1)
    mtcrf   0xFF, 12
    lmw     3, 0x08(1)
    lwz     12, 0x94(1)
    mtlr    12
    addi    1, 1, 0x90
    li      0, 0
    blr

.size payload_entry, . - payload_entry

.balign 32
payload_canary_start:
    .byte   0x50, 0x33, 0x57, 0x49, 0x49, 0x50, 0x52, 0x4F
    .byte   0x42, 0x45, 0x43, 0x41, 0x4E, 0x41, 0x52, 0x59
payload_canary_end:

.balign 4
payload_execution_counter:
    .long   0
#else
payload_entry:
    blr

.size payload_entry, . - payload_entry
#endif
