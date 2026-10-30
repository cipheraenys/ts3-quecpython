/*
 * EC600MEU_LA (ASR1606) customer_app, execute-in-place.
 * Section layout of the EC600M QuecOpen app_linkscript.ld; addresses from the stock EC600M
 * QuecPython firmware:
 *   ROM = customer_app partition, mapped at 0x80534000, 0x140000 bytes (partition.bin).
 *         The first 8 bytes hold the "QUECTEL\0" tag, so code starts at +8.
 *   RAM = starts at 0x7E320000, where the stock app's .data starts (its customer_app.bin
 *         header). The stock app references RAM up to 0x7E42D2B4; 1 MB stays inside that.
 */
__ROM_START_ADDR = 0x80534000;
__MAX_ROM_SIZE   = 0x140000;

__RAM_START_ADDR = 0x7E320000;
__MAX_RAM_SIZE   = 0x100000;
__heap_limit     = __RAM_START_ADDR + __MAX_RAM_SIZE;   /* newlib _sbrk stops here (shim) */

MEMORY
{
	ROM (rx)   : ORIGIN = __ROM_START_ADDR + 8, LENGTH = __MAX_ROM_SIZE - 8
	SRAM (rwx) : ORIGIN = __RAM_START_ADDR, LENGTH = __MAX_RAM_SIZE
}

SECTIONS
{
	. = __ROM_START_ADDR + 8;
	.initdata : ALIGN(4)
	{
		KEEP(*(.initdata))
	}>ROM
	.userStartUp : ALIGN(4)
	{
		KEEP(*(.userInit))
	}>ROM
	.text : ALIGN(4)
	{
		*(.text)
		*(.text*)
	}>ROM
	.rodata : ALIGN(4)
	{
		*(.rodata)
		*(.rodata*)
	}>ROM

	. = __RAM_START_ADDR;
	.data : ALIGN(4)
	{
		PROVIDE_HIDDEN (__data_load = LOADADDR(.data));
		PROVIDE_HIDDEN (__data_start = .);
		*(.data)
		*(.data*)
		PROVIDE_HIDDEN (_edata = .);
	}>SRAM AT>ROM
	.userBootTable : ALIGN(4)
	{
		PROVIDE_HIDDEN (__userBoot_start__ = .);
		KEEP(*(.userBootTable))
		PROVIDE_HIDDEN (__userBoot_end__ = .);
	}>SRAM AT>ROM
	.userKernelTable : ALIGN(4)
	{
		PROVIDE_HIDDEN (__userKernel_start__ = .);
		KEEP(*(.userKernelTable))
		PROVIDE_HIDDEN (__userKernel_end__ = .);
	}>SRAM AT>ROM
	.appRegTable : ALIGN(4)
	{
		PROVIDE_HIDDEN (__appRegTable_start__ = .);
		KEEP(*(.appRegTable))
		PROVIDE_HIDDEN (__appRegTable_end__ = .);
	}>SRAM AT>ROM
	.ARM.exidx : ALIGN(4)
	{
		PROVIDE_HIDDEN (__exidx_start = .);
		*(.ARM.exidx);
		PROVIDE_HIDDEN (__exidx_end = .);
	}>SRAM AT>ROM

	_bin_end = LOADADDR(.ARM.exidx) + SIZEOF(.ARM.exidx);
	ASSERT(_bin_end - __ROM_START_ADDR <= __MAX_ROM_SIZE, "EC600M customer_app ROM overflow")

	.bss : ALIGN(4)
	{
		PROVIDE_HIDDEN (__bss_start__ = .);
		*(.bss)
		*(.bss*)
		*(COMMON)
		PROVIDE_HIDDEN (__bss_end__ = .);
	}>SRAM
	end = .;

	ASSERT(__bss_end__ - __RAM_START_ADDR <= __MAX_RAM_SIZE, "EC600M customer_app RAM overflow")
}
