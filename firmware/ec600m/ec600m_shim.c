/*
 * ec600m_shim.c - run the EC600N-built libHeliosAPI.a on the EC600M (ASR1606) kernel.
 *
 * Every ql_* call in the app goes through a stub that asks the kernel for the function by
 * name (m_get_api_ptr, installed by ql_main.o at boot). libHeliosAPI.a was linked against the
 * EC600N ql_common_api; some of the names it uses have no stub in the EC600M ql_common_api.
 * This file supplies them:
 *   - FWD()/FWD_AS(): by-name forwarders, same lookup and -1-on-miss as the Quectel stubs.
 *   - Bridges for calls whose EC600M counterpart has another name or layout: per-task storage,
 *     UART config, LCD write and init, NOR flash access.
 *   - _sbrk bounded to the app RAM region (newlib heap).
 *   - The boot-time API self-test: records the kernel names this image uses that the kernel
 *     does not export (see ec600m_api_report).
 */
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h> /* malloc/free link to the ql_common_api stubs: kernel heap */
#include <string.h>

extern void *(*m_get_api_ptr)(const char *name);

/* ---------------------------------------------------------------- by-name forwarders */

/* `sym` is the symbol libHeliosAPI calls, `kname` the kernel export it resolves to. The first
 * call looks kname up and caches the result (-1 when absent); every call then tail-calls it with
 * the caller's r0-r3 and stack arguments untouched, or returns -1. */
#define FWD_AS(sym, kname)                                                     \
    __asm__(".syntax unified\n"                                                \
            ".section .text." #sym ",\"ax\",%progbits\n"                        \
            ".global " #sym "\n"                                               \
            ".type " #sym ", %function\n"                                      \
            ".thumb\n.thumb_func\n"                                            \
            #sym ":\n"                                                         \
            "  push  {r0, r1, r2, r3, r4, lr}\n"                               \
            "  ldr   r4, =fwd_cache_" #sym "\n"                                \
            "  ldr   r0, [r4]\n"                                               \
            "  cbnz  r0, 1f\n"                                                 \
            "  ldr   r0, =fwd_name_" #sym "\n"                                 \
            "  ldr   r1, =m_get_api_ptr\n"                                     \
            "  ldr   r1, [r1]\n"                                               \
            "  blx   r1\n"                                                     \
            "  cmp   r0, #0\n"                                                 \
            "  it    eq\n"                                                     \
            "  mvneq r0, #0\n"                                                 \
            "  str   r0, [r4]\n"                                               \
            "1:\n"                                                             \
            "  mov   ip, r0\n"                                                 \
            "  pop   {r0, r1, r2, r3, r4, lr}\n"                               \
            "  cmn   ip, #1\n"                                                 \
            "  beq   2f\n"                                                     \
            "  bx    ip\n"                                                     \
            "2:\n"                                                             \
            "  mvn   r0, #0\n"                                                 \
            "  bx    lr\n"                                                     \
            ".ltorg\n"                                                         \
            ".size " #sym ", .-" #sym "\n"                                     \
            ".section .bss.fwd_cache_" #sym ",\"aw\",%nobits\n"                \
            ".align 2\n"                                                       \
            "fwd_cache_" #sym ": .space 4\n"                                   \
            ".section .rodata.fwd_name_" #sym ",\"a\",%progbits\n"             \
            "fwd_name_" #sym ": .asciz \"" #kname "\"\n"                       \
            ".text\n");
#define FWD(name) FWD_AS(name, name)

FWD(_ql_fprintf)
FWD(_ql_fscanf)
FWD(printf)
FWD(vprintf)
FWD(ql_amr_stream_close)
FWD(ql_amr_stream_open)
FWD(ql_amr_stream_write)
FWD(ql_amrenc_dtx_enable)
FWD(ql_aud_record_file_start)
FWD(ql_aud_record_stop)
FWD(ql_aud_record_stream_start)
FWD(ql_bind_loudspkpa_cb)
FWD(ql_camera_caputre_start)
FWD(ql_camera_scandecode_pause)
FWD(ql_camera_scandecode_resume)
FWD(ql_camera_scandecode_start)
FWD(ql_camera_scandecode_stop)
FWD(ql_cell_locator_init)
FWD(ql_cell_locator_perform)
FWD(ql_cell_locator_release)
FWD(ql_cell_locator_set_cid)
FWD(ql_cell_locator_set_server)
FWD(ql_cell_locator_set_timeout)
FWD(ql_cell_locator_set_token)
FWD(ql_datacall_get_apn)
FWD(ql_dev_get_qpy_version)
FWD(ql_dev_get_usb_product)
FWD(ql_fota_firmware_download)
FWD(ql_get_current_profileID)
FWD(ql_get_sms_save_location)
FWD(ql_get_wifiscan_config_info)
FWD(ql_i2c_read_dalay)
FWD(ql_keypad_bl_level_ctrl)
FWD(ql_keypad_bl_switch)
FWD(ql_keypad_release)
FWD(ql_lcd_para_set)
FWD(ql_lcd_set_brightness)
FWD(ql_lpm_ex_set)
FWD(ql_machine_wdt_feed)
FWD(ql_machine_wdt_init)
FWD(ql_machine_wdt_stop)
FWD(ql_nw_get_apn)
FWD(ql_nw_set_apn)
FWD(ql_play_mp3_stream_start)
FWD(ql_play_mp3_stream_stop)
FWD(ql_pwm_config_ex)
FWD(ql_pwm_config_plus)
FWD(ql_pwrkey_unregister_irq)
FWD(ql_record_amr_file_start)
FWD(ql_record_amr_file_stop)
FWD(ql_record_amr_stream_start)
FWD(ql_record_amr_stream_stop)
FWD(ql_rtos_disable_interrupts)
FWD(ql_rtos_restore_interrupts)
FWD(ql_rtos_task_get_stack_ptr)
FWD(ql_set_camera_model)
FWD(ql_set_codec_gain_table)
FWD(ql_set_led_net_sta_pin_to_gpio)
FWD(ql_set_wifiscan_config_info)
FWD(ql_sim_add_event_handler)
FWD(ql_sim_get_simdet)
FWD(ql_sim_set_simdet)
FWD(ql_spi_write_read_4byte)
FWD(ql_start_wifiscan)
FWD(ql_tzget)
FWD(ql_tzset)
FWD(ql_uart_register_tx_cb)
FWD(ql_usbdect_unregister_cb)
FWD(ql_voicecall_set_auto_record)
FWD(ql_voicecall_start_record)
FWD(ql_voicecall_start_record_stream)
FWD(ql_voicecall_stop_record)
FWD(ql_wifiscan_add_event_handler)
FWD(ql_wifiscan_decode_buffer)

/* Per-task storage (MicroPython thread state). The stock EC600M QuecPython calls these kernel
 * functions from Helios_Thread_Get/SetSpecific with the same (task, value) arguments. */
FWD_AS(ql_rtos_task_get_specific, ql_rtos_task_get_context)
FWD_AS(ql_rtos_task_set_specific, ql_rtos_task_set_context)

/* Same arguments, EC600M kernel names (as called by the stock Helios_UART_Any and
 * Helios_USB_GetStatus). The REPL polls both. */
FWD_AS(ql_uart_get_rx_data_len, ql_uart_get_rxrb_data_len)
FWD_AS(ql_usb_get_connect_state, ql_usb_connect_state)

/* ---------------------------------------------------------------- UART */

/* Helios_UART_Init calls this (renamed by mkboard). The USB REPL port (ql_uart port 4) rejects
 * line settings with -4; the stock EC600M Helios_UART_Init ignores the result, the EC600N one
 * fails the init and MicroPython never starts the REPL. */
extern int ql_uart_set_dcbconfig(int port, void *dcb);

int ec600m_uart_set_dcbconfig(int port, void *dcb)
{
    (void)ql_uart_set_dcbconfig(port, dcb);
    return 0;
}

/* Receive callback. The EC600N Helios_UART_Init stores the callback at [ql port] and its kernel
 * callback accepts ql ports 0..3 only, so input on the REPL (Helios UART3 = ql port 4) is
 * dropped. mkboard renames the library's Helios_UART_Init to ec600n_Helios_UART_Init; this one
 * keeps the callback by Helios port and maps the ql port back like the stock EC600M build. */
typedef void (*helios_uart_cb_t)(uint64_t ind_type, int port, uint64_t size);
typedef struct {
    void *config;
    helios_uart_cb_t cb;
} helios_uart_init_t;

extern int ec600n_Helios_UART_Init(int port, helios_uart_init_t *init);
extern int ql_uart_register_cb(int port, void (*cb)(unsigned int port, void *para));

static const uint8_t helios_to_ql[] = {0, 1, 2, 4}; /* = helios_uart_map after patch_maps */
static helios_uart_cb_t uart_cb[sizeof helios_to_ql];

static void ec600m_uart_cb(unsigned int ql_port, void *para)
{
    for (unsigned h = 0; h < sizeof helios_to_ql; h++) {
        if (helios_to_ql[h] == ql_port && uart_cb[h]) {
            uint64_t size;
            memcpy(&size, para, sizeof size);
            uart_cb[h](0, (int)h, size);
            return;
        }
    }
}

int Helios_UART_Init(int port, helios_uart_init_t *init)
{
    helios_uart_init_t no_cb = {init->config, 0};
    int r = ec600n_Helios_UART_Init(port, &no_cb); /* validates port 0..3 */
    if (r || !init->cb)
        return r;
    uart_cb[port] = init->cb;
    ql_uart_register_cb(helios_to_ql[port], ec600m_uart_cb);
    return 0;
}

/* ---------------------------------------------------------------- LCD write */

/* libHeliosAPI calls ql_lcd_write(buf, sx, sy, ex, ey); the EC600M ql_common_api names it
 * ql_lcd_write_sync. */
extern int ql_lcd_write_sync(unsigned char *buf, unsigned short sx, unsigned short sy,
                             unsigned short ex, unsigned short ey);

int ql_lcd_write(unsigned char *buf, unsigned short sx, unsigned short sy,
                 unsigned short ex, unsigned short ey)
{
    return ql_lcd_write_sync(buf, sx, sy, ex, ey);
}

/* ---------------------------------------------------------------- LCD init */

/*
 * libHeliosAPI.a builds the EC600N ql_lcd_data_t (36 bytes, 6-byte init entries, SPI clock in
 * kHz). The EC600M kernel takes a 48-byte struct with 3-byte init entries and clock enums.
 * mkboard renames libHeliosAPI's ql_lcd_init reference to ec600n_ql_lcd_init (below), which
 * converts and calls the real one. Both layouts are pinned by the asserts. Fields the EC600N
 * struct lacks take the stock EC600M QuecPython defaults (rclk 6.5 MHz, cmd bytes 0, polling);
 * wclk is converted from spi_clk_khz and falls back to 13 MHz.
 */
struct ec600n_lcd_entry {
    uint8_t type;
    uint16_t value; /* a DATA entry with len 2 carries two bytes: hi << 8 | lo */
    uint8_t len;
};
struct ec600n_lcd_data {
    struct ec600n_lcd_entry *init_para;
    uint32_t init_para_len;
    uint16_t width, height;
    uint32_t te_signal;
    uint32_t spi_clk_khz;
    uint32_t lcd_id;
    uint16_t format, type, sample_edge, endian, line_num, data_line;
};
_Static_assert(sizeof(struct ec600n_lcd_entry) == 6, "EC600N init entry is 6 bytes");
_Static_assert(offsetof(struct ec600n_lcd_entry, value) == 2, "EC600N entry value at +2");
_Static_assert(offsetof(struct ec600n_lcd_entry, len) == 4, "EC600N entry len at +4");
_Static_assert(sizeof(struct ec600n_lcd_data) == 36, "EC600N ql_lcd_data_t is 36 bytes");
_Static_assert(offsetof(struct ec600n_lcd_data, spi_clk_khz) == 16, "EC600N clk at +16");
_Static_assert(offsetof(struct ec600n_lcd_data, type) == 26, "EC600N type at +26");
_Static_assert(offsetof(struct ec600n_lcd_data, line_num) == 32, "EC600N line_num at +32");

struct ec600m_lcd_entry {
    uint8_t type, value, len;
};
struct ec600m_lcd_data {
    struct ec600m_lcd_entry *init_para;
    uint32_t init_para_len;
    uint16_t width, height;
    uint8_t cmd_col_set, cmd_row_set, cmd_mem_wr;
    uint32_t te_signal;
    uint32_t spi_wclk, spi_rclk; /* QL_SPI_LCD_CLK_E */
    uint32_t lcd_id;
    uint16_t format, type, sample_edge, endian, line_num, data_line;
    uint8_t work_mode;
};
_Static_assert(sizeof(struct ec600m_lcd_entry) == 3, "EC600M init entry is 3 bytes");
_Static_assert(sizeof(struct ec600m_lcd_data) == 48, "EC600M ql_lcd_data_t is 48 bytes");
_Static_assert(offsetof(struct ec600m_lcd_data, te_signal) == 16, "EC600M te at +16");
_Static_assert(offsetof(struct ec600m_lcd_data, spi_wclk) == 20, "EC600M wclk at +20");
_Static_assert(offsetof(struct ec600m_lcd_data, format) == 32, "EC600M format at +32");
_Static_assert(offsetof(struct ec600m_lcd_data, line_num) == 40, "EC600M line_num at +40");
_Static_assert(offsetof(struct ec600m_lcd_data, work_mode) == 44, "EC600M work_mode at +44");

