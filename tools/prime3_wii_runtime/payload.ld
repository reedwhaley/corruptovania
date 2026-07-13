OUTPUT_ARCH(powerpc:common)
ENTRY(payload_entry)

SECTIONS
{
    . = DEFINED(__payload_link_address) ? __payload_link_address : 0;

    .text : ALIGN(4)
    {
        KEEP(*(.text.payload))
        *(.text .text.*)
    }

    /DISCARD/ :
    {
        *(.comment)
        *(.eh_frame)
        *(.note*)
    }
}
