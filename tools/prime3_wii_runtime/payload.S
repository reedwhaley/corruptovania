.section .text.payload, "ax", @progbits
.global payload_entry
.type payload_entry, @function

payload_entry:
    blr

.size payload_entry, . - payload_entry