#define LCD_DATA 1 /* SPI_WRITE_DATA */

extern int ql_lcd_init(struct ec600m_lcd_data *data);

static struct ec600m_lcd_entry *lcd_cmds; /* kept for the kernel; replaced on re-init */
static struct ec600m_lcd_data lcd_cfg;

static uint32_t lcd_clk_enum(uint32_t khz)
{
    static const struct { uint32_t khz; uint8_t e; } map[] = {
        {6500, 0}, {13000, 1}, {26000, 2}, {52000, 3}, {3250, 4}, {1625, 5},
        {812, 6}, {813, 6}, /* 812.5 kHz, either rounding */
    };
    for (unsigned i = 0; i < sizeof map / sizeof map[0]; i++)
        if (map[i].khz == khz)
            return map[i].e;
    return 1; /* 13 MHz, the stock default */
}

int ec600n_ql_lcd_init(const struct ec600n_lcd_data *n)
{
    uint32_t count = 0;
    for (uint32_t i = 0; i < n->init_para_len; i++)
        count += (n->init_para[i].type == LCD_DATA && n->init_para[i].len == 2) ? 2 : 1;

    struct ec600m_lcd_entry *cmds = NULL;
    if (count) {
        cmds = malloc(count * sizeof *cmds);
        if (!cmds)
            return -1;
        uint32_t o = 0;
        for (uint32_t i = 0; i < n->init_para_len; i++) {
            const struct ec600n_lcd_entry *e = &n->init_para[i];
            if (e->type == LCD_DATA && e->len == 2) { /* 16-bit data: high byte first */
                cmds[o++] = (struct ec600m_lcd_entry){LCD_DATA, (uint8_t)(e->value >> 8), 1};
                cmds[o++] = (struct ec600m_lcd_entry){LCD_DATA, (uint8_t)e->value, 1};
            } else {
                cmds[o++] = (struct ec600m_lcd_entry){e->type, (uint8_t)e->value, e->len};
            }
        }
    }
    free(lcd_cmds);
    lcd_cmds = cmds;

    memset(&lcd_cfg, 0, sizeof lcd_cfg);
    lcd_cfg.init_para = cmds;
    lcd_cfg.init_para_len = count;
    lcd_cfg.width = n->width;
    lcd_cfg.height = n->height;
    lcd_cfg.te_signal = n->te_signal;
    lcd_cfg.spi_wclk = lcd_clk_enum(n->spi_clk_khz);
    lcd_cfg.spi_rclk = 0; /* 6.5 MHz */
    lcd_cfg.lcd_id = n->lcd_id;
    lcd_cfg.format = n->format;
    lcd_cfg.type = n->type;
    lcd_cfg.sample_edge = n->sample_edge;
    lcd_cfg.endian = n->endian;
    lcd_cfg.line_num = n->line_num;
    lcd_cfg.data_line = n->data_line;
    lcd_cfg.work_mode = 0; /* polling */
    return ql_lcd_init(&lcd_cfg);
}

/* ---------------------------------------------------------------- NOR flash */

/*
 * Helios_Flash_* passes absolute flash addresses; the EC600M API wants the partition name plus
 * that same absolute address (see the EC600M QuecOpen example_flashspeed.c). A partition is
 * registered when Helios_Flash_GetPartiCtx() asks for it, before any read/write/erase.
 */
extern void ql_norflash_get_addr(unsigned char *name, unsigned int *start, unsigned int *size);
extern unsigned int ql_norflash_do_read(unsigned char *name, unsigned int addr, unsigned int buf,
                                        unsigned int size);
extern unsigned int ql_norflash_do_write(unsigned char *name, unsigned int addr, unsigned int buf,
                                         unsigned int size);
extern int ql_norflash_do_erase(unsigned char *name, unsigned int addr, unsigned int size);

/* Helios_Flash_GetPartiCtx reads start/size at +0x30/+0x34 of the entry and never checks NULL. */
struct pentry_compat {
    uint8_t reserved[0x30];
    uint32_t start;
    uint32_t size;
    char name[32];
};
_Static_assert(offsetof(struct pentry_compat, start) == 0x30, "start offset");
_Static_assert(offsetof(struct pentry_compat, size) == 0x34, "size offset");

#define MAX_PARTS 8
static struct pentry_compat parts[MAX_PARTS];
static struct pentry_compat no_part; /* size 0: every access through it fails */
static int nparts;

void *ql_qspi_nor_find_pentry(const char *name)
{
    for (int i = 0; i < nparts; i++)
        if (strcmp(parts[i].name, name) == 0)
            return &parts[i];
    if (nparts == MAX_PARTS)
        return &no_part;
    unsigned int start = 0, size = 0;
    ql_norflash_get_addr((unsigned char *)name, &start, &size);
    if (size == 0)
        return &no_part;
    struct pentry_compat *p = &parts[nparts++];
    strncpy(p->name, name, sizeof p->name - 1);
    p->start = start;
    p->size = size;
    return p;
}

static unsigned char *part_of(uint32_t addr, uint32_t len)
{
    for (int i = 0; i < nparts; i++)
        if (addr >= parts[i].start && len <= parts[i].size &&
            addr - parts[i].start <= parts[i].size - len)
            return (unsigned char *)parts[i].name;
    return NULL;
}

int ql_qspi_nor_do_read(uint32_t addr, void *buf, size_t size)
{
    unsigned char *name = part_of(addr, size);
    return name ? (int)ql_norflash_do_read(name, addr, (unsigned int)buf, size) : -1;
}

int ql_qspi_nor_do_write(uint32_t addr, const void *buf, size_t size)
{
    unsigned char *name = part_of(addr, size);
    return name ? (int)ql_norflash_do_write(name, addr, (unsigned int)buf, size) : -1;
}

int ql_qspi_nor_do_erase_4k(uint32_t addr, size_t size)
{
    unsigned char *name = part_of(addr, size);
    return name ? ql_norflash_do_erase(name, addr, size) : -1;
}

/* ---------------------------------------------------------------- newlib heap */

/* newlib's allocator (pulled in by float formatting) grows from `end`. Stop it at the end of the
 * app RAM region instead of letting it run into kernel memory. */
extern char end;
extern char __heap_limit;

void *_sbrk(ptrdiff_t incr)
{
    static char *brk = &end;
    if (incr > 0 && (size_t)(&__heap_limit - brk) < (size_t)incr)
        return (void *)-1;
    char *old = brk;
    brk += incr;
    return old;
}

/* ---------------------------------------------------------------- boot-time API self-test */

/*
 * Looks up every kernel name this image may call (ec600m_api_names.h, generated by mkboard) and
 * writes "<missing names> | checked N missing M" to ec600m_api_report. From the REPL:
 *   import uctypes; print(bytes(uctypes.bytearray_at(ADDR, 2048)).split(b'\0')[0].decode())
 * with ADDR = address of ec600m_api_report in the build's .map.
 */
#include "ec600m_api_names.h" /* static const char *const ec600m_api_names[] = {..., 0}; */

char ec600m_api_report[2048];

extern void Helios_Thread_Exit(void);

static char *put_u(char *p, unsigned x) /* no snprintf: keep newlib stdio out of this path */
{
    char t[10];
    int n = 0;
    do t[n++] = (char)('0' + x % 10); while (x /= 10);
    while (n)
        *p++ = t[--n];
    return p;
}

static void ec600m_api_selftest(void *arg)
{
    (void)arg;
    unsigned checked = 0, missing = 0;
    char *p = ec600m_api_report;
    char *const names_end = ec600m_api_report + sizeof ec600m_api_report - 48; /* tail room */
    for (const char *const *n = ec600m_api_names; *n; n++, checked++) {
        if (m_get_api_ptr(*n))
            continue;
        missing++;
        size_t len = strlen(*n);
        if (p + len + 1 < names_end) {
            memcpy(p, *n, len);
            p += len;
            *p++ = ' ';
        }
    }
    memcpy(p, "| checked ", 10);
    p = put_u(p + 10, checked);
    memcpy(p, " missing ", 9);
    p = put_u(p + 9, missing);
    *p = 0;
    Helios_Thread_Exit();
}

typedef struct {
    void (*entry)(void *);
    const char *name;
    unsigned int stack_size;
    unsigned int prio;
} app_reg_t;

/* Same table and layout as Helios' application_init(); the kernel starts it at boot. */
app_reg_t ec600m_api_selftest_reg __attribute__((used, section(".appRegTable"))) = {
    ec600m_api_selftest, "ec600m_api_selftest", 4 * 1024, 0};
