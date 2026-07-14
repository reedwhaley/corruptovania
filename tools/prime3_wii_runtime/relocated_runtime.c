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

typedef struct runtime_operation_context {
    u32 expected_generation;
    u32 completion_generation;
    u32 completion_flag;
    s32 completion_result;
    u32 callback_entry_count;
    u32 callback_exit_count;
    u32 stale_callback_count;
    u32 duplicate_callback_count;
} runtime_operation_context;

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
    RUNTIME_TRANSPORT_PHASE_CREATE_SOCKET = 13,
    RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET = 14,
    RUNTIME_TRANSPORT_PHASE_BIND_SOCKET = 15,
    RUNTIME_TRANSPORT_PHASE_WAIT_BIND_SOCKET = 16,
    RUNTIME_TRANSPORT_PHASE_BOUND_NO_RECV = 17,
    RUNTIME_TRANSPORT_PHASE_SO_STARTED = 18,
    RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE = 0xFE,
    RUNTIME_TRANSPORT_PHASE_FAILED = 0xFF,
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
    RUNTIME_TRANSPORT_OP_OPEN_KD = 1,
    RUNTIME_TRANSPORT_OP_NWC24_STARTUP = 2,
    RUNTIME_TRANSPORT_OP_CLOSE_KD = 3,
    RUNTIME_TRANSPORT_OP_OPEN_IP = 4,
    RUNTIME_TRANSPORT_OP_STARTUP = 5,
    RUNTIME_TRANSPORT_OP_GETHOSTID = 6,
    RUNTIME_TRANSPORT_OP_CREATE_SOCKET = 7,
    RUNTIME_TRANSPORT_OP_BIND_SOCKET = 8,
};

