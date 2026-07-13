.section .text.runtime, "ax", @progbits

.global runtime_entry
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

.type runtime_entry, @function

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

runtime_code_end:
.size runtime_entry, . - runtime_entry

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
runtime_state_end:
