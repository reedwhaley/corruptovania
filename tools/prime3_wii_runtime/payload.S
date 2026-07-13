.section .text.payload, "ax", @progbits

.global payload_entry
.type payload_entry, @function

#ifdef PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODE
.global payload_save_area_start
.global payload_save_area_end
.global payload_halt_loop

.set LOW_MEMORY_ARENA_HIGH, 0x80000034
.set LOW_MEMORY_MEM1_END, 0x80003110
.set BOOTSTRAP_CONTINUATION, 0x80006324
.set BOOTSTRAP_TARGET, 0x8000648C
.set DIAGNOSTIC_CANARY_OFFSET, 0x00
.set DIAGNOSTIC_SCHEMA_OFFSET, 0x10
.set DIAGNOSTIC_MARKER_OFFSET, 0x14
.set DIAGNOSTIC_COUNTER_OFFSET, 0x18
.set DIAGNOSTIC_ORIGINAL_34_OFFSET, 0x1C
.set DIAGNOSTIC_ORIGINAL_3110_OFFSET, 0x20
.set DIAGNOSTIC_REPLACEMENT_OFFSET, 0x24
.set DIAGNOSTIC_STATUS_OFFSET, 0x28
.set DIAGNOSTIC_SCHEMA_VALUE, 0x00000001
.set DIAGNOSTIC_MARKER_VALUE, 0x50334254
#ifdef PRIME3_RUNTIME_ENTRY_BOOTSTRAP_HALT
.set DIAGNOSTIC_STATUS_VALUE, 0xB0070001
#else
.set DIAGNOSTIC_STATUS_VALUE, 0xB0070002
#endif

.set STACK_FRAME_SIZE, 0x20
.set SAVE_R0_OFFSET, 0x00
.set SAVE_R10_OFFSET, 0x04
.set SAVE_R11_OFFSET, 0x08
.set SAVE_R12_OFFSET, 0x0C

payload_entry:
    stwu    1, -STACK_FRAME_SIZE(1)
    stw     0, SAVE_R0_OFFSET(1)
    stw     10, SAVE_R10_OFFSET(1)
    stw     11, SAVE_R11_OFFSET(1)
    stw     12, SAVE_R12_OFFSET(1)

    lis     11, LOW_MEMORY_ARENA_HIGH@h
    ori     11, 11, LOW_MEMORY_ARENA_HIGH@l
    lwz     12, 0(11)
    lis     10, (PRIME3_BOOTSTRAP_DIAGNOSTIC_ADDRESS + DIAGNOSTIC_ORIGINAL_34_OFFSET)@h
    ori     10, 10, (PRIME3_BOOTSTRAP_DIAGNOSTIC_ADDRESS + DIAGNOSTIC_ORIGINAL_34_OFFSET)@l
    stw     12, 0(10)

    lis     11, LOW_MEMORY_MEM1_END@h
    ori     11, 11, LOW_MEMORY_MEM1_END@l
    lwz     12, 0(11)
    lis     10, (PRIME3_BOOTSTRAP_DIAGNOSTIC_ADDRESS + DIAGNOSTIC_ORIGINAL_3110_OFFSET)@h
    ori     10, 10, (PRIME3_BOOTSTRAP_DIAGNOSTIC_ADDRESS + DIAGNOSTIC_ORIGINAL_3110_OFFSET)@l
    stw     12, 0(10)

    lis     11, PRIME3_BOOTSTRAP_RESERVED_HIGH@h
    ori     11, 11, PRIME3_BOOTSTRAP_RESERVED_HIGH@l
    lis     12, LOW_MEMORY_ARENA_HIGH@h
    ori     12, 12, LOW_MEMORY_ARENA_HIGH@l
    stw     11, 0(12)
    lis     12, LOW_MEMORY_MEM1_END@h
    ori     12, 12, LOW_MEMORY_MEM1_END@l
    stw     11, 0(12)

    lis     12, PRIME3_BOOTSTRAP_DIAGNOSTIC_ADDRESS@h
    ori     12, 12, PRIME3_BOOTSTRAP_DIAGNOSTIC_ADDRESS@l
    lis     0, 0x5033
    ori     0, 0, 0x424F
    stw     0, DIAGNOSTIC_CANARY_OFFSET + 0(12)
    lis     0, 0x4F54
    ori     0, 0, 0x5354
    stw     0, DIAGNOSTIC_CANARY_OFFSET + 4(12)
    lis     0, 0x5241
    ori     0, 0, 0x5043
    stw     0, DIAGNOSTIC_CANARY_OFFSET + 8(12)
    lis     0, 0x414E
    ori     0, 0, 0x5259
    stw     0, DIAGNOSTIC_CANARY_OFFSET + 12(12)

    lis     0, DIAGNOSTIC_SCHEMA_VALUE@h
    ori     0, 0, DIAGNOSTIC_SCHEMA_VALUE@l
    stw     0, DIAGNOSTIC_SCHEMA_OFFSET(12)
    lis     0, DIAGNOSTIC_MARKER_VALUE@h
    ori     0, 0, DIAGNOSTIC_MARKER_VALUE@l
    stw     0, DIAGNOSTIC_MARKER_OFFSET(12)
    lwz     0, DIAGNOSTIC_COUNTER_OFFSET(12)
    addi    0, 0, 1
    stw     0, DIAGNOSTIC_COUNTER_OFFSET(12)
    stw     11, DIAGNOSTIC_REPLACEMENT_OFFSET(12)
    lis     0, DIAGNOSTIC_STATUS_VALUE@h
    ori     0, 0, DIAGNOSTIC_STATUS_VALUE@l
    stw     0, DIAGNOSTIC_STATUS_OFFSET(12)

#ifdef PRIME3_RUNTIME_ENTRY_BOOTSTRAP_HALT
payload_halt_loop:
    b       payload_halt_loop
#else
    lis     11, BOOTSTRAP_CONTINUATION@h
    ori     11, 11, BOOTSTRAP_CONTINUATION@l
    mtlr    11
    lis     12, BOOTSTRAP_TARGET@h
    ori     12, 12, BOOTSTRAP_TARGET@l
    mtctr   12
    lwz     0, SAVE_R0_OFFSET(1)
    lwz     10, SAVE_R10_OFFSET(1)
    lwz     11, SAVE_R11_OFFSET(1)
    lwz     12, SAVE_R12_OFFSET(1)
    addi    1, 1, STACK_FRAME_SIZE
    bctr
#endif

.size payload_entry, . - payload_entry

.balign 4
payload_save_area_start:
    .space  16
payload_save_area_end:

#elif defined(PRIME3_RUNTIME_PROBE_MODE)
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
