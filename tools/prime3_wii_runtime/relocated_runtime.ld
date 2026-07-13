OUTPUT_ARCH(powerpc:common)
ENTRY(runtime_entry)

SECTIONS
{
    . = DEFINED(__runtime_link_address) ? __runtime_link_address : 0;

    runtime_code_start = .;
    .text : ALIGN(4)
    {
        KEEP(*(.text.runtime.entry))
        KEEP(*(.text.runtime.keep))
        *(.text.runtime .text.runtime.*)
        *(.text .text.*)
        *(.rodata .rodata.*)
    }
    runtime_code_end = .;

    . = ALIGN(32);
    runtime_state_start = .;
    .runtime_state : ALIGN(32)
    {
        KEEP(*(.runtime_state.canary))
        *(.runtime_state .runtime_state.*)
        *(.data .data.*)
        *(.bss .bss.* COMMON)
    }
    runtime_state_end = .;

    /DISCARD/ :
    {
        *(.comment)
        *(.eh_frame)
        *(.note*)
    }
}
