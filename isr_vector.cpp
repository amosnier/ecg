#include "isr.h"

/*
 * The following symbol is defined by the linker script.
 */

extern int _estack;

[[gnu::section (".isr_vector"), maybe_unused]] void (* const isr_vector[])() = {

	/*
	 * The ISR vector is an array of pointers to void functions that take no arguments (interrupt service routines),
	 * except for the first position, that contains the initial value of the stack pointer. For now, it is only
	 * valid for STM32F746xx, but it could be generalized with the help of compile time flags.
	 *
	 * There is of course a hard association between the position of a given ISR in the table and the exception it
	 * serves (see processor manuals)!
	 */

	reinterpret_cast<void (*)()>(&_estack),
};