enum {
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_NORMAL = 0,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_DRY_RUN = 1,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_OPEN_KD_ONCE = 2,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_NWC24_STARTUP_ONCE = 3,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_CLOSE_KD_ONCE = 4,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_OPEN_IP_ONCE = 5,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_STARTUP_ONCE = 6,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_GETHOSTID_ONCE = 7,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_CREATE_SOCKET_ONCE = 8,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_BIND_ONCE = 9,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_IOCTL_ASYNC_ABI_PROBE = 10,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_NWC24_CLOSE_KD_ONCE = 11,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_NWC24_CLOSE_OPEN_IP_ONCE = 12,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_NWC24_CLOSE_OPEN_IP_STARTUP_ONCE = 13,
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
    IOCTL_SO_SOCKET = 15,
    IOCTL_SO_GETHOSTID = 16,
    IOCTL_SO_STARTUP = 31,
    AF_INET = 2,
    SOCK_DGRAM = 2,
    IPPROTO_IP = 0,
    INADDR_ANY = 0,
    RUNTIME_UDP_PORT = 43674,
    RUNTIME_PREVIEW_SIZE = 16,
    RUNTIME_WII_SOCKADDR_IN_SIZE = 8,
    RUNTIME_VERIFIED_IOS_IOCTL_ASYNC_ADDRESS = 0x80504FE0,
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
volatile u32 runtime_abi_probe_supplied_args[8] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u32 runtime_abi_probe_pre_call_args[8] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u32 runtime_abi_probe_target_args[8] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile s32 runtime_abi_probe_return_value __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_result_flags __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_stack_pointer_before __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_stack_pointer_after __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_saved_lr __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_restored_lr __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_saved_r2 __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_restored_r2 __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_saved_r13 __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_restored_r13 __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_target_ctr __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_abi_probe_after_call_flag __attribute_section_state__ __attribute_used__ = 0;

volatile u32 runtime_transport_phase __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_error __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_socket_error __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_ios_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_pending_operation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_pending_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_rejected_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_callback_pending __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_kd_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_kd_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_open_kd_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_open_kd_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_kd_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_kd_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_nwc24_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_nwc24_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_nwc24_synchronous_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_nwc24_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_nwc24_output_digest __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_nwc24_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_nwc24_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_open_ip_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_open_ip_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_path_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_path_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_mode_value __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_callback_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_context_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_callback_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_stale_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_open_ip_duplicate_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_ip_fd_before_open_ip __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_kd_close_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_kd_close_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_kd_close_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_kd_close_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_kd_close_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_kd_close_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_kd_close_submitted_fd __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_kd_fd_before_close __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_kd_fd_after_close __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_ip_close_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_close_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_startup_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_startup_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_target_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_command __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_startup_submitted_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_startup_callback_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_context_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_callback_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_stale_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_duplicate_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_service_started_before_submit __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_service_started_after_completion __attribute_section_state__ __attribute_used__
    = 0;
volatile s32 runtime_transport_ip_fd_before_startup __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_ip_fd_after_startup __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_startup_pending_before_submit __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_pending_after_completion __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_phase_before_submit __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_phase_after_completion __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_startup_pre_call_args[8] __attribute_section_state_aligned_32__ __attribute_used__
    = {0};
volatile u32 runtime_transport_get_host_id_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_get_host_id_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_get_host_id_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_socket_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_socket_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_bind_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_bind_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_kd_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_kd_closed __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_ip_fd __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_socket_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_host_id __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_service_started __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bound_port __attribute_section_state__ __attribute_used__ = RUNTIME_UDP_PORT;
volatile u32 runtime_transport_receive_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_submit_count __attribute_section_state__ __attribute_used__ = 0;
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
volatile u8 runtime_transport_nwc24_output_buffer[0x20]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_nwc24_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_kd_close_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_open_ip_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_startup_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static u32 runtime_transport_socket_params[3] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_bind_params runtime_transport_bind_params __attribute_section_state_aligned_32__ __attribute_used__ = {0};

static void runtime_memzero(volatile void* destination, u32 size) __attribute_section_code__;
static void runtime_memcpy(volatile void* destination, const volatile void* source, u32 size) __attribute_section_code__;
static u16 runtime_bswap16(u16 value) __attribute_section_code__;
static void runtime_copy_preview(volatile u8* destination, const volatile u8* source, u32 size) __attribute_section_code__;
static void runtime_copy_sockaddr_in(volatile u8* destination, u32 address_be, u16 port_be) __attribute_section_code__;
static void runtime_set_phase(u32 phase, u32 action) __attribute_section_code__;
static void runtime_diag_increment(volatile u32* counter) __attribute_section_code__;
static void runtime_diag_store_marker(u32 value) __attribute_section_code__;
static void runtime_diag_record_submit_return(s32 result) __attribute_section_code__;
static u32 runtime_transport_is_dry_run_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_open_kd_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_nwc24_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_close_kd_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_nwc24_close_kd_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_nwc24_close_open_ip_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_nwc24_close_open_ip_startup_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_open_ip_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_startup_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_get_host_id_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_create_socket_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_bind_once_mode(void) __attribute_section_code__;
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
extern s32 runtime_call_retail_read_async(
    s32 fd,
    void* buffer,
    s32 length,
    s32 (*callback)(s32, void*),
    void* usrdata
) __attribute_section_code__;
extern s32 runtime_call_retail_ios_ioctl_async(
    s32 fd,
    u32 command,
    const void* input,
    u32 input_length,
    void* output,
    u32 output_length,
    s32 (*callback)(s32, void*),
    void* userdata
) __attribute_section_code__;
extern s32 runtime_call_retail_veneer_selftest(
    s32 value_a,
    s32 value_b,
    s32 value_c,
    s32 value_d,
    s32 value_e,
    s32 value_f,
    s32 value_g,
    s32 value_h
) __attribute_section_code__;
static s32 runtime_submit_open(const char* path, u32 operation, u32 next_phase) __attribute_section_code__;
static s32 runtime_submit_close(s32 fd, u32 operation, u32 next_phase) __attribute_section_code__;
static s32 runtime_submit_ioctl(
    s32 fd,
    s32 ioctl,
    volatile void* buffer_in,
    s32 len_in,
    volatile void* buffer_io,
    s32 len_io,
    u32 operation,
    u32 next_phase
) __attribute_section_code__;
static s32 runtime_wait_completion(void) __attribute_section_code__;
static void runtime_record_init_error(s32 result) __attribute_section_code__;
static void runtime_record_socket_error(s32 result) __attribute_section_code__;
static void runtime_record_operation_callback(void) __attribute_section_code__;
static void runtime_record_submit_evidence(u32 operation, s32 result, u32 generation) __attribute_section_code__;
static void runtime_record_callback_evidence(u32 operation, s32 result, u32 generation) __attribute_section_code__;
static void runtime_sync_open_ip_context_evidence(void) __attribute_section_code__;
static void runtime_sync_startup_context_evidence(void) __attribute_section_code__;
static u32 runtime_digest_words(const volatile u8* source, u32 size) __attribute_section_code__;
u32 runtime_abi_probe_expected_return_value __attribute_section_state__ __attribute_used__ = 0x13579BDFU;
s32 runtime_local_veneer_selftest_target(
    s32 value_a,
    s32 value_b,
    s32 value_c,
    s32 value_d,
    s32 value_e,
    s32 value_f,
    s32 value_g,
    s32 value_h
) __attribute_section_code_keep__ __attribute_used__;
s32 runtime_run_retail_veneer_selftest(void) __attribute_section_code_keep__ __attribute_used__;
static u32 runtime_transport_is_ioctl_async_abi_probe_mode(void) __attribute_section_code__;

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

s32 runtime_local_veneer_selftest_target(
    s32 value_a,
    s32 value_b,
    s32 value_c,
    s32 value_d,
    s32 value_e,
    s32 value_f,
    s32 value_g,
    s32 value_h
)
{
    runtime_abi_probe_target_args[0] = (u32)value_a;
    runtime_abi_probe_target_args[1] = (u32)value_b;
    runtime_abi_probe_target_args[2] = (u32)value_c;
    runtime_abi_probe_target_args[3] = (u32)value_d;
    runtime_abi_probe_target_args[4] = (u32)value_e;
    runtime_abi_probe_target_args[5] = (u32)value_f;
    runtime_abi_probe_target_args[6] = (u32)value_g;
    runtime_abi_probe_target_args[7] = (u32)value_h;
    return (s32)runtime_abi_probe_expected_return_value;
}

s32 runtime_run_retail_veneer_selftest(void)
{
    s32 result = 0;
    u32 expected_args[8] = {
        0x11111111U,
        0x22222222U,
        0x33333333U,
        0x44444444U,
        0x55555555U,
        0x66666666U,
        0x77777777U,
        0x88888888U,
    };
    u32 index = 0;
    u32 result_flags = 0;
    runtime_diag_increment(&runtime_c_before_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL);
    while (index < 8) {
        runtime_abi_probe_supplied_args[index] = expected_args[index];
        runtime_abi_probe_target_args[index] = 0;
        index += 1;
    }
    runtime_abi_probe_after_call_flag = 0;
    result = runtime_call_retail_veneer_selftest(
        (s32)expected_args[0],
        (s32)expected_args[1],
        (s32)expected_args[2],
        (s32)expected_args[3],
        (s32)expected_args[4],
        (s32)expected_args[5],
        (s32)expected_args[6],
        (s32)expected_args[7]
    );
    runtime_abi_probe_return_value = result;
    runtime_abi_probe_after_call_flag = 1;
    if ((u32)result == runtime_abi_probe_expected_return_value) {
        result_flags |= 1U << 0;
    }
    if (runtime_abi_probe_after_call_flag != 0) {
        result_flags |= 1U << 1;
    }
    if (runtime_abi_probe_stack_pointer_before == runtime_abi_probe_stack_pointer_after) {
        result_flags |= 1U << 2;
    }
    if (runtime_abi_probe_saved_lr == runtime_abi_probe_restored_lr) {
        result_flags |= 1U << 3;
    }
    if (runtime_abi_probe_saved_r2 == runtime_abi_probe_restored_r2) {
        result_flags |= 1U << 4;
    }
    if (runtime_abi_probe_saved_r13 == runtime_abi_probe_restored_r13) {
        result_flags |= 1U << 5;
    }
    index = 0;
    while (index < 8) {
        if (runtime_abi_probe_pre_call_args[index] == expected_args[index]) {
            result_flags |= (1U << (6 + index));
        }
        if (runtime_abi_probe_target_args[index] == expected_args[index]) {
            result_flags |= (1U << (14 + index));
        }
        index += 1;
    }
    runtime_abi_probe_result_flags = result_flags;
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

static u32 runtime_transport_is_nwc24_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_NWC24_STARTUP_ONCE;
}

static u32 runtime_transport_is_close_kd_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_CLOSE_KD_ONCE;
}

