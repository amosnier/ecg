# ecg [![Build Status](https://travis-ci.org/amosnier/ecg.svg?branch=master)](https://travis-ci.org/amosnier/ecg)
C++ code generator for embedded systems
## Name and purpose
At the moment, `ecg`'s only ability is to generate C++ header files from
[CMSIS System View Description file](http://www.keil.com/pack/doc/CMSIS/SVD/html/index.html). It may or may not grow
and at some point better reflect the possible interpretation of its name as a general acronym for "C++ code generator
for embedded systems".
## Prerequisites
Python 3 is required to run `ecg`, as well as the package `xmltodict`.
If you are lucky enough to run `virtualenv` and `virtualenvwrapper`, getting this could be as simple as:
```shell
$ mkvirtualenv ecg_venv -p /usr/bin/python3 && pip install xmltodict
```
`ecg_venv` is of course just an arbitrary name. Just pick whatever you like.

Also, a compiler that supports C++17 is required to compile the generated code.
## Syntax
The syntax for `ecg` is as illustrated below.
```shell
$ python ecg.py --help
usage: ecg.py [-h] -o OUTPUT [-n NAMESPACE] svd_file

Generate a C++ header file from an ARM Cortex SVD file.

positional arguments:
  svd_file              SVD file

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        C++ header file name (default: None)
  -n NAMESPACE, --namespace NAMESPACE
                        C++ namespace (default: mcu_support)
```

A test script is provided:
```shell
$ time python test.py 
[...]
svd/STM32H7/STM32H743x.svd		->	generated/STM32H7/STM32H743x/mcu.h
STM32H743x specified as little-endian
Please double-check endianness assumption by running provided runtime checking function on target!
Generating code for 128 peripherals...

generated 57 files

real	0m12,473s
user	0m12,251s
sys	0m0,220s
```

You do not have to `time` the command of course. You should however be aware of the fact the tests take a little
while to run. They generate C++ header files for pretty much all current STMicroelectronics' STM32 MCUs for which
SVD files are available. Note that this repository is in no way affiliated with STMicroelectronics. I just happen
to work quite a lot with STM32 MCUs these days. Also note that so far, no effort has been put into optimizing `ecg`
for performance.

The SVD files used by the tests can be found under [svd](svd), and the resulting header files are generated under
a `generated` directory. All the generated files are called `mcu.h`, and each file is stored in its own directory. You
are of course free to decide on your own structure and naming conventions when you use `ecg`.

The test script can also be ordered to test-compile every generated file:
```shell
$ time python test.py -c /home/alain/custom/bin/gcc-arm-none-eabi/bin/arm-none-eabi-gcc
[...]
STM32H743x specified as little-endian
Please double-check endianness assumption by running provided runtime checking function on target!
Generating code for 128 peripherals...

Running: /home/alain/custom/bin/gcc-arm-none-eabi/bin/arm-none-eabi-gcc -std=c++17 -o build/test.o -c test.cpp -I generated/STM32H7/STM32H743x
Compilation successful

generated 57 files

real	0m27,762s
user	0m27,164s
sys	0m0,568s
```

The compilation has many `static_assert`-invocations that check the offset of every register in every peripheral. In
fact, these unit tests where able to automatically detect a number of errors in ... ST's  SVD files! These were
corrected in commit [4c7f67e761](https://github.com/amosnier/ecg/commit/4c7f67e7616181aec0b9210b735cb6b9b2cc957e),
and reported to ST.

## Limitations
### ARM Cortex families and endianness
`ecg` has the ambition to handle any [SVD](https://arm-software.github.io/CMSIS_5/SVD/html/index.html) -file as its
input. SVD implies [CMSIS](https://developer.arm.com/tools-and-software/embedded/cmsis), which implies ARM Cortex.
However, I have so far only used `ecg` for Cortex-M MCUs. Whether generating C++-header files for other Cortex
variants would even be interesting is unclear at the time of writing. Please
[report any issue](https://github.com/amosnier/ecg/issues) that you may encounter in your own use cases.

Also, `ecg` chooses to generate bit-fields to conveniently map registers (see
[Frequently asked questions](#frequently-asked-questions)). While this indeed is convenient, it unfortunately forces
the code to make an assumption about the processor's endianness. For Cortex-M, this
[does not seem to be a problem](https://stackoverflow.com/questions/61701973/does-arm-assume-that-all-cortex-m-microcontrollers-are-little-endian).
The SVD files are in fact supposed to include [endianness information](https://arm-software.github.io/CMSIS_5/SVD/html/elem_cpu.html).
But unfortunately, they sometimes do not.

To handle this issue, `ecg`'s strategy is the following:
- Only support for little-endian MCUs is provided until further notice.
- When the SVD file includes endianness information, `ecg` asserts that little-endian is specified.
- When the SVD file does not include endianness information, `ecg` assumes that little-endian applies. In any case,
`ecg` provides a runtime checking function and recommends to run it for every combination MCU/toolchain.

Also, at the time of writing, only one of the generated files has been tested in a debugger on target. If you use
`ecg`, please do not blindly rely on the generated code, check it!

Finally, while `ecg` seems to work on quite many STM32 SVD files, it has not been tested on other vendors' SVD files,
or other processor families. I am not sure how strict the SVD specification and its implementations are. I would not be
surprised if `ecg` needed a few adjustments for it to work with other vendors or processor families. Again, please
[report any issue that you may find](https://github.com/amosnier/ecg/issues).

### What is automatically tested and what is not
[Travis](https://travis-ci.org/github/amosnier/ecg) automatically runs the tests mentioned above for every commit, i.e.
successful code generation and successful compilation of the generated code, including many
`static_assert`-invocations that check the offset of every register in every peripheral in the ARM ABI.

Unfortunately, correct endianness can only be tested at runtime, and it is strongly recommended to run the generated
runtime checking function.

## Cost for the target system
If we except the runtime checking function, which would typically not be linked in an application deployed in the
field, the only cost for the code generated by `ecg` from an SVD file is at most one peripheral address per peripheral.

Typical numbers of peripherals in the test SVD files are 70 to 140. For 140, the maximum cost would be 560 bytes (a
peripheral address is 4 byte-wide on an STM32 MCU), typically in flash memory. I say maximum cost, because in my
experience, compilers are nowadays quite good at detecting multiple copies of a constant in a text segment, and
removing redundancies. Under such an assumption, the cost for a peripheral that is used in the application would be
zero. If we really want to, we could eliminate all the non-used peripherals with the help of compile time flags.

At one compile flag per peripheral, that is quite many compile time flags. Please
[report an issue](https://github.com/amosnier/ecg/issues) if this is a feature of interest.

## Frequently asked questions
### C++? Isn't C a better language for embedded development?
My customers and I mostly use `gcc` for embedded development, which gives access to both C and C++. I believe other
compilers for currently available micro-controllers also give access to both C and C++. C++ being a superset of C for
all practical purposes, which adds some useful features (this is of course an understatement), I do not see any reason
to limit myself or my customers. Furthermore, I believe that C++, if used rationally, can help to vastly improve
embedded code bases.

For those reasons, I do not intend to spend time on making the code generated by `ecg` compatible with the C-language.
### Why would we need new header files? Isn't that redundant with CMSIS and the libraries provided by micro-controller vendors?
Yes, it is redundant.

But let me tell you a story. Ten years ago, I worked with a 16-bit micro-controller that had quite many peripherals.
They were memory-mapped. In the source code, we had a large C-`struct` that matched the whole memory map. It had two
benefits:
1. We could inspect and change the contents of all peripheral registers in a regular debugger variable view.
2. Access to the peripheral registers from our device drivers was obvious and straightforward.

Today, when I work with one of ST's STM32 MCUs, if I want to inspect or update some peripheral registers (there are
MANY of them in a modern MCU), I typically use a peripheral view plugin in my IDE. While that mostly works (but
can for instance get broken by the latest IDE upgrade), it unnecessarily increases my dependency on my IDE. If that
solution somehow breaks, I have to switch to plan B: I look for a C-`struct` in the vendor's library that corresponds
to the relevant peripheral, I look up the peripheral's base address in the micro-controller manual (routinely more
than 1500 pages), and I use some `gdb`-cast tricks in a variable view interface to display the registers I need to
inspect/update. This is of course not particularly efficient, but ST's support libraries, as far as I know, do not
provide a better solution. I do not know whether other vendors do, but the fact that part of the library files are
produced by ARM, while others are produced by MCU vendors is an obstacle for a centralized solution.

So while a new header file that maps all the MCU peripherals is redundant with the source code already provided by the
vendor, it also fulfils a need that is not fulfilled today.

It should be noted that given the arguments above, fulfilment of the
[CMSIS](https://developer.arm.com/tools-and-software/embedded/cmsis) (Cortex Microcontroller Software Interface
Standard) is not a design goal for the code generated by `ecg`.    
### What do these header files look like?
For instance, the `struct` that corresponds to the system control block peripheral starts in this way:
```C++
/**
 * @brief System control block
 *
 * groupName: SCB
 * baseAddress: 0xE000ED00
 * addressBlock:
 * 	offset: 0x0
 * 	size: 0x41
 * 	usage: registers
 */
struct SCB {
	/**
	 * @brief CPUID base register
	 *
	 * displayName: CPUID
	 * addressOffset: 0x0
	 * size: 0x20
	 * access: read-only
	 * resetValue: 0x410FC241
	 */
	const struct CPUID {
		uint32_t Revision: 4; /**< Revision number */
		uint32_t PartNo: 12; /**< Part number of the processor */
		uint32_t Constant: 4; /**< Reads as 0xF */
		uint32_t Variant: 4; /**< Variant number */
		uint32_t Implementer: 8; /**< Implementer code */
	} cpuid_;
// ...
};
```

Of course read-only registers and fields are declared as const (write-only can unfortunately not be enforced in C++,
or C, for that matter).

One design goal is to integrally transfer the information contained in the SVD files to the generated header files,
either in the form of data fields, or in the form of comments in the generated code, i.e. no information should be
lost in the transformation.
### Bit-fields? But the C++-standard does not provide any guarantee for how they are laid out!
This is true. According to the C++-standard, packing and endianness are implementation defined.

However:
- Since we want to map hardware registers for a specific MCU, portability across multiple processors is irrelevant.
- While the C++ standard does not provide any guarantee, toolchains that generate code for ARM targets are expected
to fulfill the
[Procedure Call Standard for the Arm Architecture](https://developer.arm.com/docs/ihi0042/latest) (aka AAPCS), an ABI
(Application Binary Interface).

In fact, as an example among others, the Application Program Status Register (APSR) is mapped in the following way in
[core_cm7.h](https://github.com/ARM-software/CMSIS/blob/master/CMSIS/Include/core_cm7.h), an official CMSIS core file
from ARM:

```C
/**
  \brief  Union type to access the Application Program Status Register (APSR).
 */
typedef union
{
  struct
  {
    uint32_t _reserved0:16;              /*!< bit:  0..15  Reserved */
    uint32_t GE:4;                       /*!< bit: 16..19  Greater than or Equal flags */
    uint32_t _reserved1:7;               /*!< bit: 20..26  Reserved */
    uint32_t Q:1;                        /*!< bit:     27  Saturation condition flag */
    uint32_t V:1;                        /*!< bit:     28  Overflow condition code flag */
    uint32_t C:1;                        /*!< bit:     29  Carry condition code flag */
    uint32_t Z:1;                        /*!< bit:     30  Zero condition code flag */
    uint32_t N:1;                        /*!< bit:     31  Negative condition code flag */
  } b;                                   /*!< Structure used for bit  access */
  uint32_t w;                            /*!< Type      used for word access */
} APSR_Type;
```

Looks familiar?

It certainly looks like some core ARM files for Cortex-M assume that ARM toolchains do provide guarantees on how they
lay out bit-fields!

So how can they be so sure?

The [AAPCS](https://developer.arm.com/docs/ihi0042/latest) has quite a long section on bit-fields. While that section
feels like an unnecessarily dry read, with hardly a single example, it seems that for simple cases, all is well. If,
for instance, all the bit-fields in a structure are declared with the same type, and if they all fit in that type, the
[AAPCS](https://developer.arm.com/docs/ihi0042/latest) gives all the guarantess that we need. In particular:
- A sequence of bit-fields is laid out in the order declared. I.e. for little-endian, the first declared bit will be
the least significant if the memory occupied by a `struct` is interpreted as an integer.
- There will be no padding between the bit-fields.

This means that if our toolchain fulfils the [AAPCS](https://developer.arm.com/docs/ihi0042/latest), the two
`struct`-examples seen so far map the corresponding hardware registers as expected.

But how does ARM know that all toolchains fulfil the [AAPCS](https://developer.arm.com/docs/ihi0042/latest)? While it
is difficult to answer this question in general, let's have a look at two interesting cases:
- [ARM's official compiler documentation](http://infocenter.arm.com/help/index.jsp?topic=/com.arm.doc.dui0491e/Babjddhe.html
) explicitly describes a bit-field layout that fulfils our [AAPCS](https://developer.arm.com/docs/ihi0042/latest
) interpretation.
- [gcc](https://gcc.gnu.org/onlinedocs/gcc/ARM-Options.html) has the option:
    - `-mabi=name`: generate code for the specified ABI. Permissible values are: ‘apcs-gnu’, ‘atpcs’, ‘aapcs’,
      ‘aapcs-linux’ and ‘iwmmxt’.

[The GNU Arm Embedded Toolchain](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm/downloads)
has the following default option:
```shell
$ arm-none-eabi-gcc -Q --help=target
The following options are target specific:
  -mabi=                      		aapcs
[...]
```

This also looks as expected.

In summary, using bit-fields to map Cortex-M ARM registers seems reasonable.

### But how can you really be sure that the bit-fields map the registers correctly?
#### Endianness
While endianness is selectable in silicon for Cortex-M, it would seem that
[core_cm7.h](https://github.com/ARM-software/CMSIS/blob/master/CMSIS/Include/core_cm7.h) (and other CMSIS
Cortex-M header files) assumes a little endian-configuration (according to the
[AAPCS](https://developer.arm.com/docs/ihi0042/latest), the bit-fields are laid out in the order declared, and the
first field in the `struct` above is always assumed to map bits 0 to 15, i.e. the least significant bits). That
implicit assumption is quite confusing, seems a little dangerous, and
[has been reported to ARM as an issue](https://github.com/ARM-software/CMSIS_5/issues/914). The approach taken by `ecg`
is to provide a bit-field runtime checking function in the generated code (unfortunately, that cannot be done at
compile time):
```C++
inline void check_bit_field_mapping()
{
	struct {
		uint32_t flag1: 1;
		uint32_t value1: 4;
		uint32_t flag2: 1;
		uint32_t flag3: 1;
		uint32_t value2: 7;
		uint32_t : 17;
		uint32_t flag4: 1;
	} bit_fields1{
		.flag1 = 1u,
		.value1 = 11u,
		.flag2 = 1u,
		.flag3 = 0,
		.value2 = 53u,
		.flag4 = 0,
	};
	if ((*reinterpret_cast<const uint32_t*>(&bit_fields1) & 0x80003fff) != (1u | (11u << 1u) | (1u << 5u) |
	                                                                        (53u << 7u)))
		for (;;)
			; // bit field mapping problem, halt
	struct {
		uint32_t flag1: 1;
		uint32_t value1: 4;
		uint32_t flag2: 1;
		uint32_t flag3: 1;
		uint32_t : 14;
		uint32_t value2: 3;
		uint32_t : 4;
		uint32_t flag4: 1;
		uint32_t flag5: 1;
		uint32_t flag6: 1;
		uint32_t flag7: 1;
	} bit_fields2{
		.flag1 = 0,
		.value1 = 13u,
		.flag2 = 1u,
		.flag3 = 0,
		.value2 = 5u,
		.flag4 = 1u,
		.flag5 = 1u,
		.flag6 = 0,
		.flag7 = 1u,
	};
	if ((*reinterpret_cast<const uint32_t*>(&bit_fields2) & 0xf0e0007f) != ((13u << 1u) | (1u << 5u) |
	                                                                        (5u << 21u) | (1u << 28u) |
	                                                                        (1u << 29u) | (1u << 31u)))
		for (;;)
			; // bit field mapping problem, halt
}
```
Running this function at least once per combination MCU/toolchain is HIGHLY RECOMMENDED!

#### Alignment
Alignment is in fact checked as a side effect by the runtime checking function above, but the generated code will force
alignment checking at compile time for every single register of every single peripheral. For instance, this is how it
is done for the watchdog peripheral of an arbitrary MCU:
```C++
static_assert(offsetof(WWDG, cr_) == 0x0, "padding error");
static_assert(offsetof(WWDG, cfr_) == 0x4, "padding error");
static_assert(offsetof(WWDG, sr_) == 0x8, "padding error");
```

### So what does that global `struct` look like?
It is straightforward. It lies in the namespace passed to `ecg`, and typically looks
like this:
```C++
inline const Mcu mcu{
	.adc1 = *reinterpret_cast<volatile ADC1*>(0x40012000),
	.adc2 = *reinterpret_cast<volatile ADC2*>(0x40012100),
	.adc3 = *reinterpret_cast<volatile ADC3*>(0x40012200),
	.can1 = *reinterpret_cast<volatile CAN1*>(0x40006400),
	.can2 = *reinterpret_cast<volatile CAN2*>(0x40006800),
	.crc = *reinterpret_cast<volatile CRC*>(0x40023000),
	.cryp = *reinterpret_cast<volatile CRYP*>(0x50060000),
	.c_adc = *reinterpret_cast<volatile C_ADC*>(0x40012300),
	.dac = *reinterpret_cast<volatile DAC*>(0x40007400),
	.dbg = *reinterpret_cast<volatile DBG*>(0xE0042000),
	.dcmi = *reinterpret_cast<volatile DCMI*>(0x50050000),
	.dma1 = *reinterpret_cast<volatile DMA1*>(0x40026000),
	.dma2 = *reinterpret_cast<volatile DMA2*>(0x40026400),
	.exti = *reinterpret_cast<volatile EXTI*>(0x40013C00),
	.ethernet_dma = *reinterpret_cast<volatile Ethernet_DMA*>(0x40029000),
	.ethernet_mac = *reinterpret_cast<volatile Ethernet_MAC*>(0x40028000),
	.ethernet_mmc = *reinterpret_cast<volatile Ethernet_MMC*>(0x40028100),
	.ethernet_ptp = *reinterpret_cast<volatile Ethernet_PTP*>(0x40028700),
	.flash = *reinterpret_cast<volatile FLASH*>(0x40023C00),
	.fpu = *reinterpret_cast<volatile FPU*>(0xE000EF34),
	.fpu_cpacr = *reinterpret_cast<volatile FPU_CPACR*>(0xE000ED88),
	.fsmc = *reinterpret_cast<volatile FSMC*>(0xA0000000),
	.gpioa = *reinterpret_cast<volatile GPIOA*>(0x40020000),
	.gpiob = *reinterpret_cast<volatile GPIOB*>(0x40020400),
	.gpioc = *reinterpret_cast<volatile GPIOC*>(0x40020800),
// ...
};
```

This is C++, so we use references instead of pointers for the peripheral members. Also, the `mcu` variable is inline,
which is a new feature in C++17, and allows the header file to be included in multiple compilation units without
creating conflicting definitions of the variable (only one copy is created for the whole program).

For convenience, the peripherals are sorted in alphabetic order.

In a debugger session, the `mcu` variable can be used in the following way:

```gdb
(gdb) set print pretty on
(gdb) p/x mcu_support::mcu.scb
$4 = (volatile mcu_support::SCB &) @0xe000ed00: {
  cpuid_ = {
    Revision = 0x1, 
    PartNo = 0xc27, 
    Constant = 0xf, 
    Variant = 0x0, 
    Implementer = 0x41
  }, 
  icsr_ = {
    VECTACTIVE = 0x0, 
    RETTOBASE = 0x0, 
    VECTPENDING = 0x0, 
    ISRPENDING = 0x0, 
    PENDSTCLR = 0x0, 
    PENDSTSET = 0x0, 
    PENDSVCLR = 0x0, 
    PENDSVSET = 0x0, 
    NMIPENDSET = 0x0
  }, 
  vtor_ = {
    TBLOFF = 0x1000
  }, 
  aircr_ = {
    VECTRESET = 0x0, 
    VECTCLRACTIVE = 0x0, 
    SYSRESETREQ = 0x0, 
    PRIGROUP = 0x0, 
    ENDIANESS = 0x0, 
    VECTKEYSTAT = 0xfa05
  }, 
  scr_ = {
    SLEEPONEXIT = 0x0, 
    SLEEPDEEP = 0x0, 
    SEVEONPEND = 0x0
  }, 
  ccr_ = {
    NONBASETHRDENA = 0x0, 
    USERSETMPEND = 0x0, 
    UNALIGN__TRP = 0x0, 
    DIV_0_TRP = 0x0, 
    BFHFNMIGN = 0x0, 
    STKALIGN = 0x1, 
    DC = 0x0, 
    IC = 0x0, 
    BP = 0x1
  }, 
  shpr1_ = {
    PRI_4 = 0x0, 
    PRI_5 = 0x0, 
    PRI_6 = 0x0
  }, 
  shpr2_ = {
    PRI_11 = 0x0
  }, 
  shpr3_ = {
    PRI_14 = 0x0, 
    PRI_15 = 0x0
  }, 
  shcrs_ = {
    MEMFAULTACT = 0x0, 
    BUSFAULTACT = 0x0, 
    USGFAULTACT = 0x0, 
    SVCALLACT = 0x0, 
    MONITORACT = 0x0, 
    PENDSVACT = 0x0, 
    SYSTICKACT = 0x0, 
    USGFAULTPENDED = 0x0, 
    MEMFAULTPENDED = 0x0, 
    BUSFAULTPENDED = 0x0, 
    SVCALLPENDED = 0x0, 
    MEMFAULTENA = 0x0, 
    BUSFAULTENA = 0x0, 
    USGFAULTENA = 0x0
  }, 
  cfsr_ufsr_bfsr_mmfsr_ = {
    IACCVIOL = 0x0, 
    DACCVIOL = 0x0, 
    MUNSTKERR = 0x0, 
    MSTKERR = 0x0, 
    MLSPERR = 0x0, 
    MMARVALID = 0x0, 
    IBUSERR = 0x0, 
    PRECISERR = 0x0, 
    IMPRECISERR = 0x0, 
    UNSTKERR = 0x0, 
    STKERR = 0x0, 
    LSPERR = 0x0, 
    BFARVALID = 0x0, 
    UNDEFINSTR = 0x0, 
    INVSTATE = 0x0, 
    INVPC = 0x0, 
    NOCP = 0x0, 
    UNALIGNED = 0x0, 
    DIVBYZERO = 0x0
  }, 
  hfsr_ = {
    VECTTBL = 0x0, 
    FORCED = 0x0, 
    DEBUG_VT = 0x0
  }, 
  padding_0 = {0xb, 0x0, 0x0, 0x0}, 
  mmfar_ = {
    ADDRESS = 0x0
  }, 
  bfar_ = {
    ADDRESS = 0x0
  }, 
  padding_1 = {0x0, 0x0, 0x0, 0x0, 0x30}
}
```

One of the fields tells us that this is an ARM Cortex-M7. Can you find which one?

Use your favorite `gdb`-IDE integration for a seamless read/write access to all your MCU peripheral registers.

Enjoy!
# License
`ecg` is licensed under the [GNU General Public License v3.0](LICENSE), but this does not apply to the generated files.
No particular license applies to the generated files from `ecg`'s perspective, but since the generated files by design
reproduce large parts of the source SVD files, you should check the license agreement of your source SVD files. When
it comes to the SVD files included in this repository, they are distributed without a license by their original provider
and seem to be reproduced elsewhere without particular precaution. Please contact me if you think I am committing any
breach of a license agreement.

# Branch `dev` in this repository
I use the branch `dev` in this repository as my private backyard. Please do not make any assumption about that branch.
In particular, it may get rebased at any time.

On the other hand, I intend to keep the `master` branch in a working state, and I will not rebase it.
