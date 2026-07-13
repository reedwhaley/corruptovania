OUTPUT_ARCH(powerpc:common)
ENTRY(runtime_entry)

SECTIONS
{
    . = DEFINED(__runtime_link_address) ? __runtime_link_address : 0;

    .text : ALIGN(4)
    {
        KEEP(*(.text.runtime))
        *(.text .text.*)
        *(.rodata .rodata.*)
        *(.data .data.*)
        *(.bss .bss.* COMMON)
    }

    /DISCARD/ :
    {
        *(.comment)
        *(.eh_frame)
        *(.note*)
    }
}