static u32 runtime_transport_is_nwc24_close_kd_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_NWC24_CLOSE_KD_ONCE;
}

static u32 runtime_transport_is_nwc24_close_open_ip_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_NWC24_CLOSE_OPEN_IP_ONCE;
}

static u32 runtime_transport_is_nwc24_close_open_ip_startup_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE
            == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_NWC24_CLOSE_OPEN_IP_STARTUP_ONCE;
}

static u32 runtime_transport_is_open_ip_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_OPEN_IP_ONCE;
}

static u32 runtime_transport_is_startup_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_STARTUP_ONCE;
}

static u32 runtime_transport_is_get_host_id_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_GETHOSTID_ONCE;
}

static u32 runtime_transport_is_create_socket_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_CREATE_SOCKET_ONCE;
}

static u32 runtime_transport_is_bind_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_BIND_ONCE;
}

static u32 runtime_transport_is_ioctl_async_abi_probe_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_IOCTL_ASYNC_ABI_PROBE;
}

static u32 runtime_digest_words(const volatile u8* source, u32 size)
{
    u32 digest = 0;
    u32 index = 0;
    while (index < size) {
        digest = (digest << 5) - digest + source[index];
        index += 1;
    }
    return digest;
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
    if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_NONE) {
        runtime_transport_rejected_callback_count += 1;
        return 0;
    }
    if (runtime_transport_callback_pending != 0) {
        if (
            runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP
            || runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CLOSE_KD
            || runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_OPEN_IP
            || runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_STARTUP
        ) {
            volatile runtime_operation_context* context = runtime_transport_pending_operation
                == RUNTIME_TRANSPORT_OP_NWC24_STARTUP ? &runtime_transport_nwc24_context
                : runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CLOSE_KD
                    ? &runtime_transport_kd_close_context
                    : runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_OPEN_IP
                        ? &runtime_transport_open_ip_context : &runtime_transport_startup_context;
            if (usrdata == (void*)context) {
                context->duplicate_callback_count += 1;
                if (context == &runtime_transport_open_ip_context) {
                    runtime_sync_open_ip_context_evidence();
                } else if (context == &runtime_transport_startup_context) {
                    runtime_sync_startup_context_evidence();
                }
            }
        }
        runtime_transport_rejected_callback_count += 1;
        return 0;
    }
    runtime_diag_increment(&runtime_callback_entry_count);
    if (
        runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP
        || runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CLOSE_KD
        || runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_OPEN_IP
        || runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_STARTUP
    ) {
        volatile runtime_operation_context* context = runtime_transport_pending_operation
            == RUNTIME_TRANSPORT_OP_NWC24_STARTUP ? &runtime_transport_nwc24_context
            : runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CLOSE_KD
                ? &runtime_transport_kd_close_context
                : runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_OPEN_IP
                    ? &runtime_transport_open_ip_context : &runtime_transport_startup_context;
        if (usrdata != (void*)context) {
            context->stale_callback_count += 1;
            if (context == &runtime_transport_open_ip_context) {
                runtime_sync_open_ip_context_evidence();
            } else if (context == &runtime_transport_startup_context) {
                runtime_sync_startup_context_evidence();
            }
            runtime_transport_rejected_callback_count += 1;
            return 0;
        }
        context->callback_entry_count += 1;
        if (context->expected_generation != runtime_transport_pending_generation) {
            context->stale_callback_count += 1;
            if (context == &runtime_transport_open_ip_context) {
                runtime_sync_open_ip_context_evidence();
            } else if (context == &runtime_transport_startup_context) {
                runtime_sync_startup_context_evidence();
            }
            runtime_transport_rejected_callback_count += 1;
            return 0;
        }
        if (context->completion_flag != 0) {
            context->duplicate_callback_count += 1;
            if (context == &runtime_transport_open_ip_context) {
                runtime_sync_open_ip_context_evidence();
            } else if (context == &runtime_transport_startup_context) {
                runtime_sync_startup_context_evidence();
            }
            runtime_transport_rejected_callback_count += 1;
            return 0;
        }
        context->completion_generation = runtime_transport_pending_generation;
        context->completion_result = result;
        context->completion_flag = 1;
    }
    runtime_transport_last_ios_result = result;
    runtime_transport_callback_generation = runtime_transport_pending_generation;
    runtime_transport_callback_count += 1;
    runtime_transport_callback_pending = 1;
    runtime_callback_result = result;
    if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP) {
        runtime_transport_nwc24_context.callback_exit_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CLOSE_KD) {
        runtime_transport_kd_close_context.callback_exit_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_OPEN_IP) {
        runtime_transport_open_ip_context.callback_exit_count += 1;
        runtime_sync_open_ip_context_evidence();
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_STARTUP) {
        runtime_transport_startup_context.callback_exit_count += 1;
        runtime_sync_startup_context_evidence();
    }
    runtime_diag_increment(&runtime_callback_exit_count);
    return 0;
}

static s32 runtime_submit_open(const char* path, u32 operation, u32 next_phase)
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

    runtime_transport_pending_operation = operation;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    if (operation == RUNTIME_TRANSPORT_OP_OPEN_IP) {
        if (
            !(runtime_transport_is_nwc24_close_open_ip_once_mode()
                || runtime_transport_is_nwc24_close_open_ip_startup_once_mode())
            || runtime_transport_kd_fd != -1 || runtime_transport_kd_closed == 0 || runtime_transport_ip_fd != -1
        ) {
            runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
            runtime_transport_last_submit_result = -1;
            runtime_record_submit_evidence(operation, -1, runtime_transport_pending_generation);
            runtime_diag_record_submit_return(-1);
            return -1;
        }
        runtime_memzero(&runtime_transport_open_ip_context, sizeof(runtime_transport_open_ip_context));
        runtime_transport_open_ip_context.expected_generation = runtime_transport_pending_generation;
        runtime_transport_open_ip_path_pointer = (u32)path;
        runtime_transport_open_ip_path_length = sizeof(runtime_ip_path) - 1;
        runtime_transport_open_ip_mode_value = 0;
        runtime_transport_open_ip_callback_pointer = (u32)runtime_ios_callback;
        runtime_transport_open_ip_context_pointer = (u32)&runtime_transport_open_ip_context;
        runtime_transport_ip_fd_before_open_ip = runtime_transport_ip_fd;
        runtime_sync_open_ip_context_evidence();
        result = runtime_call_retail_ios_open_async(
            path,
            runtime_transport_open_ip_mode_value,
            runtime_ios_callback,
            (void*)&runtime_transport_open_ip_context
        );
    } else {
        result = runtime_call_retail_ios_open_async(path, 0, runtime_ios_callback, 0);
    }
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_record_submit_evidence(operation, result, runtime_transport_pending_generation);
    runtime_diag_record_submit_return(result);
    if (result < 0) {
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        return result;
    }
    runtime_set_phase(next_phase, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
    return 0;
}

static s32 runtime_submit_close(s32 fd, u32 operation, u32 next_phase)
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

    if (
        !(runtime_transport_is_nwc24_close_kd_once_mode() || runtime_transport_is_nwc24_close_open_ip_once_mode()
            || runtime_transport_is_nwc24_close_open_ip_startup_once_mode())
        || operation != RUNTIME_TRANSPORT_OP_CLOSE_KD
        || fd < 0
        || fd != runtime_transport_kd_fd
        || runtime_transport_kd_closed != 0
        || runtime_transport_nwc24_callback_count != 1
        || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
    ) {
        runtime_transport_last_submit_result = -1;
        runtime_record_submit_evidence(operation, -1, runtime_transport_pending_generation);
        runtime_diag_record_submit_return(-1);
        return -1;
    }
    runtime_transport_kd_close_submitted_fd = fd;
    runtime_transport_kd_fd_before_close = runtime_transport_kd_fd;
    runtime_transport_pending_operation = operation;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    runtime_memzero(&runtime_transport_kd_close_context, sizeof(runtime_transport_kd_close_context));
    runtime_transport_kd_close_context.expected_generation = runtime_transport_pending_generation;
    result = runtime_call_retail_ios_close_async(fd, runtime_ios_callback, (void*)&runtime_transport_kd_close_context);
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_record_submit_evidence(operation, result, runtime_transport_pending_generation);
    runtime_diag_record_submit_return(result);
    if (result < 0) {
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        return result;
    }
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
    u32 operation,
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
    if (operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP) {
        if (
            !(runtime_transport_is_nwc24_once_mode() || runtime_transport_is_nwc24_close_kd_once_mode()
                || runtime_transport_is_nwc24_close_open_ip_once_mode()
                || runtime_transport_is_nwc24_close_open_ip_startup_once_mode())
            || fd < 0
            || ioctl != IOCTL_NWC24_STARTUP
            || buffer_in != 0
            || len_in != 0
            || buffer_io != runtime_transport_nwc24_output_buffer
            || len_io != 0x20
            || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
        ) {
            runtime_transport_last_ios_result = -1;
            runtime_transport_last_submit_result = -1;
            runtime_record_submit_evidence(operation, -1, runtime_transport_pending_generation);
            runtime_diag_record_submit_return(-1);
            return -1;
        }
    } else if (operation == RUNTIME_TRANSPORT_OP_STARTUP) {
        if (
            !(runtime_transport_is_startup_once_mode() || runtime_transport_is_nwc24_close_open_ip_startup_once_mode())
            || fd < 0
            || fd != runtime_transport_ip_fd
            || ioctl != IOCTL_SO_STARTUP
            || buffer_in != 0
            || len_in != 0
            || buffer_io != 0
            || len_io != 0
            || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
            || runtime_transport_startup_submit_count != 1
            || runtime_transport_kd_fd != -1
            || runtime_transport_kd_closed == 0
            || runtime_transport_service_started != 0
        ) {
            runtime_transport_last_ios_result = -1;
            runtime_transport_last_submit_result = -1;
            runtime_record_submit_evidence(operation, -1, runtime_transport_pending_generation);
            runtime_diag_record_submit_return(-1);
            return -1;
        }
        runtime_transport_startup_target_address = RUNTIME_VERIFIED_IOS_IOCTL_ASYNC_ADDRESS;
        runtime_transport_startup_command = (u32)ioctl;
        runtime_transport_startup_submitted_fd = fd;
        runtime_transport_startup_callback_pointer = (u32)runtime_ios_callback;
        runtime_transport_startup_context_pointer = (u32)&runtime_transport_startup_context;
        runtime_transport_startup_service_started_before_submit = runtime_transport_service_started;
        runtime_transport_ip_fd_before_startup = runtime_transport_ip_fd;
        runtime_transport_startup_pending_before_submit = runtime_transport_pending_operation;
        runtime_transport_startup_phase_before_submit = runtime_transport_phase;
        runtime_transport_startup_pre_call_args[0] = (u32)fd;
        runtime_transport_startup_pre_call_args[1] = (u32)ioctl;
        runtime_transport_startup_pre_call_args[2] = (u32)buffer_in;
        runtime_transport_startup_pre_call_args[3] = (u32)len_in;
        runtime_transport_startup_pre_call_args[4] = (u32)buffer_io;
        runtime_transport_startup_pre_call_args[5] = (u32)len_io;
        runtime_transport_startup_pre_call_args[6] = (u32)runtime_ios_callback;
        runtime_transport_startup_pre_call_args[7] = (u32)&runtime_transport_startup_context;
        runtime_memzero(&runtime_transport_startup_context, sizeof(runtime_transport_startup_context));
        runtime_transport_startup_context.expected_generation = runtime_transport_pending_generation + 1;
        runtime_sync_startup_context_evidence();
    } else {
        runtime_transport_last_ios_result = -1;
        runtime_transport_last_submit_result = -1;
        runtime_record_submit_evidence(operation, -1, runtime_transport_pending_generation);
        runtime_diag_record_submit_return(-1);
        return -1;
    }
    runtime_transport_pending_operation = operation;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    if (operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP) {
        runtime_transport_nwc24_context.expected_generation = runtime_transport_pending_generation;
        runtime_transport_nwc24_context.completion_generation = 0;
        runtime_transport_nwc24_context.completion_flag = 0;
        runtime_transport_nwc24_context.completion_result = 0;
        runtime_transport_nwc24_context.callback_entry_count = 0;
        runtime_transport_nwc24_context.callback_exit_count = 0;
        runtime_transport_nwc24_context.stale_callback_count = 0;
        runtime_transport_nwc24_context.duplicate_callback_count = 0;
    } else {
        runtime_transport_startup_context.expected_generation = runtime_transport_pending_generation;
        runtime_transport_startup_context.completion_generation = 0;
        runtime_transport_startup_context.completion_flag = 0;
        runtime_transport_startup_context.completion_result = 0;
        runtime_transport_startup_context.callback_entry_count = 0;
        runtime_transport_startup_context.callback_exit_count = 0;
        runtime_transport_startup_context.stale_callback_count = 0;
        runtime_transport_startup_context.duplicate_callback_count = 0;
    }
    result = runtime_call_retail_ios_ioctl_async(
        fd,
        (u32)ioctl,
        (const void*)buffer_in,
        (u32)len_in,
        (void*)buffer_io,
        (u32)len_io,
        runtime_ios_callback,
        operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP
            ? (void*)&runtime_transport_nwc24_context : (void*)&runtime_transport_startup_context
    );
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_record_submit_evidence(operation, result, runtime_transport_pending_generation);
    runtime_diag_record_submit_return(result);
    if (result < 0) {
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        return result;
    }
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
    if (runtime_transport_callback_generation != runtime_transport_pending_generation) {
        runtime_transport_rejected_callback_count += 1;
        return -1;
    }
    if (
        runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_BIND_SOCKET
    ) {
        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET) {
            runtime_cache_invalidate(runtime_transport_socket_params, sizeof(runtime_transport_socket_params));
        } else {
            runtime_cache_invalidate(&runtime_transport_bind_params, sizeof(runtime_transport_bind_params));
        }
    }
    runtime_record_operation_callback();
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
    return 0;
}

static void runtime_record_init_error(s32 result)
{
    runtime_transport_last_error = result;
    runtime_transport_last_ios_result = result;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FAILED, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
}

static void runtime_record_socket_error(s32 result)
{
    runtime_transport_last_socket_error = result;
    runtime_transport_last_error = result;
    runtime_transport_last_ios_result = result;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FAILED, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
}

static void runtime_record_operation_callback(void)
{
    runtime_record_callback_evidence(
        runtime_transport_pending_operation,
        runtime_transport_last_ios_result,
        runtime_transport_callback_generation
    );
    if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_OPEN_KD) {
        runtime_transport_open_kd_callback_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP) {
        runtime_transport_nwc24_callback_count += 1;
        runtime_transport_nwc24_callback_result = runtime_transport_last_ios_result;
        runtime_transport_nwc24_output_digest = runtime_digest_words(runtime_transport_nwc24_output_buffer, 0x20);
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CLOSE_KD) {
        runtime_transport_kd_close_callback_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_OPEN_IP) {
        runtime_transport_open_ip_callback_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_STARTUP) {
        runtime_transport_startup_callback_count += 1;
        runtime_transport_startup_service_started_after_completion = runtime_transport_service_started;
        runtime_transport_ip_fd_after_startup = runtime_transport_ip_fd;
        runtime_transport_startup_pending_after_completion = runtime_transport_pending_operation;
        runtime_transport_startup_phase_after_completion = runtime_transport_phase;
        if (runtime_transport_last_ios_result == 0) {
            runtime_transport_service_started = 1;
            runtime_transport_startup_service_started_after_completion = runtime_transport_service_started;
        }
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_GETHOSTID) {
        runtime_transport_get_host_id_callback_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET) {
        runtime_transport_socket_callback_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET) {
        runtime_transport_bind_callback_count += 1;
    }
}

static void runtime_record_submit_evidence(u32 operation, s32 result, u32 generation)
{
    if (operation == RUNTIME_TRANSPORT_OP_OPEN_KD) {
        runtime_transport_open_kd_submit_result = result;
        runtime_transport_open_kd_submit_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP) {
        runtime_transport_nwc24_synchronous_result = result;
        runtime_transport_nwc24_submit_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_CLOSE_KD) {
        runtime_transport_kd_close_submit_result = result;
        runtime_transport_kd_close_submit_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_OPEN_IP) {
        runtime_transport_open_ip_submit_result = result;
        runtime_transport_open_ip_submit_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_STARTUP) {
        runtime_transport_startup_submit_result = result;
        runtime_transport_startup_submit_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_GETHOSTID) {
        runtime_transport_get_host_id_submit_result = result;
        runtime_transport_get_host_id_submit_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET) {
        runtime_transport_socket_submit_result = result;
        runtime_transport_socket_submit_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET) {
        runtime_transport_bind_submit_result = result;
        runtime_transport_bind_submit_generation = generation;
    }
}

static void runtime_record_callback_evidence(u32 operation, s32 result, u32 generation)
{
    if (operation == RUNTIME_TRANSPORT_OP_OPEN_KD) {
        runtime_transport_open_kd_callback_result = result;
        runtime_transport_open_kd_callback_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP) {
        runtime_transport_nwc24_callback_result = result;
        runtime_transport_nwc24_callback_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_CLOSE_KD) {
        runtime_transport_kd_close_callback_result = result;
        runtime_transport_kd_close_callback_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_OPEN_IP) {
        runtime_transport_open_ip_callback_result = result;
        runtime_transport_open_ip_callback_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_STARTUP) {
        runtime_transport_startup_callback_result = result;
        runtime_transport_startup_callback_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_GETHOSTID) {
        runtime_transport_get_host_id_callback_result = result;
        runtime_transport_get_host_id_callback_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET) {
        runtime_transport_socket_callback_result = result;
        runtime_transport_socket_callback_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET) {
        runtime_transport_bind_callback_result = result;
        runtime_transport_bind_callback_generation = generation;
    }
}

static void runtime_sync_open_ip_context_evidence(void)
{
    runtime_transport_open_ip_callback_exit_count = runtime_transport_open_ip_context.callback_exit_count;
    runtime_transport_open_ip_stale_callback_count = runtime_transport_open_ip_context.stale_callback_count;
    runtime_transport_open_ip_duplicate_callback_count = runtime_transport_open_ip_context.duplicate_callback_count;
}

