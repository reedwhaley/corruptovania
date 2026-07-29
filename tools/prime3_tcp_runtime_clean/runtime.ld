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
        __cp3c_config_start = runtime_cp3c_config_block;
        __cp3c_server_ipv4 = runtime_cp3c_config_block + 12;
        __cp3c_server_port = runtime_cp3c_config_block + 16;
        KEEP(*(.runtime_state.canary))
        *(.runtime_state .runtime_state.*)
        *(.data .data.*)
        *(.bss .bss.* COMMON)
        __cp3c_config_end = runtime_cp3c_config_block + 32;
    }
    runtime_state_end = .;

    /DISCARD/ :
    {
        *(.comment)
        *(.eh_frame)
        *(.note*)
    }
}
