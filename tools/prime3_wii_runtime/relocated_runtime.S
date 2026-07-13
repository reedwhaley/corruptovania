.section .text.runtime, "ax", @progbits

.global runtime_entry
.global runtime_poll_entry
.global runtime_poll_hook_wrapper
.global runtime_code_start
.global runtime_code_end
.global runtime_state_start
.global runtime_state_end
.global runtime_canary_start
.global runtime_canary_end
.global runtime_copy_complete_marker
.global runtime_executed_marker
.global runtime_execution_counter
.global runtime_status
.global runtime_bootstrap_return_marker
.global runtime_poll_counter
.global runtime_poll_heartbeat
.global runtime_poll_last_sequence

.type runtime_entry, @function
.type runtime_poll_entry, @function
.type runtime_poll_hook_wrapper, @function

runtime_code_start:
runtime_entry:
    lis     11, runtime_executed_marker@h
    ori     11, 11, runtime_executed_marker@l
    lis     12, PRIME3_RUNTIME_EXECUTED_MARKER_VALUE@h
    ori     12, 12, PRIME3_RUNTIME_EXECUTED_MARKER_VALUE@l
    stw     12, 0(11)

    lis     11, runtime_execution_counter@h
    ori     11, 11, runtime_execution_counter@l
    lwz     12, 0(11)
    addi    12, 12, 1
    stw     12, 0(11)

    lis     11, runtime_status@h
    ori     11, 11, runtime_status@l
    lis     12, PRIME3_RUNTIME_SUCCESS_STATUS_VALUE@h
    ori     12, 12, PRIME3_RUNTIME_SUCCESS_STATUS_VALUE@l
    stw     12, 0(11)
    blr

.size runtime_entry, . - runtime_entry

runtime_poll_entry:
    lis     11, runtime_poll_counter@h
    ori     11, 11, runtime_poll_counter@l
    lwz     12, 0(11)
    addi    12, 12, 1
    stw     12, 0(11)

    lis     11, runtime_poll_heartbeat@h
    ori     11, 11, runtime_poll_heartbeat@l
    stw     12, 0(11)

    lis     11, runtime_poll_last_sequence@h
    ori     11, 11, runtime_poll_last_sequence@l
    stw     12, 0(11)
    blr

.size runtime_poll_entry, . - runtime_poll_entry

runtime_poll_hook_wrapper:
    stwu    1, -0x30(1)
    mflr    0
    stw     0, 0x2C(1)
    mfcr    0
    stw     0, 0x28(1)
    mfxer   0
    stw     0, 0x24(1)
    stw     3, 0x20(1)
    bl      runtime_poll_entry
    lwz     3, 0x20(1)
    lwz     0, 0x24(1)
    mtxer   0
    lwz     0, 0x28(1)
    mtcrf   0xFF, 0
    lwz     0, 0x2C(1)
    mtlr    0
    addi    1, 1, 0x30
    lwz     3, 0x24(3)
    lis     12, PRIME3_RUNTIME_POLL_HOOK_CONTINUATION_ADDRESS@h
    ori     12, 12, PRIME3_RUNTIME_POLL_HOOK_CONTINUATION_ADDRESS@l
    mtctr   12
    bctr

.size runtime_poll_hook_wrapper, . - runtime_poll_hook_wrapper

runtime_code_end:

.balign 32
runtime_state_start:
runtime_canary_start:
    .byte   0x50, 0x33, 0x48, 0x49, 0x52, 0x55, 0x4E, 0x54
    .byte   0x49, 0x4D, 0x45, 0x43, 0x41, 0x4E, 0x41, 0x52
runtime_canary_end:

.balign 4
runtime_copy_complete_marker:
    .long   0
runtime_executed_marker:
    .long   0
runtime_execution_counter:
    .long   0
runtime_status:
    .long   0
runtime_bootstrap_return_marker:
    .long   0
runtime_poll_counter:
    .long   0
runtime_poll_heartbeat:
    .long   0
runtime_poll_last_sequence:
    .long   0
runtime_state_end:
