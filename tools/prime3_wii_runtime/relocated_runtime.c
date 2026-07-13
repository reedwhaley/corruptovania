#define __attribute_used__ __attribute__((used))
#define __attribute_aligned_4__ __attribute__((aligned(4)))
#define __attribute_aligned_32__ __attribute__((aligned(32)))
#define __attribute_section_code__ __attribute__((section(".text.runtime.core")))
#define __attribute_section_code_keep__ __attribute__((section(".text.runtime.keep")))
#define __attribute_section_rodata__ __attribute__((section(".rodata.runtime")))
#define __attribute_section_state__ __attribute__((section(".runtime_state")))
#define __attribute_section_state_aligned_32__ __attribute__((section(".runtime_state"), aligned(32)))

#ifndef PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
#define PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC 0
#endif

#ifndef PRIME3_ENABLE_RECURRING_HOOK_DIAGNOSTICS
#define PRIME3_ENABLE_RECURRING_HOOK_DIAGNOSTICS 0
#endif

#ifndef PRIME3_IOS_UDP_DIAGNOSTIC_MODE
#define PRIME3_IOS_UDP_DIAGNOSTIC_MODE 0
#endif

typedef signed int s32;
typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;

typedef struct runtime_ioctlv {
    void* data;
    u32 len;
} runtime_ioctlv;

typedef struct runtime_bind_params {
    u32 socket;
    u32 has_name;
    u8 name[28];
} runtime_bind_params;

typedef struct runtime_sendto_params {
    u32 socket;
    u32 flags;
    u32 has_destaddr;
    u8 destaddr[28];
} runtime_sendto_params;

enum {
    RUNTIME_TRANSPORT_PHASE_UNINITIALIZED = 0,
    RUNTIME_TRANSPORT_PHASE_OPEN_KD = 1,
    RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_KD = 2,
    RUNTIME_TRANSPORT_PHASE_NWC24_STARTUP = 3,
    RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP = 4,
    RUNTIME_TRANSPORT_PHASE_CLOSE_KD = 5,
    RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_KD = 6,
    RUNTIME_TRANSPORT_PHASE_OPEN_IP = 7,
    RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_IP = 8,
    RUNTIME_TRANSPORT_PHASE_SO_STARTUP = 9,
    RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP = 10,
    RUNTIME_TRANSPORT_PHASE_GETHOSTID = 11,
    RUNTIME_TRANSPORT_PHASE_WAIT_GETHOSTID = 12,
    RUNTIME_TRANSPORT_PHASE_SOCKET = 13,
    RUNTIME_TRANSPORT_PHASE_WAIT_SOCKET = 14,
    RUNTIME_TRANSPORT_PHASE_FCNTL_GET = 15,
    RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_GET = 16,
    RUNTIME_TRANSPORT_PHASE_FCNTL_SET = 17,
    RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_SET = 18,
    RUNTIME_TRANSPORT_PHASE_BIND = 19,
    RUNTIME_TRANSPORT_PHASE_WAIT_BIND = 20,
    RUNTIME_TRANSPORT_PHASE_READY = 21,
    RUNTIME_TRANSPORT_PHASE_RECV = 22,
    RUNTIME_TRANSPORT_PHASE_WAIT_RECV = 23,
    RUNTIME_TRANSPORT_PHASE_SEND = 24,
    RUNTIME_TRANSPORT_PHASE_WAIT_SEND = 25,
    RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE = 0xFE,
    RUNTIME_TRANSPORT_PHASE_ERROR = 0xFF,
};

enum {
    RUNTIME_TRANSPORT_POLL_ACTION_IDLE = 0,
    RUNTIME_TRANSPORT_POLL_ACTION_INIT = 1,
    RUNTIME_TRANSPORT_POLL_ACTION_WAIT = 2,
    RUNTIME_TRANSPORT_POLL_ACTION_RECV = 3,
    RUNTIME_TRANSPORT_POLL_ACTION_SEND = 4,
    RUNTIME_TRANSPORT_POLL_ACTION_RETRY = 5,
    RUNTIME_TRANSPORT_POLL_ACTION_ERROR = 6,
};

enum {
    RUNTIME_TRANSPORT_OP_NONE = 0,
    RUNTIME_TRANSPORT_OP_OPEN = 1,
    RUNTIME_TRANSPORT_OP_CLOSE = 2,
    RUNTIME_TRANSPORT_OP_IOCTL = 3,
    RUNTIME_TRANSPORT_OP_IOCTLV = 4,
};

enum {
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_NORMAL = 0,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_DRY_RUN = 1,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_OPEN_KD_ONCE = 2,
};

enum {
    RUNTIME_DIAGNOSTIC_MARKER_HOOK_WRAPPER_ENTERED = 0xC0DE0001,
    RUNTIME_DIAGNOSTIC_MARKER_POLL_ENTRY = 0xC0DE0002,
    RUNTIME_DIAGNOSTIC_MARKER_STATE_MACHINE_ENTRY = 0xC0DE0003,
    RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL = 0xC0DE0004,
    RUNTIME_DIAGNOSTIC_MARKER_RETAIL_VENEER_ENTERED = 0xC0DE0005,
    RUNTIME_DIAGNOSTIC_MARKER_RETAIL_BEFORE_BCTRL = 0xC0DE0006,
    RUNTIME_DIAGNOSTIC_MARKER_RETAIL_TARGET_RETURNED = 0xC0DE0007,
    RUNTIME_DIAGNOSTIC_MARKER_RETAIL_BEFORE_LR_RESTORE = 0xC0DE0008,
    RUNTIME_DIAGNOSTIC_MARKER_RETAIL_BEFORE_VENEER_BLR = 0xC0DE0009,
    RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL = 0xC0DE000A,
    RUNTIME_DIAGNOSTIC_MARKER_POLL_RETURNING = 0xC0DE000B,
    RUNTIME_DIAGNOSTIC_MARKER_WRAPPER_RESTORING = 0xC0DE000C,
    RUNTIME_DIAGNOSTIC_MARKER_WRAPPER_RETURNING = 0xC0DE000D,
};

enum {
    IOCTL_NWC24_STARTUP = 6,
    IOCTL_SO_BIND = 2,
    IOCTL_SO_CLOSE = 3,
    IOCTL_SO_FCNTL = 5,
    IOCTLV_SO_RECVFROM = 12,
    IOCTLV_SO_SENDTO = 13,
    IOCTL_SO_SOCKET = 15,
    IOCTL_SO_GETHOSTID = 16,
    IOCTL_SO_STARTUP = 31,
    IOS_O_NONBLOCK = 0x04,
    F_GETFL = 3,
    F_SETFL = 4,
    AF_INET = 2,
    SOCK_DGRAM = 2,
    IPPROTO_IP = 0,
    INADDR_ANY = 0,
    MSG_DONTWAIT = 0x40,
    RUNTIME_UDP_PORT = 43674,
    RUNTIME_PREVIEW_SIZE = 16,
    RUNTIME_RECV_BUFFER_SIZE = 256,
    RUNTIME_SEND_BUFFER_SIZE = 48,
    RUNTIME_WII_SOCKADDR_IN_SIZE = 8,
};

static const char runtime_kd_path[] __attribute_section_rodata__ = "/dev/net/kd/request";
static const char runtime_ip_path[] __attribute_section_rodata__ = "/dev/net/ip/top";

extern void runtime_canary_start(void);
extern void runtime_canary_end(void);

volatile u32 runtime_copy_complete_marker __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_executed_marker __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_execution_counter __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_status __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_bootstrap_return_marker __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_poll_counter __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_poll_heartbeat __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_poll_last_sequence __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_hook_wrapper_entry_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_hook_wrapper_before_poll_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_poll_entry_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_poll_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_state_machine_entry_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_state_machine_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_c_before_veneer_call_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_retail_veneer_entry_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_retail_target_return_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_retail_veneer_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_c_after_veneer_call_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_ios_submit_attempt_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_ios_submit_return_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_ios_submit_return_value __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_callback_entry_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_callback_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_hook_wrapper_after_poll_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_hook_wrapper_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_last_execution_marker __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_last_transport_phase_before_step __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_last_transport_phase_after_step __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_verified_game_r2 __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_verified_game_r13 __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_retail_veneer_selftest_observed_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_retail_veneer_selftest_after_call_flag __attribute_section_state__ __attribute_used__ = 0;

volatile u32 runtime_transport_phase __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_error __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_ios_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_pending_operation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_pending_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_callback_pending __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_kd_fd __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_ip_fd __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_socket_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_host_id __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bound_port __attribute_section_state__ __attribute_used__ = RUNTIME_UDP_PORT;
volatile u32 runtime_transport_receive_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_bytes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_bytes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_receive_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_send_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_peer_ipv4 __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_peer_port __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_peer_family __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_poll_action __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_submit_result __attribute_section_state__ __attribute_used__ = 0;

volatile u8 runtime_transport_last_receive_preview[RUNTIME_PREVIEW_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u8 runtime_transport_last_send_preview[RUNTIME_PREVIEW_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};

static volatile u32 runtime_transport_send_armed __attribute_section_state__ __attribute_used__ = 0;
static volatile u32 runtime_transport_tx_sequence __attribute_section_state__ __attribute_used__ = 0;
static volatile u32 runtime_transport_last_fcntl_flags __attribute_section_state__ __attribute_used__ = 0;

static u8 runtime_transport_nwc24_buffer[0x20] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static u32 runtime_transport_socket_params[3] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static u32 runtime_transport_fcntl_params[3] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_bind_params runtime_transport_bind_params __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static u32 runtime_transport_recv_params[2] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_sendto_params runtime_transport_sendto_params
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_ioctlv runtime_transport_recv_iov[3] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_ioctlv runtime_transport_send_iov[2] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static u8 runtime_transport_receive_buffer[RUNTIME_RECV_BUFFER_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static u8 runtime_transport_send_buffer[RUNTIME_SEND_BUFFER_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static u8 runtime_transport_source_sockaddr[32] __attribute_section_state_aligned_32__ __attribute_used__ = {0};

static void runtime_memzero(volatile void* destination, u32 size) __attribute_section_code__;
static void runtime_memcpy(volatile void* destination, const volatile void* source, u32 size) __attribute_section_code__;
static u16 runtime_bswap16(u16 value) __attribute_section_code__;
static u32 runtime_bswap32(u32 value) __attribute_section_code__;
static void runtime_store_u32_be(volatile u8* destination, u32 value) __attribute_section_code__;
static void runtime_copy_preview(volatile u8* destination, const volatile u8* source, u32 size) __attribute_section_code__;
static void runtime_copy_sockaddr_in(volatile u8* destination, u32 address_be, u16 port_be) __attribute_section_code__;
static void runtime_prepare_recv_vectors(void) __attribute_section_code__;
static void runtime_prepare_send_payload(void) __attribute_section_code__;
static void runtime_set_phase(u32 phase, u32 action) __attribute_section_code__;
static void runtime_diag_increment(volatile u32* counter) __attribute_section_code__;
static void runtime_diag_store_marker(u32 value) __attribute_section_code__;
static void runtime_diag_record_submit_return(s32 result) __attribute_section_code__;
static u32 runtime_transport_is_dry_run_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_open_kd_once_mode(void) __attribute_section_code__;
static void runtime_cache_flush(const volatile void* address, u32 size) __attribute_section_code__;
static void runtime_cache_invalidate(const volatile void* address, u32 size) __attribute_section_code__;
extern s32 runtime_call_retail_ios_open_async(
    const char* filepath,
    u32 mode,
    s32 (*callback)(s32, void*),
    void* usrdata
) __attribute_section_code__;
extern s32 runtime_call_retail_ios_close_async(s32 fd, s32 (*callback)(s32, void*), void* usrdata)
    __attribute_section_code__;
extern s32 runtime_call_retail_ios_ioctl_async(
    s32 fd,
    s32 ioctl,
    void* buffer_in,
    s32 len_in,
    void* buffer_io,
    s32 len_io,
    s32 (*callback)(s32, void*),
    void* usrdata
) __attribute_section_code__;
extern s32 runtime_call_retail_ios_ioctlv_async(
    s32 fd,
    s32 ioctl,
    s32 cnt_in,
    s32 cnt_io,
    void* argv,
    s32 (*callback)(s32, void*),
    void* usrdata
) __attribute_section_code__;
extern s32 runtime_call_retail_veneer_selftest(s32 value_a, s32 value_b, s32 value_c, s32 value_d)
    __attribute_section_code__;
static s32 runtime_submit_open(const char* path, volatile s32* destination_fd, u32 next_phase) __attribute_section_code__;
static s32 runtime_submit_close(s32 fd, u32 next_phase) __attribute_section_code__;
static s32 runtime_submit_ioctl(
    s32 fd,
    s32 ioctl,
    volatile void* buffer_in,
    s32 len_in,
    volatile void* buffer_io,
    s32 len_io,
    u32 next_phase
) __attribute_section_code__;
static s32 runtime_submit_ioctlv(
    s32 fd,
    s32 ioctl,
    s32 cnt_in,
    s32 cnt_io,
    runtime_ioctlv* argv,
    u32 next_phase
) __attribute_section_code__;
static s32 runtime_wait_completion(void) __attribute_section_code__;
static void runtime_record_init_error(s32 result) __attribute_section_code__;
static void runtime_record_steady_state_error(s32 result) __attribute_section_code__;
static void runtime_on_recv_complete(s32 result) __attribute_section_code__;
static void runtime_on_send_complete(s32 result) __attribute_section_code__;
s32 runtime_local_veneer_selftest_target(
    s32 value_a,
    s32 value_b,
    s32 value_c,
    s32 value_d
) __attribute_section_code_keep__ __attribute_used__;
s32 runtime_run_retail_veneer_selftest(void) __attribute_section_code_keep__ __attribute_used__;

static void runtime_memzero(volatile void* destination, u32 size)
{
    volatile u8* current = (volatile u8*)destination;
    u32 index = 0;
    while (index < size) {
        current[index] = 0;
        index += 1;
    }
}

static void runtime_memcpy(volatile void* destination, const volatile void* source, u32 size)
{
    volatile u8* current_destination = (volatile u8*)destination;
    const volatile u8* current_source = (const volatile u8*)source;
    u32 index = 0;
    while (index < size) {
        current_destination[index] = current_source[index];
        index += 1;
    }
}

static u16 runtime_bswap16(u16 value)
{
    return (u16)((value >> 8) | (value << 8));
}

static u32 runtime_bswap32(u32 value)
{
    return ((value & 0x000000FFU) << 24)
        | ((value & 0x0000FF00U) << 8)
        | ((value & 0x00FF0000U) >> 8)
        | ((value & 0xFF000000U) >> 24);
}

static void runtime_store_u32_be(volatile u8* destination, u32 value)
{
    destination[0] = (u8)(value >> 24);
    destination[1] = (u8)(value >> 16);
    destination[2] = (u8)(value >> 8);
    destination[3] = (u8)value;
}

static void runtime_copy_preview(volatile u8* destination, const volatile u8* source, u32 size)
{
    u32 index = 0;
    while (index < RUNTIME_PREVIEW_SIZE) {
        destination[index] = index < size ? source[index] : 0;
        index += 1;
    }
}

static void runtime_copy_sockaddr_in(volatile u8* destination, u32 address_be, u16 port_be)
{
    runtime_memzero(destination, 28);
    destination[0] = RUNTIME_WII_SOCKADDR_IN_SIZE;
    destination[1] = AF_INET;
    destination[2] = (u8)(port_be >> 8);
    destination[3] = (u8)port_be;
    destination[4] = (u8)(address_be >> 24);
    destination[5] = (u8)(address_be >> 16);
    destination[6] = (u8)(address_be >> 8);
    destination[7] = (u8)address_be;
}

static void runtime_set_phase(u32 phase, u32 action)
{
    runtime_transport_phase = phase;
    runtime_transport_last_poll_action = action;
}

static void runtime_diag_increment(volatile u32* counter)
{
#if PRIME3_ENABLE_RECURRING_HOOK_DIAGNOSTICS
    *counter += 1;
#else
    (void)counter;
#endif
}

static void runtime_diag_store_marker(u32 value)
{
#if PRIME3_ENABLE_RECURRING_HOOK_DIAGNOSTICS
    runtime_last_execution_marker = value;
#else
    (void)value;
#endif
}

static void runtime_diag_record_submit_return(s32 result)
{
#if PRIME3_ENABLE_RECURRING_HOOK_DIAGNOSTICS
    runtime_ios_submit_return_count += 1;
    runtime_ios_submit_return_value = result;
#else
    (void)result;
#endif
}

s32 runtime_local_veneer_selftest_target(s32 value_a, s32 value_b, s32 value_c, s32 value_d)
{
    return value_a + (value_b * 2) + (value_c * 3) + (value_d * 4) + 0x1234;
}

s32 runtime_run_retail_veneer_selftest(void)
{
    s32 result = 0;
    runtime_diag_increment(&runtime_c_before_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL);
    result = runtime_call_retail_veneer_selftest(1, 2, 3, 4);
    runtime_retail_veneer_selftest_observed_result = result;
    runtime_retail_veneer_selftest_after_call_flag = 1;
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    return result;
}

static u32 runtime_transport_is_dry_run_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_DRY_RUN;
}

static u32 runtime_transport_is_open_kd_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_OPEN_KD_ONCE;
}

static void runtime_cache_flush(const volatile void* address, u32 size)
{
    u32 aligned = (u32)address & ~31U;
    u32 end = ((u32)address + size + 31U) & ~31U;
    while (aligned < end) {
        __asm__ volatile("dcbf 0,%0" : : "r"(aligned) : "memory");
        aligned += 32;
    }
    __asm__ volatile("sync" ::: "memory");
}

static void runtime_cache_invalidate(const volatile void* address, u32 size)
{
    u32 aligned = (u32)address & ~31U;
    u32 end = ((u32)address + size + 31U) & ~31U;
    while (aligned < end) {
        __asm__ volatile("dcbi 0,%0" : : "r"(aligned) : "memory");
        aligned += 32;
    }
    __asm__ volatile("sync" ::: "memory");
}

#if PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
static s32 runtime_ios_callback(s32 result, void* usrdata) __attribute_section_code__;

static s32 runtime_ios_callback(s32 result, void* usrdata)
{
    (void)usrdata;
    runtime_diag_increment(&runtime_callback_entry_count);
    runtime_transport_last_ios_result = result;
    runtime_transport_callback_generation = runtime_transport_pending_generation;
    runtime_transport_callback_count += 1;
    runtime_transport_callback_pending = 1;
    runtime_callback_result = result;
    runtime_diag_increment(&runtime_callback_exit_count);
    return 0;
}

static s32 runtime_submit_open(const char* path, volatile s32* destination_fd, u32 next_phase)
{
    s32 result = 0;
    runtime_diag_increment(&runtime_ios_submit_attempt_count);
    runtime_diag_increment(&runtime_c_before_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL);
    if (runtime_transport_is_dry_run_mode()) {
        runtime_transport_last_submit_result = 0;
        runtime_diag_record_submit_return(0);
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        runtime_transport_callback_pending = 0;
        runtime_transport_last_ios_result = 0;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        return 0;
    }

    result = runtime_call_retail_ios_open_async(path, 0, runtime_ios_callback, (void*)destination_fd);
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_diag_record_submit_return(result);
    if (result < 0) {
        return result;
    }
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_OPEN;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    runtime_set_phase(next_phase, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
    return 0;
}

static s32 runtime_submit_close(s32 fd, u32 next_phase)
{
    s32 result = 0;
    runtime_diag_increment(&runtime_ios_submit_attempt_count);
    runtime_diag_increment(&runtime_c_before_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL);
    if (runtime_transport_is_dry_run_mode()) {
        runtime_transport_last_submit_result = 0;
        runtime_diag_record_submit_return(0);
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        runtime_transport_callback_pending = 0;
        runtime_transport_last_ios_result = 0;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        return 0;
    }

    result = runtime_call_retail_ios_close_async(fd, runtime_ios_callback, 0);
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_diag_record_submit_return(result);
    if (result < 0) {
        return result;
    }
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_CLOSE;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    runtime_set_phase(next_phase, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
    return 0;
}

static s32 runtime_submit_ioctl(
    s32 fd,
    s32 ioctl,
    volatile void* buffer_in,
    s32 len_in,
    volatile void* buffer_io,
    s32 len_io,
    u32 next_phase
)
{
    s32 result = 0;
    runtime_diag_increment(&runtime_ios_submit_attempt_count);
    runtime_diag_increment(&runtime_c_before_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL);
    if (runtime_transport_is_dry_run_mode()) {
        runtime_transport_last_submit_result = 0;
        runtime_diag_record_submit_return(0);
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        runtime_transport_callback_pending = 0;
        runtime_transport_last_ios_result = 0;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        return 0;
    }

    if (buffer_in != 0 && len_in > 0) {
        runtime_cache_flush(buffer_in, (u32)len_in);
    }
    if (buffer_io != 0 && len_io > 0) {
        runtime_cache_flush(buffer_io, (u32)len_io);
    }
    result = runtime_call_retail_ios_ioctl_async(
        fd,
        ioctl,
        (void*)buffer_in,
        len_in,
        (void*)buffer_io,
        len_io,
        runtime_ios_callback,
        0
    );
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_diag_record_submit_return(result);
    if (result < 0) {
        return result;
    }
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_IOCTL;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    runtime_set_phase(next_phase, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
    return 0;
}

static s32 runtime_submit_ioctlv(
    s32 fd,
    s32 ioctl,
    s32 cnt_in,
    s32 cnt_io,
    runtime_ioctlv* argv,
    u32 next_phase
)
{
    s32 result = 0;
    runtime_diag_increment(&runtime_ios_submit_attempt_count);
    runtime_diag_increment(&runtime_c_before_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL);
    if (runtime_transport_is_dry_run_mode()) {
        runtime_transport_last_submit_result = 0;
        runtime_diag_record_submit_return(0);
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        runtime_transport_callback_pending = 0;
        runtime_transport_last_ios_result = 0;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        return 0;
    }

    s32 index = 0;
    while (index < cnt_in) {
        runtime_cache_flush(argv[index].data, argv[index].len);
        index += 1;
    }
    while (index < cnt_in + cnt_io) {
        runtime_cache_flush(argv[index].data, argv[index].len);
        index += 1;
    }
    runtime_cache_flush(argv, (u32)((cnt_in + cnt_io) * (s32)sizeof(runtime_ioctlv)));
    result = runtime_call_retail_ios_ioctlv_async(fd, ioctl, cnt_in, cnt_io, argv, runtime_ios_callback, 0);
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_diag_record_submit_return(result);
    if (result < 0) {
        return result;
    }
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_IOCTLV;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    runtime_set_phase(next_phase, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
    return 0;
}

static s32 runtime_wait_completion(void)
{
    if (runtime_transport_callback_pending == 0) {
        runtime_set_phase(runtime_transport_phase, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        return 1;
    }
    runtime_transport_callback_pending = 0;
    if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_IOCTL) {
        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP) {
            runtime_cache_invalidate(runtime_transport_nwc24_buffer, sizeof(runtime_transport_nwc24_buffer));
        } else if (
            runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SOCKET
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_GET
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_SET
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_BIND
        ) {
            if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SOCKET) {
                runtime_cache_invalidate(runtime_transport_socket_params, sizeof(runtime_transport_socket_params));
            } else if (
                runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_GET
                || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_SET
            ) {
                runtime_cache_invalidate(runtime_transport_fcntl_params, sizeof(runtime_transport_fcntl_params));
            } else {
                runtime_cache_invalidate(&runtime_transport_bind_params, sizeof(runtime_transport_bind_params));
            }
        }
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_IOCTLV) {
        runtime_cache_invalidate(
            runtime_transport_recv_iov,
            (u32)(sizeof(runtime_transport_recv_iov))
        );
        runtime_cache_invalidate(
            runtime_transport_send_iov,
            (u32)(sizeof(runtime_transport_send_iov))
        );
        runtime_cache_invalidate(runtime_transport_receive_buffer, sizeof(runtime_transport_receive_buffer));
        runtime_cache_invalidate(runtime_transport_send_buffer, sizeof(runtime_transport_send_buffer));
        runtime_cache_invalidate(runtime_transport_source_sockaddr, sizeof(runtime_transport_source_sockaddr));
    }
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
    return 0;
}

static void runtime_record_init_error(s32 result)
{
    runtime_transport_last_error = result;
    runtime_transport_last_ios_result = result;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_ERROR, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
}

static void runtime_record_steady_state_error(s32 result)
{
    runtime_transport_last_error = result;
    runtime_transport_last_ios_result = result;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_READY, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
}

static void runtime_prepare_recv_vectors(void)
{
    runtime_memzero(runtime_transport_source_sockaddr, sizeof(runtime_transport_source_sockaddr));
    runtime_transport_recv_params[0] = (u32)runtime_transport_socket_fd;
    runtime_transport_recv_params[1] = MSG_DONTWAIT;
    runtime_transport_recv_iov[0].data = (void*)runtime_transport_recv_params;
    runtime_transport_recv_iov[0].len = sizeof(runtime_transport_recv_params);
    runtime_transport_recv_iov[1].data = (void*)runtime_transport_receive_buffer;
    runtime_transport_recv_iov[1].len = RUNTIME_RECV_BUFFER_SIZE;
    runtime_transport_recv_iov[2].data = (void*)runtime_transport_source_sockaddr;
    runtime_transport_recv_iov[2].len = sizeof(runtime_transport_source_sockaddr);
}

static void runtime_prepare_send_payload(void)
{
    runtime_transport_tx_sequence += 1;
    runtime_memzero(runtime_transport_send_buffer, sizeof(runtime_transport_send_buffer));
    runtime_transport_send_buffer[0] = 'P';
    runtime_transport_send_buffer[1] = '3';
    runtime_transport_send_buffer[2] = 'U';
    runtime_transport_send_buffer[3] = 'D';
    runtime_store_u32_be(&runtime_transport_send_buffer[4], 1);
    runtime_store_u32_be(&runtime_transport_send_buffer[8], runtime_transport_tx_sequence);
    runtime_store_u32_be(&runtime_transport_send_buffer[12], runtime_poll_counter);
    runtime_store_u32_be(&runtime_transport_send_buffer[16], runtime_transport_phase);
    runtime_store_u32_be(&runtime_transport_send_buffer[20], runtime_transport_host_id);
    runtime_store_u32_be(&runtime_transport_send_buffer[24], runtime_transport_receive_count);
    runtime_store_u32_be(&runtime_transport_send_buffer[28], runtime_transport_last_receive_length);
    runtime_copy_preview(
        &runtime_transport_send_buffer[32],
        runtime_transport_last_receive_preview,
        RUNTIME_PREVIEW_SIZE
    );
    runtime_copy_preview(
        runtime_transport_last_send_preview,
        runtime_transport_send_buffer,
        RUNTIME_PREVIEW_SIZE
    );
    runtime_transport_sendto_params.socket = (u32)runtime_transport_socket_fd;
    runtime_transport_sendto_params.flags = 0;
    runtime_transport_sendto_params.has_destaddr = 1;
    runtime_copy_sockaddr_in(
        runtime_transport_sendto_params.destaddr,
        runtime_transport_last_peer_ipv4,
        (u16)runtime_transport_last_peer_port
    );
    runtime_transport_send_iov[0].data = (void*)runtime_transport_send_buffer;
    runtime_transport_send_iov[0].len = RUNTIME_SEND_BUFFER_SIZE;
    runtime_transport_send_iov[1].data = (void*)&runtime_transport_sendto_params;
    runtime_transport_send_iov[1].len = sizeof(runtime_transport_sendto_params);
}

static void runtime_on_recv_complete(s32 result)
{
    runtime_transport_last_receive_length = result > 0 ? (u32)result : 0;
    if (result <= 0) {
        runtime_record_steady_state_error(result);
        return;
    }

    runtime_transport_receive_count += 1;
    runtime_transport_receive_bytes += (u32)result;
    runtime_copy_preview(
        runtime_transport_last_receive_preview,
        runtime_transport_receive_buffer,
        (u32)result
    );
    runtime_transport_last_peer_family = runtime_transport_source_sockaddr[1];
    runtime_transport_last_peer_port = (u32)(
        ((u16)runtime_transport_source_sockaddr[2] << 8)
        | (u16)runtime_transport_source_sockaddr[3]
    );
    runtime_transport_last_peer_ipv4 = ((u32)runtime_transport_source_sockaddr[4] << 24)
        | ((u32)runtime_transport_source_sockaddr[5] << 16)
        | ((u32)runtime_transport_source_sockaddr[6] << 8)
        | (u32)runtime_transport_source_sockaddr[7];
    runtime_transport_send_armed = runtime_transport_last_peer_family == AF_INET ? 1U : 0U;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_READY, RUNTIME_TRANSPORT_POLL_ACTION_RECV);
}

static void runtime_on_send_complete(s32 result)
{
    runtime_transport_last_send_length = result > 0 ? (u32)result : 0;
    if (result <= 0) {
        runtime_record_steady_state_error(result);
        runtime_transport_send_armed = 0;
        return;
    }

    runtime_transport_send_count += 1;
    runtime_transport_send_bytes += (u32)result;
    runtime_transport_send_armed = 0;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_READY, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
}
#endif

void runtime_entry_impl(void) __attribute_section_code__;
void runtime_poll_entry_impl(void) __attribute_section_code__;

void runtime_entry_impl(void)
{
    runtime_executed_marker = PRIME3_RUNTIME_EXECUTED_MARKER_VALUE;
    runtime_execution_counter += 1;
    runtime_status = PRIME3_RUNTIME_SUCCESS_STATUS_VALUE;
    runtime_hook_wrapper_entry_count = 0;
    runtime_hook_wrapper_before_poll_count = 0;
    runtime_poll_entry_count = 0;
    runtime_poll_exit_count = 0;
    runtime_state_machine_entry_count = 0;
    runtime_state_machine_exit_count = 0;
    runtime_c_before_veneer_call_count = 0;
    runtime_retail_veneer_entry_count = 0;
    runtime_retail_target_return_count = 0;
    runtime_retail_veneer_exit_count = 0;
    runtime_c_after_veneer_call_count = 0;
    runtime_ios_submit_attempt_count = 0;
    runtime_ios_submit_return_count = 0;
    runtime_ios_submit_return_value = 0;
    runtime_callback_entry_count = 0;
    runtime_callback_exit_count = 0;
    runtime_hook_wrapper_after_poll_count = 0;
    runtime_hook_wrapper_exit_count = 0;
    runtime_last_execution_marker = 0;
    runtime_last_transport_phase_before_step = 0;
    runtime_last_transport_phase_after_step = 0;
    runtime_callback_result = 0;
    runtime_verified_game_r2 = 0;
    runtime_verified_game_r13 = 0;
    runtime_retail_veneer_selftest_observed_result = 0;
    runtime_retail_veneer_selftest_after_call_flag = 0;
    runtime_transport_last_error = 0;
    runtime_transport_last_ios_result = 0;
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
    runtime_transport_pending_generation = 0;
    runtime_transport_callback_generation = 0;
    runtime_transport_callback_count = 0;
    runtime_transport_callback_pending = 0;
    runtime_transport_kd_fd = -1;
    runtime_transport_ip_fd = -1;
    runtime_transport_socket_fd = -1;
    runtime_transport_host_id = 0;
    runtime_transport_bound_port = RUNTIME_UDP_PORT;
    runtime_transport_receive_count = 0;
    runtime_transport_receive_bytes = 0;
    runtime_transport_send_count = 0;
    runtime_transport_send_bytes = 0;
    runtime_transport_last_receive_length = 0;
    runtime_transport_last_send_length = 0;
    runtime_transport_last_peer_ipv4 = 0;
    runtime_transport_last_peer_port = 0;
    runtime_transport_last_peer_family = 0;
    runtime_transport_last_submit_result = 0;
    runtime_transport_send_armed = 0;
    runtime_transport_tx_sequence = 0;
    runtime_transport_last_fcntl_flags = 0;
    runtime_memzero(runtime_transport_last_receive_preview, sizeof(runtime_transport_last_receive_preview));
    runtime_memzero(runtime_transport_last_send_preview, sizeof(runtime_transport_last_send_preview));
    runtime_memzero(runtime_transport_nwc24_buffer, sizeof(runtime_transport_nwc24_buffer));
    runtime_memzero(runtime_transport_socket_params, sizeof(runtime_transport_socket_params));
    runtime_memzero(runtime_transport_fcntl_params, sizeof(runtime_transport_fcntl_params));
    runtime_memzero(&runtime_transport_bind_params, sizeof(runtime_transport_bind_params));
    runtime_memzero(runtime_transport_recv_params, sizeof(runtime_transport_recv_params));
    runtime_memzero(&runtime_transport_sendto_params, sizeof(runtime_transport_sendto_params));
    runtime_memzero(runtime_transport_recv_iov, sizeof(runtime_transport_recv_iov));
    runtime_memzero(runtime_transport_send_iov, sizeof(runtime_transport_send_iov));
    runtime_memzero(runtime_transport_receive_buffer, sizeof(runtime_transport_receive_buffer));
    runtime_memzero(runtime_transport_send_buffer, sizeof(runtime_transport_send_buffer));
    runtime_memzero(runtime_transport_source_sockaddr, sizeof(runtime_transport_source_sockaddr));
#if PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
    runtime_transport_phase = RUNTIME_TRANSPORT_PHASE_OPEN_KD;
    runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_INIT;
#else
    runtime_transport_phase = RUNTIME_TRANSPORT_PHASE_UNINITIALIZED;
    runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
#endif
}

void runtime_poll_entry_impl(void)
{
    u32 state_machine_entered = 0;
    runtime_poll_counter += 1;
    runtime_poll_heartbeat = runtime_poll_counter;
    runtime_poll_last_sequence = runtime_poll_counter;
    runtime_diag_increment(&runtime_poll_entry_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_POLL_ENTRY);

#if !PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
    runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
    goto runtime_poll_exit;
#endif

    runtime_last_transport_phase_before_step = runtime_transport_phase;
    runtime_diag_increment(&runtime_state_machine_entry_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_STATE_MACHINE_ENTRY);
    state_machine_entered = 1;

    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE) {
        runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
        goto runtime_poll_exit;
    }
    if (runtime_transport_is_dry_run_mode()) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        goto runtime_poll_exit;
    }

    if (
        runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_KD
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_KD
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_IP
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_GETHOSTID
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SOCKET
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_GET
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_SET
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_BIND
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_RECV
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND
    ) {
        s32 wait_result = runtime_wait_completion();
        if (wait_result != 0) {
            goto runtime_poll_exit;
        }

        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_KD) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_kd_fd = runtime_transport_last_ios_result;
            if (runtime_transport_is_open_kd_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_NWC24_STARTUP, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_KD, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_KD) {
            runtime_transport_kd_fd = -1;
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_OPEN_IP, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_IP) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_ip_fd = runtime_transport_last_ios_result;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SO_STARTUP, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_GETHOSTID, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_GETHOSTID) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            if (runtime_transport_last_ios_result == 0) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_GETHOSTID, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
                goto runtime_poll_exit;
            }
            runtime_transport_host_id = (u32)runtime_transport_last_ios_result;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SOCKET, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SOCKET) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_socket_fd = runtime_transport_last_ios_result;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FCNTL_GET, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_GET) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_last_fcntl_flags = (u32)runtime_transport_last_ios_result;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FCNTL_SET, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_SET) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_BIND, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_BIND) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_READY, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_RECV) {
            runtime_on_recv_complete(runtime_transport_last_ios_result);
            goto runtime_poll_exit;
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND) {
            runtime_on_send_complete(runtime_transport_last_ios_result);
            goto runtime_poll_exit;
        }
    }

    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_OPEN_KD) {
        if (runtime_submit_open(runtime_kd_path, &runtime_transport_kd_fd, RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_KD) < 0) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NWC24_STARTUP) {
        if (
            runtime_submit_ioctl(
                runtime_transport_kd_fd,
                IOCTL_NWC24_STARTUP,
                0,
                0,
                runtime_transport_nwc24_buffer,
                sizeof(runtime_transport_nwc24_buffer),
                RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CLOSE_KD) {
        if (runtime_submit_close(runtime_transport_kd_fd, RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_KD) < 0) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_OPEN_IP) {
        if (runtime_submit_open(runtime_ip_path, &runtime_transport_ip_fd, RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_IP) < 0) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SO_STARTUP) {
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_STARTUP,
                0,
                0,
                0,
                0,
                RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_GETHOSTID) {
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_GETHOSTID,
                0,
                0,
                0,
                0,
                RUNTIME_TRANSPORT_PHASE_WAIT_GETHOSTID
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SOCKET) {
        runtime_transport_socket_params[0] = AF_INET;
        runtime_transport_socket_params[1] = SOCK_DGRAM;
        runtime_transport_socket_params[2] = IPPROTO_IP;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_SOCKET,
                runtime_transport_socket_params,
                sizeof(runtime_transport_socket_params),
                0,
                0,
                RUNTIME_TRANSPORT_PHASE_WAIT_SOCKET
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_FCNTL_GET) {
        runtime_transport_fcntl_params[0] = (u32)runtime_transport_socket_fd;
        runtime_transport_fcntl_params[1] = F_GETFL;
        runtime_transport_fcntl_params[2] = 0;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_FCNTL,
                runtime_transport_fcntl_params,
                sizeof(runtime_transport_fcntl_params),
                0,
                0,
                RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_GET
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_FCNTL_SET) {
        runtime_transport_fcntl_params[0] = (u32)runtime_transport_socket_fd;
        runtime_transport_fcntl_params[1] = F_SETFL;
        runtime_transport_fcntl_params[2] = runtime_transport_last_fcntl_flags | IOS_O_NONBLOCK;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_FCNTL,
                runtime_transport_fcntl_params,
                sizeof(runtime_transport_fcntl_params),
                0,
                0,
                RUNTIME_TRANSPORT_PHASE_WAIT_FCNTL_SET
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_BIND) {
        runtime_memzero(&runtime_transport_bind_params, sizeof(runtime_transport_bind_params));
        runtime_transport_bind_params.socket = (u32)runtime_transport_socket_fd;
        runtime_transport_bind_params.has_name = 1;
        runtime_copy_sockaddr_in(
            runtime_transport_bind_params.name,
            INADDR_ANY,
            runtime_bswap16((u16)RUNTIME_UDP_PORT)
        );
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_BIND,
                &runtime_transport_bind_params,
                sizeof(runtime_transport_bind_params),
                0,
                0,
                RUNTIME_TRANSPORT_PHASE_WAIT_BIND
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_READY) {
        if (runtime_transport_send_armed != 0 && runtime_transport_last_peer_family == AF_INET) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SEND, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_RECV, RUNTIME_TRANSPORT_POLL_ACTION_RECV);
        }
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECV) {
        runtime_prepare_recv_vectors();
        if (
            runtime_submit_ioctlv(
                runtime_transport_ip_fd,
                IOCTLV_SO_RECVFROM,
                1,
                2,
                runtime_transport_recv_iov,
                RUNTIME_TRANSPORT_PHASE_WAIT_RECV
            ) < 0
        ) {
            runtime_record_steady_state_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND) {
        runtime_prepare_send_payload();
        if (
            runtime_submit_ioctlv(
                runtime_transport_ip_fd,
                IOCTLV_SO_SENDTO,
                2,
                0,
                runtime_transport_send_iov,
                RUNTIME_TRANSPORT_PHASE_WAIT_SEND
            ) < 0
        ) {
            runtime_transport_send_armed = 0;
            runtime_record_steady_state_error(runtime_transport_last_submit_result);
        }
    }

runtime_poll_exit:
    runtime_last_transport_phase_after_step = runtime_transport_phase;
    if (state_machine_entered != 0) {
        runtime_diag_increment(&runtime_state_machine_exit_count);
    }
    return;
}