static void runtime_sync_startup_context_evidence(void)
{
    runtime_transport_startup_callback_exit_count = runtime_transport_startup_context.callback_exit_count;
    runtime_transport_startup_stale_callback_count = runtime_transport_startup_context.stale_callback_count;
    runtime_transport_startup_duplicate_callback_count = runtime_transport_startup_context.duplicate_callback_count;
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
    runtime_memzero(runtime_abi_probe_supplied_args, sizeof(runtime_abi_probe_supplied_args));
    runtime_memzero(runtime_abi_probe_pre_call_args, sizeof(runtime_abi_probe_pre_call_args));
    runtime_memzero(runtime_abi_probe_target_args, sizeof(runtime_abi_probe_target_args));
    runtime_abi_probe_return_value = 0;
    runtime_abi_probe_result_flags = 0;
    runtime_abi_probe_stack_pointer_before = 0;
    runtime_abi_probe_stack_pointer_after = 0;
    runtime_abi_probe_saved_lr = 0;
    runtime_abi_probe_restored_lr = 0;
    runtime_abi_probe_saved_r2 = 0;
    runtime_abi_probe_restored_r2 = 0;
    runtime_abi_probe_saved_r13 = 0;
    runtime_abi_probe_restored_r13 = 0;
    runtime_abi_probe_target_ctr = 0;
    runtime_abi_probe_after_call_flag = 0;
    runtime_transport_last_error = 0;
    runtime_transport_last_socket_error = 0;
    runtime_transport_last_ios_result = 0;
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
    runtime_transport_pending_generation = 0;
    runtime_transport_callback_generation = 0;
    runtime_transport_callback_count = 0;
    runtime_transport_rejected_callback_count = 0;
    runtime_transport_callback_pending = 0;
    runtime_transport_open_kd_submit_count = 0;
    runtime_transport_open_kd_callback_count = 0;
    runtime_transport_open_kd_submit_result = 0;
    runtime_transport_open_kd_callback_result = 0;
    runtime_transport_open_kd_submit_generation = 0;
    runtime_transport_open_kd_callback_generation = 0;
    runtime_transport_nwc24_submit_count = 0;
    runtime_transport_nwc24_callback_count = 0;
    runtime_transport_nwc24_synchronous_result = 0;
    runtime_transport_nwc24_callback_result = 0;
    runtime_transport_nwc24_output_digest = 0;
    runtime_transport_nwc24_submit_generation = 0;
    runtime_transport_nwc24_callback_generation = 0;
    runtime_transport_open_ip_submit_count = 0;
    runtime_transport_open_ip_callback_count = 0;
    runtime_transport_open_ip_submit_result = 0;
    runtime_transport_open_ip_callback_result = 0;
    runtime_transport_open_ip_submit_generation = 0;
    runtime_transport_open_ip_callback_generation = 0;
    runtime_transport_open_ip_path_pointer = 0;
    runtime_transport_open_ip_path_length = 0;
    runtime_transport_open_ip_mode_value = 0;
    runtime_transport_open_ip_callback_pointer = 0;
    runtime_transport_open_ip_context_pointer = 0;
    runtime_transport_open_ip_callback_exit_count = 0;
    runtime_transport_open_ip_stale_callback_count = 0;
    runtime_transport_open_ip_duplicate_callback_count = 0;
    runtime_transport_ip_fd_before_open_ip = -1;
    runtime_transport_kd_close_submit_count = 0;
    runtime_transport_kd_close_callback_count = 0;
    runtime_transport_kd_close_submit_result = 0;
    runtime_transport_kd_close_callback_result = 0;
    runtime_transport_kd_close_submit_generation = 0;
    runtime_transport_kd_close_callback_generation = 0;
    runtime_transport_kd_close_submitted_fd = -1;
    runtime_transport_kd_fd_before_close = -1;
    runtime_transport_kd_fd_after_close = -1;
    runtime_transport_ip_close_submit_count = 0;
    runtime_transport_socket_close_submit_count = 0;
    runtime_transport_startup_submit_count = 0;
    runtime_transport_startup_callback_count = 0;
    runtime_transport_startup_submit_result = 0;
    runtime_transport_startup_callback_result = 0;
    runtime_transport_startup_submit_generation = 0;
    runtime_transport_startup_callback_generation = 0;
    runtime_transport_startup_target_address = 0;
    runtime_transport_startup_command = 0;
    runtime_transport_startup_submitted_fd = -1;
    runtime_transport_startup_callback_pointer = 0;
    runtime_transport_startup_context_pointer = 0;
    runtime_transport_startup_callback_exit_count = 0;
    runtime_transport_startup_stale_callback_count = 0;
    runtime_transport_startup_duplicate_callback_count = 0;
    runtime_transport_startup_service_started_before_submit = 0;
    runtime_transport_startup_service_started_after_completion = 0;
    runtime_transport_ip_fd_before_startup = -1;
    runtime_transport_ip_fd_after_startup = -1;
    runtime_transport_startup_pending_before_submit = 0;
    runtime_transport_startup_pending_after_completion = 0;
    runtime_transport_startup_phase_before_submit = 0;
    runtime_transport_startup_phase_after_completion = 0;
    runtime_memzero(runtime_transport_startup_pre_call_args, sizeof(runtime_transport_startup_pre_call_args));
    runtime_transport_get_host_id_submit_count = 0;
    runtime_transport_get_host_id_callback_count = 0;
    runtime_transport_get_host_id_submit_result = 0;
    runtime_transport_get_host_id_callback_result = 0;
    runtime_transport_get_host_id_submit_generation = 0;
    runtime_transport_get_host_id_callback_generation = 0;
    runtime_transport_socket_submit_count = 0;
    runtime_transport_socket_callback_count = 0;
    runtime_transport_socket_submit_result = 0;
    runtime_transport_socket_callback_result = 0;
    runtime_transport_socket_submit_generation = 0;
    runtime_transport_socket_callback_generation = 0;
    runtime_transport_bind_submit_count = 0;
    runtime_transport_bind_callback_count = 0;
    runtime_transport_bind_submit_result = 0;
    runtime_transport_bind_callback_result = 0;
    runtime_transport_bind_submit_generation = 0;
    runtime_transport_bind_callback_generation = 0;
    runtime_transport_kd_fd = -1;
    runtime_transport_kd_closed = 0;
    runtime_transport_ip_fd = -1;
    runtime_transport_socket_fd = -1;
    runtime_transport_host_id = 0;
    runtime_transport_service_started = 0;
    runtime_transport_bound_port = RUNTIME_UDP_PORT;
    runtime_transport_receive_submit_count = 0;
    runtime_transport_send_submit_count = 0;
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
    runtime_memzero(runtime_transport_last_receive_preview, sizeof(runtime_transport_last_receive_preview));
    runtime_memzero(runtime_transport_last_send_preview, sizeof(runtime_transport_last_send_preview));
    runtime_memzero(runtime_transport_nwc24_output_buffer, sizeof(runtime_transport_nwc24_output_buffer));
    runtime_memzero(&runtime_transport_nwc24_context, sizeof(runtime_transport_nwc24_context));
    runtime_memzero(&runtime_transport_kd_close_context, sizeof(runtime_transport_kd_close_context));
    runtime_memzero(&runtime_transport_open_ip_context, sizeof(runtime_transport_open_ip_context));
    runtime_memzero(&runtime_transport_startup_context, sizeof(runtime_transport_startup_context));
    runtime_memzero(runtime_transport_socket_params, sizeof(runtime_transport_socket_params));
    runtime_memzero(&runtime_transport_bind_params, sizeof(runtime_transport_bind_params));
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

    if (
        runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SO_STARTED
    ) {
        runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
        goto runtime_poll_exit;
    }
    if (runtime_transport_is_dry_run_mode()) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_is_ioctl_async_abi_probe_mode()) {
        (void)runtime_run_retail_veneer_selftest();
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
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_BIND_SOCKET
    ) {
        s32 wait_result = runtime_wait_completion();
        if (wait_result != 0) {
            if (wait_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
            }
            goto runtime_poll_exit;
        }

        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_KD) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_kd_fd = runtime_transport_last_ios_result;
            runtime_transport_kd_closed = 0;
            if (runtime_transport_is_open_kd_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_NWC24_STARTUP, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP) {
            if (runtime_transport_is_nwc24_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_KD, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_KD) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_kd_fd = -1;
            runtime_transport_kd_closed = 1;
            runtime_transport_kd_fd_after_close = runtime_transport_kd_fd;
            if (runtime_transport_is_close_kd_once_mode() || runtime_transport_is_nwc24_close_kd_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_OPEN_IP, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_IP) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_ip_fd = runtime_transport_last_ios_result;
            if (runtime_transport_is_open_ip_once_mode() || runtime_transport_is_nwc24_close_open_ip_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SO_STARTUP, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_socket_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_service_started = 1;
            runtime_transport_startup_service_started_after_completion = runtime_transport_service_started;
            runtime_transport_ip_fd_after_startup = runtime_transport_ip_fd;
            runtime_transport_startup_pending_after_completion = runtime_transport_pending_operation;
            runtime_transport_startup_phase_after_completion = runtime_transport_phase;
            if (runtime_transport_is_nwc24_close_open_ip_startup_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SO_STARTED, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            if (runtime_transport_is_startup_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_GETHOSTID, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_GETHOSTID) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_socket_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_host_id = (u32)runtime_transport_last_ios_result;
            if (runtime_transport_host_id == 0) {
                runtime_record_socket_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            if (runtime_transport_is_get_host_id_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CREATE_SOCKET, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_socket_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_socket_fd = runtime_transport_last_ios_result;
            if (runtime_transport_is_create_socket_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_BIND_SOCKET, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_BIND_SOCKET) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_socket_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_bound_port = RUNTIME_UDP_PORT;
            if (runtime_transport_is_bind_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_BOUND_NO_RECV, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
            goto runtime_poll_exit;
        }
    }

    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_OPEN_KD) {
        runtime_transport_open_kd_submit_count += 1;
        if (
            runtime_submit_open(
                runtime_kd_path,
                RUNTIME_TRANSPORT_OP_OPEN_KD,
                RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_KD
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NWC24_STARTUP) {
        ((volatile u32*)runtime_transport_nwc24_output_buffer)[0] = 0x4E574332U;
        ((volatile u32*)runtime_transport_nwc24_output_buffer)[1] = 0x34535441U;
        ((volatile u32*)runtime_transport_nwc24_output_buffer)[2] = 0x52545550U;
        ((volatile u32*)runtime_transport_nwc24_output_buffer)[3] = 0x50415454U;
        ((volatile u32*)runtime_transport_nwc24_output_buffer)[4] = 0x45524E21U;
        ((volatile u32*)runtime_transport_nwc24_output_buffer)[5] = 0x4E574332U;
        ((volatile u32*)runtime_transport_nwc24_output_buffer)[6] = 0x34535441U;
        ((volatile u32*)runtime_transport_nwc24_output_buffer)[7] = 0x52545550U;
        runtime_transport_nwc24_submit_count += 1;
        if (
            runtime_submit_ioctl(
                runtime_transport_kd_fd,
                IOCTL_NWC24_STARTUP,
                0,
                0,
                runtime_transport_nwc24_output_buffer,
                0x20,
                RUNTIME_TRANSPORT_OP_NWC24_STARTUP,
                RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CLOSE_KD) {
        runtime_transport_kd_close_submit_count += 1;
        if (
            runtime_submit_close(
                runtime_transport_kd_fd,
                RUNTIME_TRANSPORT_OP_CLOSE_KD,
                RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_KD
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_OPEN_IP) {
        runtime_transport_open_ip_submit_count += 1;
        if (
            runtime_submit_open(
                runtime_ip_path,
                RUNTIME_TRANSPORT_OP_OPEN_IP,
                RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_IP
            ) < 0
        ) {
            runtime_record_init_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SO_STARTUP) {
        runtime_transport_startup_submit_count += 1;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_STARTUP,
                0,
                0,
                0,
                0,
                RUNTIME_TRANSPORT_OP_STARTUP,
                RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP
            ) < 0
        ) {
            runtime_record_socket_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_GETHOSTID) {
        runtime_transport_get_host_id_submit_count += 1;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_GETHOSTID,
                0,
                0,
                0,
                0,
                RUNTIME_TRANSPORT_OP_GETHOSTID,
                RUNTIME_TRANSPORT_PHASE_WAIT_GETHOSTID
            ) < 0
        ) {
            runtime_record_socket_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CREATE_SOCKET) {
        runtime_transport_socket_params[0] = AF_INET;
        runtime_transport_socket_params[1] = SOCK_DGRAM;
        runtime_transport_socket_params[2] = IPPROTO_IP;
        runtime_transport_socket_submit_count += 1;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_SOCKET,
                runtime_transport_socket_params,
                sizeof(runtime_transport_socket_params),
                0,
                0,
                RUNTIME_TRANSPORT_OP_CREATE_SOCKET,
                RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET
            ) < 0
        ) {
            runtime_record_socket_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_BIND_SOCKET) {
        runtime_memzero(&runtime_transport_bind_params, sizeof(runtime_transport_bind_params));
        runtime_transport_bind_params.socket = (u32)runtime_transport_socket_fd;
        runtime_transport_bind_params.has_name = 1;
        runtime_copy_sockaddr_in(
            runtime_transport_bind_params.name,
            INADDR_ANY,
            runtime_bswap16((u16)RUNTIME_UDP_PORT)
        );
        runtime_transport_bind_submit_count += 1;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_BIND,
                &runtime_transport_bind_params,
                sizeof(runtime_transport_bind_params),
                0,
                0,
                RUNTIME_TRANSPORT_OP_BIND_SOCKET,
                RUNTIME_TRANSPORT_PHASE_WAIT_BIND_SOCKET
            ) < 0
        ) {
            runtime_record_socket_error(runtime_transport_last_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_BOUND_NO_RECV) {
        runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SO_STARTED) {
        runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
        goto runtime_poll_exit;
    }

runtime_poll_exit:
    runtime_last_transport_phase_after_step = runtime_transport_phase;
    if (state_machine_entered != 0) {
        runtime_diag_increment(&runtime_state_machine_exit_count);
    }
    return;
}
