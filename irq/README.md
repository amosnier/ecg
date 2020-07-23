The files located in the sub-directories of this directory are
systematically fetched from
https://github.com/STMicroelectronics/cmsis_device_xx, where `xx` stands
for `f4`, `f7`, `h7`, `g4`, `l4`, etc. Some more series could be added
in the future. All the examples mentioned above are available at the
time of writing, among others.

The files fetched are startup assembly files for the ARM toolchain, but
we do not really care about the actual assembly code. The only purpose
of fetching those files is to extract interrupt and exception vector
table information in a systematic manner, in order to automatically
generate our own C++ code for those.

ST's startup templates in assembly are the only vector table
specification provided by ST in text form that we know of.

Also, we arbitrarily choose the ARM toolchain version of these files,
because it feels like the cleanest version, although it does not matter
that much: all the variant provide the same information, and the name
conventions for the IRQ handler a re strictly the same everywhere, as
far as we can. Those names are apparently derived from a source that is
common to processor manuals and code.

For instance, if the manual mentions the acronym `TAMP_STAMP` for an
interrupt with description "Tamper and TimeStamp interrupts through the
EXTI line", all assembly startup files will have an ISR with name
'TAMP_STAMP_IRQHandler' and a comment which repeats the exact same text
as the one in the manual.

It is worth noting that in the naming convention for ARM Cortex M
interrupts (common to all MCUs), the word "Handler", instead of
"IRQHandler" is added to the interrupt acronym to form the ISR name.
