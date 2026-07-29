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

#ifndef PRIME3_CP3W_GAME_IDENTITY_COMMAND
#define PRIME3_CP3W_GAME_IDENTITY_COMMAND 5
#endif
#ifndef PRIME3_CP3W_GAME_IDENTITY_CAPABILITY
#define PRIME3_CP3W_GAME_IDENTITY_CAPABILITY (1 << 11)
#endif
#ifndef PRIME3_CP3W_GAME_IDENTITY_SCHEMA_VERSION
#define PRIME3_CP3W_GAME_IDENTITY_SCHEMA_VERSION 1
#endif
#ifndef PRIME3_CP3W_GAME_IDENTITY_PROFILE_ID
#define PRIME3_CP3W_GAME_IDENTITY_PROFILE_ID 0x50334E41
#endif
#ifndef PRIME3_CP3W_GAME_IDENTITY_PROFILE_FINGERPRINT
#define PRIME3_CP3W_GAME_IDENTITY_PROFILE_FINGERPRINT 0x67B00CE6
#endif
#ifndef PRIME3_CP3W_RUNTIME_BUILD_ID
#define PRIME3_CP3W_RUNTIME_BUILD_ID 0x50335731
#endif
#ifndef ENABLE_TCP_DIAGNOSTICS
#define ENABLE_TCP_DIAGNOSTICS 0
#endif

typedef signed int s32;
typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;

typedef struct runtime_cp3c_config {
    u32 magic;
    u16 version;
    u16 size;
    u32 flags;
    u32 server_ipv4;
    u16 server_port;
    u16 reserved;
    u32 reserved_words[3];
} runtime_cp3c_config;

typedef struct runtime_ioctlv {
    void* data;
    u32 len;
} runtime_ioctlv;

typedef struct runtime_connect_params {
    u32 socket;
    u32 has_addr;
    u8 address[8];
    u8 reserved[20];
} runtime_connect_params;

typedef struct runtime_sendto_params {
    u32 socket;
    u32 flags;
    u32 has_destaddr;
    u8 destaddr[28];
} runtime_sendto_params;

typedef struct runtime_socket_request {
    u32 family;
    u32 type;
    u32 protocol;
    u8 reserved[0x20 - 12];
} runtime_socket_request;

typedef struct runtime_receive_request {
    s32 socket;
    u32 flags;
} runtime_receive_request;

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

typedef struct runtime_protocol_queue_slot {
    u32 occupied;
    u32 message_type;
    u32 sequence;
    u8 frame[64];
} runtime_protocol_queue_slot;

typedef struct runtime_send13_diagnostic {
    u32 magic;
    u32 phase_before;
    u32 phase_after;
    s32 submit_result;
    u32 callback_invoked;
    s32 callback_result;
    u32 pending_operation;
    u32 callback_generation;
    u32 userdata_valid;
    s32 ip_fd;
    s32 socket_fd;
    u32 args[7];
    u32 vector0_address;
    u32 vector0_length;
    u32 vector1_address;
    u32 vector1_length;
    u32 request_address;
    u8 request_bytes[40];
    u8 payload_bytes[16];
} runtime_send13_diagnostic;

typedef struct runtime_network_diagnostics {
    u32 magic;
    u32 version;
    u32 size;
    u32 build_id;
    u32 current_phase;
    u32 previous_phase;
    u32 transition_count;
    u32 ios_version;
    u32 ios_revision;
    u32 initialization_attempt_count;
    u32 successful_initialization_count;
    u32 restart_request_count;
    u32 socket_recovery_count;
    u32 initial_delay_polls;
    u32 retry_delay_polls;
    s32 network_initialization_result;
    s32 nwc24_result;
    s32 host_id_result;
    u32 host_ip;
    s32 socket_descriptor;
    s32 socket_creation_result;
    s32 bind_result;
    s32 getsockname_result;
    s32 last_socket_error;
    u32 last_error_phase;
    u32 requested_bind_address;
    u32 requested_bind_port;
    u32 actual_bind_address;
    u32 actual_bind_port;
    u32 byte_order_applied;
    u32 listening;
    u32 receive_loop_active;
    u32 receive_call_count;
    u32 packets_received;
    u32 malformed_packets_received;
    u32 transient_receive_errors;
    u32 fatal_receive_errors;
    u32 send_call_count;
    u32 packets_sent;
    u32 send_failures;
    u32 close_call_count;
    u32 shutdown_call_count;
    u32 cleanup_call_count;
    u32 network_device_close_count;
    s32 last_close_descriptor;
    s32 last_shutdown_descriptor;
    u32 last_received_command;
    u32 last_received_packet_size;
    u32 last_sender_ip;
    u32 last_sender_port;
    s32 last_heartbeat_result;
    u32 uptime_polls;
    u32 last_successful_bind_poll;
    u32 last_packet_receive_poll;
    u32 last_packet_send_poll;
    u32 restart_request;
    u32 heartbeat_request;
    u32 overlay_enabled;
    u32 overlay_page;
    u32 auto_retry_enabled;
    u32 reset_counters_request;
    u32 socket_lost_count;
    u32 getsockname_call_count;
    u32 receive_loop_iteration_count;
} runtime_network_diagnostics;

typedef char runtime_network_diagnostics_size_must_be_0x100[
    sizeof(runtime_network_diagnostics) == 0x100 ? 1 : -1
];

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
    RUNTIME_TRANSPORT_PHASE_HOST_ID_READY = 19,
    RUNTIME_TRANSPORT_PHASE_SOCKET_READY = 20,
    RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE = 21,
    RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_SOCKET_AFTER_BIND_FAILURE = 22,
    RUNTIME_TRANSPORT_PHASE_BIND_FAILED_CLEANED = 23,
    RUNTIME_TRANSPORT_PHASE_FAILED_SOCKET_LEAK = 24,
    RUNTIME_TRANSPORT_PHASE_SUBMIT_RECEIVE_ONCE = 25,
    RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE = 26,
    RUNTIME_TRANSPORT_PHASE_RECEIVED_DATAGRAM = 27,
    RUNTIME_TRANSPORT_PHASE_RECEIVE_SUBMIT_FAILED = 28,
    RUNTIME_TRANSPORT_PHASE_RECEIVE_ASYNC_FAILED = 29,
    RUNTIME_TRANSPORT_PHASE_RECEIVE_INVALID_POSITIVE = 30,
    RUNTIME_TRANSPORT_PHASE_RECEIVE_OVERSIZED_RESULT = 31,
    RUNTIME_TRANSPORT_PHASE_RECEIVE_STALE_CALLBACK = 32,
    RUNTIME_TRANSPORT_PHASE_RECEIVE_DUPLICATE_CALLBACK = 33,
    RUNTIME_TRANSPORT_PHASE_RECEIVE_CLEANUP_DEFERRED = 34,
    RUNTIME_TRANSPORT_PHASE_SUBMIT_SEND_ONCE = 35,
    RUNTIME_TRANSPORT_PHASE_WAIT_SEND = 36,
    RUNTIME_TRANSPORT_PHASE_SENT_DATAGRAM = 37,
    RUNTIME_TRANSPORT_PHASE_SEND_SUBMIT_FAILED = 38,
    RUNTIME_TRANSPORT_PHASE_SEND_ASYNC_FAILED = 39,
    RUNTIME_TRANSPORT_PHASE_SEND_INVALID_POSITIVE = 40,
    RUNTIME_TRANSPORT_PHASE_SEND_STALE_CALLBACK = 41,
    RUNTIME_TRANSPORT_PHASE_SEND_DUPLICATE_CALLBACK = 42,
    RUNTIME_TRANSPORT_PHASE_SEND_CLEANUP_DEFERRED = 43,
    RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE = 44,
    RUNTIME_TRANSPORT_PHASE_LOOP_COMPLETE = 45,
    RUNTIME_TRANSPORT_PHASE_REARM_SUBMIT_FAILED = 46,
    RUNTIME_TRANSPORT_PHASE_REARM_INVALID_STATE = 47,
    RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID = 48,
    RUNTIME_TRANSPORT_PHASE_EXCHANGE_COUNTER_OVERFLOW = 49,
    RUNTIME_TRANSPORT_PHASE_CP3W_VALIDATE_FRAME = 50,
    RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_VALID = 51,
    RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_REJECTED = 52,
    RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_RESPONSE = 53,
    RUNTIME_TRANSPORT_PHASE_CP3W_WAIT_RESPONSE = 54,
    RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_LOOP_COMPLETE = 55,
    RUNTIME_TRANSPORT_PHASE_CP3W_DISPATCH_REQUEST = 56,
    RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_PING = 57,
    RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_UNSUPPORTED_COMMAND = 58,
    RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE = 59,
    RUNTIME_TRANSPORT_PHASE_CP3W_WAIT_DISPATCH_RESPONSE = 60,
    RUNTIME_TRANSPORT_PHASE_CP3W_PING_PONG_LOOP_COMPLETE = 61,
    RUNTIME_TRANSPORT_PHASE_CP3W_PROCESS_HELLO = 62,
    RUNTIME_TRANSPORT_PHASE_CP3W_NEGOTIATE_HELLO_VERSION = 63,
    RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_HELLO_SUCCESS = 64,
    RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_HELLO_REJECTED = 65,
    RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_DUPLICATE_HELLO = 66,
    RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_RENEGOTIATION_REJECTED = 67,
    RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_NOT_NEGOTIATED = 68,
    RUNTIME_TRANSPORT_PHASE_CP3W_HELLO_SESSION_LOOP_COMPLETE = 69,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_VALIDATE_REQUEST = 70,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_VALIDATE_CAPABILITY = 71,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_VALIDATE_EXECUTABLE = 72,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_RESOLVE_GAME_STATE = 73,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_RESOLVE_PLAYER_STATE = 74,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_BUILD_RESPONSE = 75,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_SUBMIT_RESPONSE = 76,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_RESPONSE_COMPLETE = 77,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_HANDLE_ERROR = 78,
    RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_LOOP_COMPLETE = 79,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_VALIDATE_REQUEST = 80,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_VALIDATE_CAPABILITY = 81,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_VALIDATE_IDENTITY = 82,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_RESOLVE_GAME_STATE = 83,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_RESOLVE_ROOT = 84,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_VALIDATE_RANGE = 85,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_READ_RECORDS = 86,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_REVALIDATE_ROOT = 87,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_BUILD_RESPONSE = 88,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_SUBMIT_RESPONSE = 89,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_RESPONSE_COMPLETE = 90,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_HANDLE_UNAVAILABLE = 91,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_HANDLE_ERROR = 92,
    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_LOOP_COMPLETE = 93,
    RUNTIME_TRANSPORT_PHASE_WAIT_NETWORK_READY = 94,
    RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_READY = 95,
    RUNTIME_TRANSPORT_PHASE_INITIAL_DELAY = 96,
    RUNTIME_TRANSPORT_PHASE_VERIFY_BOUND_ENDPOINT = 97,
    RUNTIME_TRANSPORT_PHASE_WAIT_VERIFY_BOUND_ENDPOINT = 98,
    RUNTIME_TRANSPORT_PHASE_LISTENING = 99,
    RUNTIME_TRANSPORT_PHASE_RETRY_DELAY = 100,
    RUNTIME_TRANSPORT_PHASE_RESTART_REQUESTED = 101,
    RUNTIME_TRANSPORT_PHASE_SOCKET_LOST = 102,
    RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_FOR_RECOVERY = 103,
    RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_SOCKET_FOR_RECOVERY = 104,
    RUNTIME_TRANSPORT_PHASE_SUBMIT_HEARTBEAT = 105,
    RUNTIME_TRANSPORT_PHASE_WAIT_HEARTBEAT = 106,
    RUNTIME_TRANSPORT_PHASE_FATAL_ERROR = 107,
    RUNTIME_TRANSPORT_PHASE_NATIVE_BOOTSTRAP = 108,
    RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_HOST_ID = 109,
    RUNTIME_TRANSPORT_PHASE_NATIVE_HOST_ID_TIMEOUT = 110,
    RUNTIME_TRANSPORT_PHASE_NATIVE_CREATE_BEACON_SOCKET = 111,
    RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON_INTERVAL = 112,
    RUNTIME_TRANSPORT_PHASE_NATIVE_SUBMIT_BEACON = 113,
    RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON = 114,
    RUNTIME_TRANSPORT_PHASE_NATIVE_BEACON_COMPLETE = 115,
    RUNTIME_TRANSPORT_PHASE_CONNECT_TCP = 116,
    RUNTIME_TRANSPORT_PHASE_WAIT_CONNECT_TCP = 117,
    RUNTIME_TRANSPORT_PHASE_SEND_TCP_HELLO = 118,
    RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_HELLO = 119,
    RUNTIME_TRANSPORT_PHASE_RECEIVE_TCP_ACK = 120,
    RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE_TCP_ACK = 121,
    RUNTIME_TRANSPORT_PHASE_TCP_ESTABLISHED = 122,
    RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_TEST = 123,
    RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST = 124,
    RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_ALT1 = 125,
    RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_ALT1 = 126,
    RUNTIME_TRANSPORT_PHASE_WAIT_TCP_SEND_OUTCOME_CLOSE = 127,
    RUNTIME_TRANSPORT_PHASE_PREPARE_FRAME = 128,
    RUNTIME_TRANSPORT_PHASE_SEND_FRAME_SYNC = 129,
    RUNTIME_TRANSPORT_PHASE_WAIT_INTERVAL = 130,
    RUNTIME_TRANSPORT_PHASE_SUBMIT_ECHO_RECV = 131,
    RUNTIME_TRANSPORT_PHASE_WAIT_ECHO_RECV = 132,
    RUNTIME_TRANSPORT_PHASE_VALIDATE_ECHO = 133,
    RUNTIME_TRANSPORT_PHASE_DISCONNECTED = 134,
    RUNTIME_TRANSPORT_PHASE_CONNECTED = 135,
    RUNTIME_TRANSPORT_PHASE_QUEUE_CLIENT_HELLO = 136,
    RUNTIME_TRANSPORT_PHASE_SEND_QUEUED_FRAME = 137,
    RUNTIME_TRANSPORT_PHASE_RECEIVE_FRAME = 138,
    RUNTIME_TRANSPORT_PHASE_VALIDATE_FRAME = 139,
    RUNTIME_TRANSPORT_PHASE_WAIT_SERVER_HELLO_ACK = 140,
    RUNTIME_TRANSPORT_PHASE_QUEUE_CLIENT_TEST = 141,
    RUNTIME_TRANSPORT_PHASE_WAIT_SERVER_TEST = 142,
    RUNTIME_TRANSPORT_PHASE_ESTABLISHED = 143,
    RUNTIME_TRANSPORT_PHASE_PREPARE_TRACKER_SNAPSHOT = 144,
    RUNTIME_TRANSPORT_PHASE_WAIT_TRACKER_ACK = 145,
    RUNTIME_TRANSPORT_PHASE_TRACKING = 146,
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
    RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE = 9,
    RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET = 10,
    RUNTIME_TRANSPORT_OP_SEND_SOCKET = 11,
    RUNTIME_TRANSPORT_OP_GETSOCKNAME = 12,
    RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_FOR_RECOVERY = 13,
    RUNTIME_TRANSPORT_OP_TCP_SEND = 14,
    RUNTIME_TRANSPORT_OP_TCP_ECHO_RECEIVE = 15,
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
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_RECVFROM_ONCE = 14,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_RECV_SEND_ONCE = 15,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_RECV_SEND_LOOP = 16,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_FRAME_VALIDATION = 17,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_PING_PONG = 18,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_HELLO_SESSION = 19,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_GAME_IDENTITY = 20,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_INVENTORY = 21,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_INVENTORY_SERVICE = 22,
    RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_NATIVE_WC24_BOOTSTRAP_BEACON_ONCE = 23,
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
    IOCTL_SO_CONNECT = 4,
    IOCTL_SO_CLOSE = 3,
    IOCTL_SO_GETSOCKNAME = 7,
    IOCTLV_SO_RECVFROM = 12,
    IOCTLV_SO_SENDTO = 13,
    IOCTL_SO_SOCKET = 15,
    IOCTL_SO_GETHOSTID = 16,
    IOCTL_SO_STARTUP = 31,
    AF_INET = 2,
    SOCK_STREAM = 1,
    IPPROTO_IP = 0,
    INADDR_ANY = 0,
    RUNTIME_UDP_RECEIVE_CAPACITY = 512,
    RUNTIME_UDP_SEND_CAPACITY = 512,
    RUNTIME_PREVIEW_SIZE = 16,
    RUNTIME_WII_SOCKADDR_IN_SIZE = 8,
    RUNTIME_NETWORK_READY_RETRY_POLL_INTERVAL = 60,
    RUNTIME_NWC24_RETRY_POLL_INTERVAL = 6,
    RUNTIME_NATIVE_HOST_ID_RETRY_POLL_INTERVAL = 30,
    RUNTIME_NATIVE_HOST_ID_ATTEMPT_LIMIT = 20,
    RUNTIME_NATIVE_BEACON_RETRY_POLL_INTERVAL = 30,
    RUNTIME_NATIVE_BEACON_ATTEMPT_LIMIT = 10,
    RUNTIME_NATIVE_INTERVAL_TIMEBASE_TICKS = 30375000,
    RUNTIME_NATIVE_EXECUTION_CANARY = 0x4E415431,
    RUNTIME_NATIVE_POST_COPY_HOOK_ADDRESS = 0x80372460,
    RUNTIME_NATIVE_POST_COPY_HOOK_EXPECTED = 0x80010014,
    RUNTIME_INITIAL_DELAY_POLL_INTERVAL = 300,
    RUNTIME_RETRY_DELAY_POLL_INTERVAL = 120,
    RUNTIME_DIAGNOSTICS_MAGIC = 0x43503344,
    RUNTIME_DIAGNOSTICS_VERSION = 1,
    RUNTIME_DIAGNOSTICS_SIZE = 0x100,
    RUNTIME_VERIFIED_IOS_IOCTL_ASYNC_ADDRESS = 0x80504FE0,
    RUNTIME_SOCKET_REQUEST_LOGICAL_SIZE = 12,
    RUNTIME_RECEIVE_REQUEST_LOGICAL_SIZE = 8,
    RUNTIME_RECEIVE_VECTOR_COUNT = 2,
    RUNTIME_RECEIVE_INPUT_VECTOR_COUNT = 1,
    RUNTIME_RECEIVE_OUTPUT_VECTOR_COUNT = 1,
    RUNTIME_SEND_REQUEST_LOGICAL_SIZE = 40,
    RUNTIME_SEND_VECTOR_COUNT = 2,
    RUNTIME_SEND_INPUT_VECTOR_COUNT = 2,
    RUNTIME_SEND_OUTPUT_VECTOR_COUNT = 0,
    RUNTIME_TCP_FRAME_SIZE = 64,
    RUNTIME_TCP_FRAME_CRC_OFFSET = 60,
    RUNTIME_PROTOCOL_QUEUE_DEPTH = 4,
    RUNTIME_PROTOCOL_MAGIC = 0x43503357,
    RUNTIME_PROTOCOL_VERSION = 1,
    RUNTIME_PROTOCOL_CLIENT_HELLO = 1,
    RUNTIME_PROTOCOL_SERVER_HELLO_ACK = 2,
    RUNTIME_PROTOCOL_CLIENT_TEST = 3,
    RUNTIME_PROTOCOL_SERVER_TEST = 4,
    RUNTIME_PROTOCOL_CP3D_DIAGNOSTIC_REQUEST = 0x10,
    RUNTIME_PROTOCOL_CP3D_DIAGNOSTIC_ECHO = 0x11,
    RUNTIME_PROTOCOL_TRACKER_SNAPSHOT = 0x20,
    RUNTIME_PROTOCOL_TRACKER_DELTA = 0x21,
    RUNTIME_PROTOCOL_TRACKER_ACK = 0x22,
    RUNTIME_PROTOCOL_CAPABILITIES = 0x0F,
    RUNTIME_SEND_PAYLOAD_LENGTH = 29,
    RUNTIME_EXCHANGE_COUNTER_LIMIT_MAX = 100,
    RUNTIME_CP3W_HEADER_SIZE = 16,
    RUNTIME_CP3W_CRC_SIZE = 4,
    RUNTIME_CP3W_PACKET_KIND_REQUEST = 1,
    RUNTIME_CP3W_PACKET_KIND_RESPONSE = 2,
    RUNTIME_CP3W_RESPONSE_STATUS_OK = 0,
    RUNTIME_CP3W_RESPONSE_STATUS_ERROR = 1,
    RUNTIME_CP3W_COMMAND_HELLO = 1,
    RUNTIME_CP3W_COMMAND_READ_MEMORY = 2,
    RUNTIME_CP3W_COMMAND_PING = 3,
    RUNTIME_CP3W_COMMAND_DISCONNECT = 4,
    RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY = PRIME3_CP3W_GAME_IDENTITY_COMMAND,
    RUNTIME_CP3W_COMMAND_GET_INVENTORY = PRIME3_CP3W_INVENTORY_COMMAND,
    RUNTIME_CP3W_COMMAND_RESERVED_MAILBOX = 127,
    RUNTIME_CP3W_SUPPORTED_PROTOCOL_VERSION = 1,
    RUNTIME_CP3W_ERROR_CODE_UNSUPPORTED_VERSION = 3,
    RUNTIME_CP3W_ERROR_CODE_UNKNOWN_COMMAND = 4,
    RUNTIME_CP3W_ERROR_CODE_INVALID_PAYLOAD_LENGTH = 5,
    RUNTIME_CP3W_ERROR_CODE_NOT_NEGOTIATED = 9,
    RUNTIME_CP3W_ERROR_CODE_INVALID_STATE = 10,
    RUNTIME_CP3W_ERROR_CODE_CAPABILITY_NOT_NEGOTIATED = 11,
    RUNTIME_CP3W_HELLO_REQUEST_FIXED_SIZE = 10,
    RUNTIME_CP3W_HELLO_RESPONSE_FIXED_SIZE = 19,
    RUNTIME_CP3W_HELLO_NAME_LENGTH_SIZE = 1,
    RUNTIME_CP3W_HELLO_MAX_NAME_LENGTH = 31,
    RUNTIME_CP3W_HELLO_METADATA_VERSION = 1,
    RUNTIME_CP3W_RUNTIME_BUILD_ID = PRIME3_CP3W_RUNTIME_BUILD_ID,
    RUNTIME_CP3W_CAPABILITY_HELLO_NEGOTIATION = 1,
    RUNTIME_CP3W_CAPABILITY_PING = 1 << 1,
    RUNTIME_CP3W_CAPABILITY_STRUCTURED_ERRORS = 1 << 2,
    RUNTIME_CP3W_CAPABILITY_DETERMINISTIC_SESSION_ID = 1 << 3,
    RUNTIME_CP3W_CAPABILITY_READ_MEMORY = 1 << 4,
    RUNTIME_CP3W_CAPABILITY_GAME_IDENTITY = PRIME3_CP3W_GAME_IDENTITY_CAPABILITY,
    RUNTIME_CP3W_CAPABILITY_INVENTORY_STATE = PRIME3_CP3W_INVENTORY_CAPABILITY,
    RUNTIME_CP3W_RUNTIME_CAPABILITIES = RUNTIME_CP3W_CAPABILITY_HELLO_NEGOTIATION
        | RUNTIME_CP3W_CAPABILITY_PING
        | RUNTIME_CP3W_CAPABILITY_STRUCTURED_ERRORS
        | RUNTIME_CP3W_CAPABILITY_DETERMINISTIC_SESSION_ID,
    RUNTIME_CP3W_GAME_IDENTITY_SCHEMA_VERSION = PRIME3_CP3W_GAME_IDENTITY_SCHEMA_VERSION,
    RUNTIME_CP3W_GAME_ID = 1,
    RUNTIME_CP3W_PLATFORM_ID = 1,
    RUNTIME_CP3W_REGION_ID = 1,
    RUNTIME_CP3W_REVISION_ID = 1,
    RUNTIME_CP3W_PROFILE_ID = PRIME3_CP3W_GAME_IDENTITY_PROFILE_ID,
    RUNTIME_CP3W_PROFILE_FINGERPRINT = PRIME3_CP3W_GAME_IDENTITY_PROFILE_FINGERPRINT,
    RUNTIME_CP3W_GAME_IDENTITY_PAYLOAD_SIZE = 28,
    RUNTIME_CP3W_INVENTORY_SCHEMA_VERSION = PRIME3_CP3W_INVENTORY_SCHEMA_VERSION,
    RUNTIME_CP3W_INVENTORY_RECORD_COUNT = PRIME3_CP3W_INVENTORY_RECORD_COUNT,
    RUNTIME_CP3W_INVENTORY_RECORD_SIZE = PRIME3_CP3W_INVENTORY_RECORD_SIZE,
    RUNTIME_CP3W_INVENTORY_HEADER_SIZE = 12,
    RUNTIME_CP3W_INVENTORY_PAYLOAD_SIZE = PRIME3_CP3W_INVENTORY_PAYLOAD_SIZE,
    RUNTIME_CP3W_AVAILABILITY_EXECUTABLE_RECOGNIZED = 1 << 0,
    RUNTIME_CP3W_AVAILABILITY_GAME_STATE_POINTER_VALID = 1 << 1,
    RUNTIME_CP3W_AVAILABILITY_PLAYER_STATE_POINTER_VALID = 1 << 2,
    RUNTIME_CP3W_AVAILABILITY_INVENTORY_ROOT_AVAILABLE = 1 << 3,
    RUNTIME_CP3W_AVAILABILITY_WORLD_STATE_AVAILABLE = 1 << 4,
    RUNTIME_CP3W_INVENTORY_AVAILABILITY_EXECUTABLE_RECOGNIZED = 1 << 0,
    RUNTIME_CP3W_INVENTORY_AVAILABILITY_GAME_STATE_POINTER_VALID = 1 << 1,
    RUNTIME_CP3W_INVENTORY_AVAILABILITY_ROOT_VALID = 1 << 2,
    RUNTIME_CP3W_INVENTORY_AVAILABILITY_SNAPSHOT_AVAILABLE = 1 << 3,
    RUNTIME_CP3W_INVENTORY_AVAILABILITY_TEMPORARILY_UNAVAILABLE = 1 << 4,
    RUNTIME_CP3W_INVENTORY_AVAILABILITY_CONSISTENCY_PASSED = 1 << 5,
    RUNTIME_CP3W_INVENTORY_AVAILABILITY_INCONSISTENT = 1 << 6,
    RUNTIME_CP3W_INVENTORY_AVAILABILITY_RANGE_VALID = 1 << 7,
    RUNTIME_MEM1_START = 0x80000000,
    RUNTIME_MEM1_END = 0x81800000,
    RUNTIME_PRIME3_NTSC_BUILD_STRING_ADDRESS = 0x805822B0,
    RUNTIME_PRIME3_NTSC_GAME_STATE_POINTER_ADDRESS = 0x8067DC0C,
    RUNTIME_PRIME3_NTSC_CSTATE_MANAGER_GLOBAL_ADDRESS = 0x805C4F70,
    RUNTIME_PRIME3_NTSC_CPLAYER_VTABLE = 0x80592C78,
    RUNTIME_CP3W_ERROR_HEADER_SIZE = 6,
    RUNTIME_CP3W_MAX_PING_PAYLOAD_LENGTH = 44,
};

/* CP3C fields are patched by the production asset manifest in network byte order. */
volatile runtime_cp3c_config runtime_cp3c_config_block __attribute_section_state_aligned_32__ __attribute_used__ = {
    0x43503343, 1, sizeof(runtime_cp3c_config), 0, 0, 43674, 0, {0, 0, 0}
};


#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
enum {
    RUNTIME_NATIVE_STAGE_RELOCATED_INITIALIZED = 1,
    RUNTIME_NATIVE_STAGE_RECURRING_HOOK_ENTERED = 2,
    RUNTIME_NATIVE_STAGE_MODE_RECOGNIZED = 3,
    RUNTIME_NATIVE_STAGE_STARTUP_DELAY = 4,
    RUNTIME_NATIVE_STAGE_BOOTSTRAP_ENTERED = 5,
    RUNTIME_NATIVE_STAGE_BOOTSTRAP_RETURNED = 6,
    RUNTIME_NATIVE_STAGE_HOST_ID = 7,
    RUNTIME_NATIVE_STAGE_SOCKET = 8,
    RUNTIME_NATIVE_STAGE_BEACON_SUBMIT = 9,
    RUNTIME_NATIVE_STAGE_BEACON_COMPLETE = 10,
    RUNTIME_NATIVE_STAGE_TERMINAL_FAILURE = 15,
};
#endif

static const char runtime_kd_path[] __attribute_section_rodata__ = "/dev/net/kd/request";
static const char runtime_ip_path[] __attribute_section_rodata__ = "/dev/net/ip/top";
static const char runtime_send_payload_ascii[RUNTIME_SEND_PAYLOAD_LENGTH + 1] __attribute_section_rodata__ =
    "P3_SENDTO_LOOP_REPLY_20260717";
static const u8 runtime_cp3w_magic[4] __attribute_section_rodata__ = {'C', 'P', '3', 'W'};
static const u8 runtime_heartbeat_prefix[] __attribute_section_rodata__ = "CP3W-DIAG-HEARTBEAT";
static const char runtime_cp3w_request_payload_ascii[] __attribute_section_rodata__ = "P3_FRAME_TEST_20260717";
static const char runtime_cp3w_response_payload_ascii[] __attribute_section_rodata__ = "P3_FRAME_ACK_20260717";
static const char runtime_cp3w_runtime_name_ascii[] __attribute_section_rodata__ = "Prime3 Wii Runtime";
static const char runtime_cp3w_not_negotiated_message_ascii[] __attribute_section_rodata__ =
    "Negotiation required before PING.";
static const char runtime_cp3w_unsupported_version_message_ascii[] __attribute_section_rodata__ =
    "Unsupported protocol version range.";
static const char runtime_cp3w_invalid_state_message_ascii[] __attribute_section_rodata__ =
    "Session is already negotiated.";
static const char runtime_cp3w_unsupported_message_ascii[] __attribute_section_rodata__ = "Command is unsupported";
static const char runtime_cp3w_identity_not_negotiated_message_ascii[] __attribute_section_rodata__ =
    "Negotiation required before GET_GAME_IDENTITY.";
static const char runtime_cp3w_identity_capability_message_ascii[] __attribute_section_rodata__ =
    "GAME_IDENTITY capability was not negotiated.";
static const char runtime_cp3w_identity_invalid_payload_message_ascii[] __attribute_section_rodata__ =
    "GET_GAME_IDENTITY request payload must be empty.";
static const char runtime_cp3w_inventory_not_negotiated_message_ascii[] __attribute_section_rodata__ =
    "Negotiation required before GET_INVENTORY.";
static const char runtime_cp3w_inventory_capability_message_ascii[] __attribute_section_rodata__ =
    "INVENTORY_STATE capability was not negotiated.";
static const char runtime_cp3w_inventory_invalid_payload_message_ascii[] __attribute_section_rodata__ =
    "GET_INVENTORY request payload must be empty.";
static const u8 runtime_cp3w_inventory_item_ids[RUNTIME_CP3W_INVENTORY_RECORD_COUNT]
    __attribute_section_rodata__ = {
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
        40, 41, 42, 44, 45, 46, 48, 49, 50, 51, 52, 62, 63, 64, 65, 66, 67, 68, 69
    };

enum {
    RUNTIME_CP3W_REQUEST_PAYLOAD_LENGTH = sizeof(runtime_cp3w_request_payload_ascii) - 1,
    RUNTIME_CP3W_RESPONSE_PAYLOAD_LENGTH = sizeof(runtime_cp3w_response_payload_ascii) - 1,
    RUNTIME_CP3W_RUNTIME_NAME_LENGTH = sizeof(runtime_cp3w_runtime_name_ascii) - 1,
    RUNTIME_CP3W_NOT_NEGOTIATED_MESSAGE_LENGTH = sizeof(runtime_cp3w_not_negotiated_message_ascii) - 1,
    RUNTIME_CP3W_UNSUPPORTED_VERSION_MESSAGE_LENGTH = sizeof(runtime_cp3w_unsupported_version_message_ascii) - 1,
    RUNTIME_CP3W_INVALID_STATE_MESSAGE_LENGTH = sizeof(runtime_cp3w_invalid_state_message_ascii) - 1,
    RUNTIME_CP3W_UNSUPPORTED_MESSAGE_LENGTH = sizeof(runtime_cp3w_unsupported_message_ascii) - 1,
    RUNTIME_CP3W_IDENTITY_NOT_NEGOTIATED_MESSAGE_LENGTH =
        sizeof(runtime_cp3w_identity_not_negotiated_message_ascii) - 1,
    RUNTIME_CP3W_IDENTITY_CAPABILITY_MESSAGE_LENGTH = sizeof(runtime_cp3w_identity_capability_message_ascii) - 1,
    RUNTIME_CP3W_IDENTITY_INVALID_PAYLOAD_MESSAGE_LENGTH =
        sizeof(runtime_cp3w_identity_invalid_payload_message_ascii) - 1,
    RUNTIME_CP3W_INVENTORY_NOT_NEGOTIATED_MESSAGE_LENGTH =
        sizeof(runtime_cp3w_inventory_not_negotiated_message_ascii) - 1,
    RUNTIME_CP3W_INVENTORY_CAPABILITY_MESSAGE_LENGTH = sizeof(runtime_cp3w_inventory_capability_message_ascii) - 1,
    RUNTIME_CP3W_INVENTORY_INVALID_PAYLOAD_MESSAGE_LENGTH =
        sizeof(runtime_cp3w_inventory_invalid_payload_message_ascii) - 1,
    RUNTIME_CP3W_RESPONSE_PACKET_LENGTH =
        RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_RESPONSE_PAYLOAD_LENGTH + RUNTIME_CP3W_CRC_SIZE,
    RUNTIME_CP3W_ERROR_RESPONSE_PACKET_LENGTH = RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_ERROR_HEADER_SIZE
        + RUNTIME_CP3W_UNSUPPORTED_MESSAGE_LENGTH + RUNTIME_CP3W_CRC_SIZE,
    RUNTIME_CP3W_HELLO_RESPONSE_PAYLOAD_LENGTH = RUNTIME_CP3W_HELLO_RESPONSE_FIXED_SIZE
        + RUNTIME_CP3W_HELLO_NAME_LENGTH_SIZE + RUNTIME_CP3W_RUNTIME_NAME_LENGTH,
};

enum {
    RUNTIME_CP3W_FRAME_RESULT_NONE = 0,
    RUNTIME_CP3W_FRAME_RESULT_VALID = 1,
    RUNTIME_CP3W_FRAME_RESULT_TOO_SHORT = 2,
    RUNTIME_CP3W_FRAME_RESULT_INVALID_MAGIC = 3,
    RUNTIME_CP3W_FRAME_RESULT_INVALID_VERSION = 4,
    RUNTIME_CP3W_FRAME_RESULT_UNSUPPORTED_TYPE = 5,
    RUNTIME_CP3W_FRAME_RESULT_NONZERO_FLAGS = 6,
    RUNTIME_CP3W_FRAME_RESULT_LENGTH_MISMATCH = 7,
    RUNTIME_CP3W_FRAME_RESULT_PAYLOAD_TOO_LARGE = 8,
    RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD = 9,
    RUNTIME_CP3W_FRAME_RESULT_MALFORMED = 10,
};

#ifndef PRIME3_IOS_UDP_DIAGNOSTIC_LOOP_COUNT
#define PRIME3_IOS_UDP_DIAGNOSTIC_LOOP_COUNT 3
#endif

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
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
volatile u32 runtime_native_beacon_ipv4 __attribute_section_state__ __attribute_used__ = PRIME3_NATIVE_BEACON_IPV4;
volatile u32 runtime_native_next_host_id_poll __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_next_host_id_timebase __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_low_level_recovery_active __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_first_valid_host_id_poll __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_next_beacon_poll __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_next_beacon_timebase __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_beacon_attempt_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_beacon_success_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_beacon_submission_failure_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_beacon_completion_failure_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_first_successful_beacon_poll __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_last_successful_beacon_poll __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_native_last_beacon_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_native_last_beacon_completion_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_overlay_top_register __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_overlay_bottom_register __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_overlay_geometry __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_native_overlay_render_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_native_post_copy_hook_result __attribute_section_state__ __attribute_used__ = 0;
#else
#define runtime_native_beacon_ipv4 PRIME3_NATIVE_BEACON_IPV4
#endif
volatile s32 runtime_transport_last_error __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_socket_error __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_ios_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_pending_operation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_pending_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_rejected_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_callback_pending __attribute_section_state__ __attribute_used__ = 0;
volatile runtime_network_diagnostics runtime_network_diagnostics_block
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u32 runtime_transport_retry_deadline __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_error_phase __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_initialization_success_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_restart_request_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_recovery_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_lost_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_getsockname_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_getsockname_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_actual_bound_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_actual_bound_port __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_successful_bind_poll __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_packet_receive_poll __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_packet_send_poll __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_transient_receive_error_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_fatal_receive_error_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_failure_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_close_call_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_close_descriptor __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_last_heartbeat_result __attribute_section_state__ __attribute_used__ = 0;
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
volatile u32 runtime_transport_get_host_id_target_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_command __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_get_host_id_submitted_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_get_host_id_callback_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_context_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_callback_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_stale_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_duplicate_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_service_started_before_submit __attribute_section_state__ __attribute_used__
    = 0;
volatile u32 runtime_transport_get_host_id_service_started_after_completion __attribute_section_state__ __attribute_used__
    = 0;
volatile s32 runtime_transport_ip_fd_before_get_host_id __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_ip_fd_after_get_host_id __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_get_host_id_pending_before_submit __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_pending_after_completion __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_phase_before_submit __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_phase_after_completion __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_get_host_id_pre_call_args[8] __attribute_section_state_aligned_32__ __attribute_used__
    = {0};
volatile u32 runtime_transport_socket_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_socket_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_socket_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_target_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_command __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_socket_submitted_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_socket_callback_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_context_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_callback_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_stale_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_duplicate_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_socket_fd_before_submit __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_socket_fd_after_completion __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_socket_request_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_request_storage_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_request_logical_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_request_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_family_value __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_type_value __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_protocol_value __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_descriptor_valid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_ready __attribute_section_state__ __attribute_used__ = 0;
volatile u8 runtime_transport_socket_request_bytes[RUNTIME_SOCKET_REQUEST_LOGICAL_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u32 runtime_transport_socket_pre_call_args[8] __attribute_section_state_aligned_32__ __attribute_used__
    = {0};
volatile u32 runtime_transport_bind_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_bind_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_bind_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_target_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_command __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_bind_submitted_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_bind_callback_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_context_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_callback_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_stale_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_duplicate_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_request_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_request_storage_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_request_logical_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_request_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_sockaddr_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_family_value __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_port_value __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bind_address_value __attribute_section_state__ __attribute_used__ = 0;
volatile u8 runtime_transport_bind_request_bytes[36] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u32 runtime_transport_bind_pre_call_args[8] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u32 runtime_transport_cleanup_close_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_cleanup_close_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_cleanup_close_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_target_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_command __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_cleanup_close_submitted_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_cleanup_close_callback_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_context_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_callback_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_stale_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_duplicate_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_request_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_request_storage_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_request_logical_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_close_request_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_cleanup_close_request_value __attribute_section_state__ __attribute_used__ = -1;
volatile u8 runtime_transport_cleanup_close_request_bytes[4] __attribute_section_state_aligned_32__ __attribute_used__
    = {0};
volatile u32 runtime_transport_cleanup_close_pre_call_args[8] __attribute_section_state_aligned_32__
    __attribute_used__ = {0};
volatile u32 runtime_transport_bound_flag __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bound_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_closed_after_bind_failure __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_socket_leak_detected __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_kd_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_kd_closed __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_ip_fd __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_socket_fd __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_host_id __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_host_id_available __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_host_id_ready __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_service_started __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_bound_port __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_arm_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_rearm_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_submit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_bytes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_bytes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_receive_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_send_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_prepared_send_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_peer_ipv4 __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_peer_port __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_peer_family __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_peer_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_poll_action __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_last_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_submit_result_u32 __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_receive_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_receive_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_send_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_send_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_validated_result __attribute_section_state__ __attribute_used__ = 0;
/* Compact TCP send evidence, updated only in the connect/send completion paths. */
volatile s32 runtime_tcp_connect_completion_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_connect_phase_before __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_connect_phase_after __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_send_hello_entered __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_send_offset __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_send_completed_bytes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_hello_crc32 __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_send_r3_r9[7] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u32 runtime_tcp_send_outcome_close_pending __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_sync_veneer_address __attribute_section_state__ __attribute_used__ = 0x80505468;
volatile u32 runtime_tcp_sync_wrapper_entries __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_sync_pre_poll __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_sync_post_poll __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_tcp_sync_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_counter_sequence __attribute_section_state__ __attribute_used__ = 1;
volatile u32 runtime_tcp_counter_sent __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_counter_calls __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_counter_bytes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_counter_partials __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_expected __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_received __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_receive_offset __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_tcp_echo_receive_submit_result __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_tcp_echo_receive_callback_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_receive_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_partial_receive_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_success_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_mismatch_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_peer_close_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_receive_error_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_last_failure_phase __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_received_magic __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_received_type __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_received_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_expected_crc __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_received_crc __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_last_successful_sequence __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_tcp_echo_receive_bytes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_frames_encoded __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_frames_sent __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_frames_received __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_inbound_high_water __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_outbound_high_water __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_queue_overflow_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_crc_failure_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_sequence_failure_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_handshake_failure_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_client_test_sent_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_server_test_received_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_last_sent_type __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_last_received_type __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_client_tx_sequence __attribute_section_state__ __attribute_used__ = 1;
volatile u32 runtime_protocol_server_rx_sequence __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_last_client_acknowledged __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_client_nonce __attribute_section_state__ __attribute_used__ = 0x43503357;
volatile u32 runtime_protocol_server_nonce __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_expected_type __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_outbound_head __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_outbound_tail __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_outbound_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_inbound_head __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_inbound_tail __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_protocol_inbound_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_submit_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_callback_generation __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_configured_exchange_limit __attribute_section_state__ __attribute_used__ =
    PRIME3_IOS_UDP_DIAGNOSTIC_LOOP_COUNT;
volatile u32 runtime_transport_completed_exchange_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_current_exchange_index __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_last_completed_exchange_index __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_previous_peer_ipv4 __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_previous_peer_port __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_rearm_submission_failure_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_loop_complete_transition_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cleanup_deferred_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_target_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_command __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_target_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_command __attribute_section_state__ __attribute_used__ = 0;
volatile s32 runtime_transport_receive_submitted_fd __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_receive_submitted_socket __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_send_submitted_fd __attribute_section_state__ __attribute_used__ = -1;
volatile s32 runtime_transport_send_submitted_socket __attribute_section_state__ __attribute_used__ = -1;
volatile u32 runtime_transport_receive_input_vector_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_output_vector_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_input_vector_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_output_vector_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_request_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_request_storage_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_request_logical_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_request_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_request_flags __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_request_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_request_storage_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_request_logical_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_request_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_request_flags __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_has_destaddr __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_storage_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_logical_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_vector_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_vector_storage_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_vector_logical_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_vector_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_0_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_0_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_1_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_1_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_2_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_vector_2_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_vector_0_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_vector_0_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_vector_1_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_vector_1_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_payload_buffer_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_payload_capacity __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_payload_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_payload_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_payload_capacity __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_payload_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_source_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_source_logical_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_source_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_destination_address __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_destination_logical_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_destination_storage_size __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_destination_alignment __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_callback_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_context_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_callback_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_stale_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_receive_duplicate_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_callback_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_context_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_callback_exit_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_stale_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_send_duplicate_callback_count __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_polls_before_receive __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_polls_while_receive_pending __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_polls_after_receive __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_polls_before_send __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_polls_while_send_pending __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_polls_after_send __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_polls_after_loop_complete __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_datagrams_processed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_valid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_invalid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_too_short __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_invalid_magic __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_invalid_version __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_unsupported_type __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_nonzero_flags __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_length_mismatch __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_payload_too_large __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_invalid_payload __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_frames_malformed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_framed_responses_submitted __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_framed_responses_completed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_request_id __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_response_id __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_message_type __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_declared_payload_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_actual_payload_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_frame_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_final_datagram_index __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_requests_dispatched __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_hello_requests_received __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_hello_successes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_hello_version_rejections __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_hello_responses_submitted __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_hello_responses_completed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_hello_duplicate_requests __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_hello_renegotiation_rejections __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_pre_hello_gated_commands __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_not_negotiated_responses_submitted __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_not_negotiated_responses_completed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_ping_requests_received __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_pong_responses_submitted __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_pong_responses_completed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_unsupported_commands_received __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_unsupported_responses_submitted __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_unsupported_responses_completed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_negotiated_flag __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_selected_protocol_version __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_client_nonce __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_client_capabilities __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_runtime_capabilities __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_accepted_capabilities __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_session_id __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_runtime_build_id __attribute_section_state__ __attribute_used__ =
    RUNTIME_CP3W_RUNTIME_BUILD_ID;
volatile u32 runtime_transport_cp3w_hello_min_protocol_version __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_hello_max_protocol_version __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_hello_client_name_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_command __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_response_status __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_ping_payload_length __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_last_dispatch_result __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_requests __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_successes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_pre_hello_rejections __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_capability_rejections __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_invalid_payload_rejections __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_executable_validations __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_executable_failures __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_game_state_valid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_game_state_invalid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_player_state_valid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_player_state_invalid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_inventory_root_available __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_responses_submitted __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_responses_completed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_capability_errors_submitted __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_capability_errors_completed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_invalid_payload_errors_submitted __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_invalid_payload_errors_completed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_last_request_id __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_last_status __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_last_availability __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_last_profile_id __attribute_section_state__ __attribute_used__ =
    RUNTIME_CP3W_PROFILE_ID;
volatile u32 runtime_transport_cp3w_game_identity_last_fingerprint __attribute_section_state__ __attribute_used__ =
    RUNTIME_CP3W_PROFILE_FINGERPRINT;
volatile u32 runtime_transport_cp3w_game_identity_executable_recognized __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_game_state_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_player_state_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_game_identity_inventory_root_pointer __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_requests __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_available_snapshots __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_unavailable_snapshots __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_pre_hello_rejections __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_capability_rejections __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_invalid_payload_rejections __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_executable_failures __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_game_state_valid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_game_state_invalid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_root_valid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_root_invalid __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_range_failures __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_consistency_successes __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_consistency_failures __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_responses_submitted __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_responses_completed __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_last_request_id __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_last_status __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_last_availability __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_snapshot_sequence __attribute_section_state__ __attribute_used__ = 0;
volatile u32 runtime_transport_cp3w_inventory_last_root __attribute_section_state__ __attribute_used__ = 0;
volatile u8 runtime_transport_receive_request_bytes[RUNTIME_RECEIVE_REQUEST_LOGICAL_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u8 runtime_transport_receive_source_bytes[RUNTIME_WII_SOCKADDR_IN_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u8 runtime_transport_send_request_bytes[RUNTIME_SEND_REQUEST_LOGICAL_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u8 runtime_transport_send_destination_bytes[28] __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u8 runtime_transport_send_payload_bytes[RUNTIME_UDP_SEND_CAPACITY]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u8 runtime_transport_cp3w_hello_client_name_bytes[RUNTIME_CP3W_HELLO_MAX_NAME_LENGTH + 1]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};

volatile u8 runtime_transport_last_receive_preview[RUNTIME_PREVIEW_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u8 runtime_transport_last_send_preview[RUNTIME_PREVIEW_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u8 runtime_transport_receive_payload_buffer[RUNTIME_UDP_RECEIVE_CAPACITY]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u8 runtime_transport_nwc24_output_buffer[0x20]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
volatile u32 runtime_transport_getsockname_request __attribute_section_state_aligned_32__ __attribute_used__ = 0;
volatile u8 runtime_transport_getsockname_address[RUNTIME_WII_SOCKADDR_IN_SIZE]
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_nwc24_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_kd_close_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_open_ip_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_startup_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_get_host_id_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_socket_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_bind_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_cleanup_close_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_transport_receive_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_operation_context runtime_tcp_echo_receive_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_protocol_queue_slot runtime_protocol_outbound_queue[RUNTIME_PROTOCOL_QUEUE_DEPTH]
    __attribute_section_state_aligned_32__ __attribute_used__ = {{0}};
static runtime_protocol_queue_slot runtime_protocol_inbound_queue[RUNTIME_PROTOCOL_QUEUE_DEPTH]
    __attribute_section_state_aligned_32__ __attribute_used__ = {{0}};
static volatile runtime_operation_context runtime_transport_send_context
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static volatile runtime_send13_diagnostic runtime_send13_diagnostic_block
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_socket_request runtime_transport_socket_request __attribute_section_state_aligned_32__ __attribute_used__
    = {0};
static runtime_connect_params runtime_transport_bind_params __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_sendto_params runtime_transport_send_request __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_receive_request runtime_transport_receive_request
    __attribute_section_state_aligned_32__ __attribute_used__ = {0};
static runtime_ioctlv runtime_transport_receive_vectors[RUNTIME_RECEIVE_VECTOR_COUNT]
    __attribute_section_state_aligned_32__ __attribute_used__ = {{0}};
static runtime_ioctlv runtime_transport_send_vectors[RUNTIME_SEND_VECTOR_COUNT]
    __attribute_section_state_aligned_32__ __attribute_used__ = {{0}};
static volatile s32 runtime_transport_cleanup_close_request __attribute_section_state_aligned_32__ __attribute_used__ = -1;

static void runtime_memzero(volatile void* destination, u32 size) __attribute_section_code__;
static void runtime_memcpy(volatile void* destination, const volatile void* source, u32 size) __attribute_section_code__;
static u16 runtime_bswap16(u16 value) __attribute_section_code__;
static u32 runtime_host_id_is_ready(s32 result) __attribute_section_code__;
static void runtime_sync_network_diagnostics(void) __attribute_section_code__;
static void runtime_schedule_retry(u32 error_phase, s32 result, u32 socket_lost) __attribute_section_code__;
static void runtime_record_endpoint_verification_warning(s32 result) __attribute_section_code__;
static void runtime_enter_listening_after_bind(u32 endpoint_verified) __attribute_section_code__;
static void runtime_prepare_heartbeat(void) __attribute_section_code__;
static void runtime_prepare_tcp_hello(void) __attribute_section_code__;
static void runtime_prepare_tcp_literal_test(void) __attribute_section_code__;
static void runtime_prepare_tcp_literal_alt1(void) __attribute_section_code__;
static void runtime_copy_preview(volatile u8* destination, const volatile u8* source, u32 size) __attribute_section_code__;
static void runtime_copy_sockaddr_in(volatile u8* destination, u32 address_be, u16 port_be) __attribute_section_code__;
static u16 runtime_read_be16(const volatile u8* source) __attribute_section_code__;
static u32 runtime_read_be32(const volatile u8* source) __attribute_section_code__;
static void runtime_write_be16(volatile u8* destination, u16 value) __attribute_section_code__;
static void runtime_write_be32(volatile u8* destination, u32 value) __attribute_section_code__;
static u32 runtime_crc32(const volatile u8* source, u32 size) __attribute_section_code__;
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
static u32 runtime_transport_is_recvfrom_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_recv_send_once_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_recv_send_loop_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_cp3w_frame_validation_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_cp3w_ping_pong_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_cp3w_hello_session_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_cp3w_game_identity_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_cp3w_inventory_mode(void) __attribute_section_code__;
static u32 runtime_transport_is_cp3w_mode(void) __attribute_section_code__;
static u32 runtime_transport_uses_receive_mode(void) __attribute_section_code__;
static u32 runtime_transport_uses_send_mode(void) __attribute_section_code__;
static u32 runtime_transport_validate_loop_limit(void) __attribute_section_code__;
static void runtime_transport_note_loop_complete(void) __attribute_section_code__;
static void runtime_transport_note_cp3w_loop_complete(void) __attribute_section_code__;
static void runtime_transport_note_cp3w_ping_pong_loop_complete(void) __attribute_section_code__;
static void runtime_transport_note_cp3w_hello_session_loop_complete(void) __attribute_section_code__;
static void runtime_transport_note_cp3w_game_identity_loop_complete(void) __attribute_section_code__;
static void runtime_transport_note_cp3w_inventory_loop_complete(void) __attribute_section_code__;
static void runtime_transport_record_cp3w_frame_result(u32 result) __attribute_section_code__;
static s32 runtime_transport_validate_cp3w_frame(void) __attribute_section_code__;
static s32 runtime_transport_validate_cp3w_ping_pong_frame(void) __attribute_section_code__;
static u32 runtime_transport_cp3w_hello_request_matches_negotiated(u32 payload_length) __attribute_section_code__;
static void runtime_transport_copy_cp3w_hello_request_state(u32 payload_length) __attribute_section_code__;
static u32 runtime_transport_compute_cp3w_session_id(u32 client_nonce, u32 accepted_capabilities)
    __attribute_section_code__;
static s32 runtime_transport_validate_cp3w_hello_payload(u32 payload_length) __attribute_section_code__;
static s32 runtime_transport_dispatch_cp3w_ping_pong_request(void) __attribute_section_code__;
static s32 runtime_transport_dispatch_cp3w_hello_session_request(void) __attribute_section_code__;
static s32 runtime_transport_dispatch_cp3w_game_identity_request(void) __attribute_section_code__;
static void runtime_transport_prepare_loop_reply(void) __attribute_section_code__;
static void runtime_transport_prepare_cp3w_response(u32 request_id) __attribute_section_code__;
static void runtime_transport_prepare_cp3w_ping_response(u32 request_id, u32 payload_length) __attribute_section_code__;
static void runtime_transport_prepare_cp3w_hello_response(u32 request_id) __attribute_section_code__;
static void runtime_transport_prepare_cp3w_game_identity_response(
    u32 request_id,
    u32 availability
) __attribute_section_code__;
static u32 runtime_transport_prepare_cp3w_inventory_response(
    u32 request_id,
    u32 game_state,
    u32 inventory_root,
    u32 availability,
    u32 sequence
) __attribute_section_code__;
static void runtime_transport_prepare_cp3w_error_response(
    u32 request_id,
    u32 command,
    u32 error_code,
    const char* message,
    u32 message_length
) __attribute_section_code__;
static void runtime_cache_flush(const volatile void* address, u32 size) __attribute_section_code__;
static void runtime_cache_invalidate(const volatile void* address, u32 size) __attribute_section_code__;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
extern void runtime_native_post_copy_wrapper(void) __attribute_section_code__;
void runtime_native_overlay_draw_destination(u32 destination) __attribute_section_code__;
#endif
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
extern s32 runtime_call_retail_ios_ioctlv_async(
    s32 fd,
    u32 command,
    u32 input_count,
    u32 output_count,
    runtime_ioctlv* vectors,
    s32 (*callback)(s32, void*),
    void* userdata
) __attribute_section_code__;
extern s32 runtime_call_retail_ios_ioctlv_sync(
    s32 fd, u32 command, u32 input_count, u32 output_count, runtime_ioctlv* vectors
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
extern s32 runtime_call_retail_nwc24_open_lib(void) __attribute_section_code__;
extern s32 runtime_call_retail_network_bootstrap(void) __attribute_section_code__;
extern s32 runtime_read_retail_so_fd(void) __attribute_section_code__;
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
static s32 runtime_submit_ioctlv_receive(u32 next_phase) __attribute_section_code__;
static s32 runtime_submit_tcp_echo_receive(u32 next_phase) __attribute_section_code__;
static s32 runtime_submit_ioctlv_send(u32 next_phase) __attribute_section_code__;
static s32 runtime_wait_completion(void) __attribute_section_code__;
static s32 runtime_consume_receive_completion(void) __attribute_section_code__;
static s32 runtime_consume_tcp_echo_receive(void) __attribute_section_code__;
static s32 runtime_protocol_enqueue_outbound(u32 message_type, const volatile u8* frame) __attribute_section_code__;
static s32 runtime_protocol_enqueue_inbound(u32 message_type, u32 sequence) __attribute_section_code__;
static void runtime_protocol_prepare_frame(u32 message_type, volatile u8* frame) __attribute_section_code__;
static void runtime_protocol_fail(u32 phase) __attribute_section_code__;
static s32 runtime_consume_send_completion(void) __attribute_section_code__;
static void runtime_record_init_error(s32 result) __attribute_section_code__;
static void runtime_record_socket_error(s32 result) __attribute_section_code__;
static void runtime_record_receive_error(u32 phase, s32 result) __attribute_section_code__;
static void runtime_record_send_error(u32 phase, s32 result) __attribute_section_code__;
static void runtime_record_operation_callback(void) __attribute_section_code__;
static void runtime_record_submit_evidence(u32 operation, s32 result, u32 generation) __attribute_section_code__;
static void runtime_record_callback_evidence(u32 operation, s32 result, u32 generation) __attribute_section_code__;
static void runtime_sync_open_ip_context_evidence(void) __attribute_section_code__;
static void runtime_sync_startup_context_evidence(void) __attribute_section_code__;
static void runtime_sync_get_host_id_context_evidence(void) __attribute_section_code__;
static void runtime_sync_socket_context_evidence(void) __attribute_section_code__;
static void runtime_sync_bind_context_evidence(void) __attribute_section_code__;
static void runtime_sync_cleanup_close_context_evidence(void) __attribute_section_code__;
static void runtime_sync_receive_context_evidence(void) __attribute_section_code__;
static void runtime_sync_send_context_evidence(void) __attribute_section_code__;
static volatile runtime_operation_context* runtime_context_for_operation(u32 operation) __attribute_section_code__;
static void runtime_sync_context_for_operation(u32 operation) __attribute_section_code__;
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

static u32 runtime_host_id_is_ready(s32 result)
{
    u32 host_id = (u32)result;
    return host_id != 0 && (host_id >> 24) != 0xFFU;
}

#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
static u32 runtime_native_read_timebase(void)
{
    u32 value;
    __asm__ volatile("mftb %0" : "=r"(value));
    return value;
}

static u32 runtime_native_deadline_reached(u32 deadline)
{
    return deadline == 0 || (s32)(runtime_native_read_timebase() - deadline) >= 0;
}

static void runtime_native_set_stage(u32 stage)
{
    runtime_network_diagnostics_block.ios_revision = stage;
}
#endif

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

static u16 runtime_read_be16(const volatile u8* source)
{
    return (u16)(((u16)source[0] << 8) | (u16)source[1]);
}

static u32 runtime_read_be32(const volatile u8* source)
{
    return ((u32)source[0] << 24) | ((u32)source[1] << 16) | ((u32)source[2] << 8) | (u32)source[3];
}

static void runtime_write_be16(volatile u8* destination, u16 value)
{
    destination[0] = (u8)(value >> 8);
    destination[1] = (u8)value;
}

static void runtime_write_be32(volatile u8* destination, u32 value)
{
    destination[0] = (u8)(value >> 24);
    destination[1] = (u8)(value >> 16);
    destination[2] = (u8)(value >> 8);
    destination[3] = (u8)value;
}

static u32 runtime_crc32(const volatile u8* source, u32 size)
{
    u32 crc = 0xFFFFFFFFU;
    u32 index = 0;
    while (index < size) {
        u32 current = (crc ^ source[index]) & 0xFFU;
        u32 bit = 0;
        while (bit < 8) {
            current = (current & 1U) != 0 ? (current >> 1) ^ 0xEDB88320U : current >> 1;
            bit += 1;
        }
        crc = (crc >> 8) ^ current;
        index += 1;
    }
    return crc ^ 0xFFFFFFFFU;
}

static void runtime_set_phase(u32 phase, u32 action)
{
    if (runtime_transport_phase != phase) {
        runtime_network_diagnostics_block.previous_phase = runtime_transport_phase;
        runtime_network_diagnostics_block.transition_count += 1;
    }
    runtime_transport_phase = phase;
    runtime_transport_last_poll_action = action;
}

static void runtime_sync_network_diagnostics(void)
{
    volatile runtime_network_diagnostics* diagnostics = &runtime_network_diagnostics_block;
    diagnostics->current_phase = runtime_transport_phase;
    diagnostics->initialization_attempt_count = runtime_transport_open_ip_submit_count;
    diagnostics->successful_initialization_count = runtime_transport_initialization_success_count;
    diagnostics->restart_request_count = runtime_transport_restart_request_count;
    diagnostics->socket_recovery_count = runtime_transport_socket_recovery_count;
    diagnostics->network_initialization_result = runtime_transport_startup_callback_result;
    diagnostics->nwc24_result = *(volatile s32*)runtime_transport_nwc24_output_buffer;
    diagnostics->host_id_result = runtime_transport_get_host_id_callback_result;
    diagnostics->host_ip = runtime_transport_host_id;
    diagnostics->socket_descriptor = runtime_transport_socket_fd;
    diagnostics->socket_creation_result = runtime_transport_socket_callback_result;
    diagnostics->bind_result = runtime_transport_bind_callback_result;
    diagnostics->getsockname_result = runtime_transport_getsockname_result;
    diagnostics->last_socket_error = runtime_transport_last_socket_error;
    diagnostics->last_error_phase = runtime_transport_last_error_phase;
    diagnostics->actual_bind_address = runtime_transport_actual_bound_address;
    diagnostics->actual_bind_port = runtime_transport_actual_bound_port;
    diagnostics->listening = runtime_transport_bound_flag != 0 && runtime_transport_socket_fd >= 0;
    diagnostics->receive_loop_active = runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET;
    diagnostics->receive_call_count = runtime_transport_receive_submit_count;
    diagnostics->packets_received = runtime_transport_receive_count;
    diagnostics->malformed_packets_received = runtime_transport_cp3w_frames_malformed;
    diagnostics->transient_receive_errors = runtime_transport_transient_receive_error_count;
    diagnostics->fatal_receive_errors = runtime_transport_fatal_receive_error_count;
    diagnostics->send_call_count = runtime_transport_send_submit_count;
    diagnostics->packets_sent = runtime_transport_send_count;
    diagnostics->send_failures = runtime_transport_send_failure_count;
    diagnostics->close_call_count = runtime_transport_close_call_count;
    diagnostics->cleanup_call_count = runtime_transport_cleanup_count;
    diagnostics->last_close_descriptor = runtime_transport_last_close_descriptor;
    diagnostics->last_received_command = runtime_transport_cp3w_last_command;
    diagnostics->last_received_packet_size = runtime_transport_last_receive_length;
    diagnostics->last_sender_ip = runtime_transport_last_peer_ipv4;
    diagnostics->last_sender_port = runtime_transport_last_peer_port;
    diagnostics->last_heartbeat_result = runtime_transport_last_heartbeat_result;
    diagnostics->uptime_polls = runtime_poll_counter;
    diagnostics->last_successful_bind_poll = runtime_transport_last_successful_bind_poll;
    diagnostics->last_packet_receive_poll = runtime_transport_last_packet_receive_poll;
    diagnostics->last_packet_send_poll = runtime_transport_last_packet_send_poll;
    diagnostics->socket_lost_count = runtime_transport_socket_lost_count;
    diagnostics->getsockname_call_count = runtime_transport_getsockname_submit_count;
    diagnostics->receive_loop_iteration_count = runtime_transport_receive_arm_count;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    diagnostics->receive_call_count = runtime_transport_get_host_id_submit_count;
    diagnostics->last_packet_receive_poll = runtime_native_first_valid_host_id_poll;
    diagnostics->send_call_count = runtime_native_beacon_attempt_count;
    diagnostics->packets_sent = runtime_native_beacon_success_count;
    diagnostics->send_failures =
        runtime_native_beacon_submission_failure_count + runtime_native_beacon_completion_failure_count;
    diagnostics->malformed_packets_received = runtime_native_beacon_submission_failure_count;
    diagnostics->transient_receive_errors = runtime_native_beacon_completion_failure_count;
    diagnostics->bind_result = runtime_native_last_beacon_submit_result;
    diagnostics->getsockname_result = runtime_native_last_beacon_completion_result;
    diagnostics->last_successful_bind_poll = runtime_native_first_successful_beacon_poll;
    diagnostics->last_packet_send_poll = runtime_native_last_successful_beacon_poll;
    diagnostics->receive_loop_iteration_count = RUNTIME_NATIVE_BEACON_ATTEMPT_LIMIT;
    diagnostics->last_received_command = runtime_native_overlay_top_register;
    diagnostics->last_received_packet_size = runtime_native_overlay_bottom_register;
    diagnostics->last_sender_ip = runtime_native_overlay_geometry;
    diagnostics->last_sender_port = runtime_native_overlay_render_count;
    diagnostics->overlay_page = (u32)runtime_native_post_copy_hook_result;
#endif
}

static void runtime_schedule_retry(u32 error_phase, s32 result, u32 socket_lost)
{
    runtime_transport_last_error_phase = error_phase;
    runtime_transport_last_error = result;
    runtime_transport_last_ios_result = result;
    if (socket_lost != 0) {
        runtime_transport_socket_lost_count += 1;
        runtime_transport_socket_recovery_count += 1;
    }
    if (runtime_network_diagnostics_block.auto_retry_enabled == 0) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FATAL_ERROR, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
    } else if (socket_lost != 0) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SOCKET_LOST, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
    } else if (runtime_transport_socket_fd >= 0) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_FOR_RECOVERY, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
    } else {
        runtime_transport_retry_deadline = runtime_poll_counter + runtime_network_diagnostics_block.retry_delay_polls;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_RETRY_DELAY, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
    }
}

static void runtime_record_endpoint_verification_warning(s32 result)
{
    runtime_transport_last_socket_error = result;
    runtime_transport_last_error = result;
    runtime_transport_last_error_phase = RUNTIME_TRANSPORT_PHASE_WAIT_VERIFY_BOUND_ENDPOINT;
}

#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
static void runtime_native_record_fatal_error(u32 error_phase, s32 result)
{
    runtime_transport_last_error_phase = error_phase;
    runtime_transport_last_error = result;
    runtime_transport_last_socket_error = result;
    runtime_transport_last_ios_result = result;
    runtime_native_set_stage(RUNTIME_NATIVE_STAGE_TERMINAL_FAILURE);
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FAILED, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
}

static void runtime_native_continue_after_startup_warning(s32 result)
{
    runtime_transport_last_error_phase = RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP;
    runtime_transport_last_error = result;
    runtime_transport_last_socket_error = result;
    runtime_transport_service_started = 1;
    runtime_transport_startup_service_started_after_completion = 1;
    runtime_transport_ip_fd_after_startup = runtime_transport_ip_fd;
    runtime_native_set_stage(RUNTIME_NATIVE_STAGE_HOST_ID);
    runtime_native_next_host_id_poll = runtime_poll_counter;
    runtime_native_next_host_id_timebase = 0;
    runtime_set_phase(
        RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_HOST_ID,
        RUNTIME_TRANSPORT_POLL_ACTION_WAIT
    );
}

static void runtime_native_record_beacon_completion_failure(u32 error_phase, s32 result)
{
    runtime_native_beacon_completion_failure_count += 1;
    runtime_native_last_beacon_completion_result = result;
    runtime_transport_last_heartbeat_result = result;
    runtime_native_record_fatal_error(error_phase, result);
}
#endif

static void runtime_enter_listening_after_bind(u32 endpoint_verified)
{
    if (endpoint_verified != 0) {
        runtime_transport_bound_port = runtime_transport_actual_bound_port;
        runtime_transport_bound_address = runtime_transport_actual_bound_address;
    } else {
        runtime_transport_actual_bound_port = 0;
        runtime_transport_actual_bound_address = 0;
        runtime_transport_bound_port = runtime_cp3c_config_block.server_port;
        runtime_transport_bound_address = INADDR_ANY;
    }
    runtime_transport_bound_flag = 1;
    runtime_transport_initialization_success_count += 1;
    runtime_transport_last_successful_bind_poll = runtime_poll_counter;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_LISTENING, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
}

static void runtime_prepare_heartbeat(void)
{
    u32 index = 0;
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    while (index < sizeof(runtime_heartbeat_prefix) - 1) {
        runtime_transport_send_payload_bytes[index] = runtime_heartbeat_prefix[index];
        index += 1;
    }
    runtime_transport_send_payload_bytes[index++] = 0;
    runtime_write_be32(runtime_transport_send_payload_bytes + index, PRIME3_CP3W_RUNTIME_BUILD_ID);
    index += 4;
    runtime_write_be32(runtime_transport_send_payload_bytes + index, runtime_transport_phase);
    index += 4;
    runtime_transport_prepared_send_length = index;
}

/* CP3T HELLO: fixed 16-byte header followed by build, game, nonce, and seed. */
static void runtime_prepare_tcp_hello(void)
{
    u32 crc = 0;
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_write_be32(runtime_transport_send_payload_bytes + 0, 0x43503354);
    runtime_transport_send_payload_bytes[4] = 1;
    runtime_transport_send_payload_bytes[5] = 1;
    runtime_write_be16(runtime_transport_send_payload_bytes + 6, 32);
    runtime_write_be32(runtime_transport_send_payload_bytes + 8, 1);
    runtime_write_be32(runtime_transport_send_payload_bytes + 16, PRIME3_CP3W_RUNTIME_BUILD_ID);
    runtime_write_be32(runtime_transport_send_payload_bytes + 20, 1);
    runtime_write_be32(runtime_transport_send_payload_bytes + 24, 0x43503354);
    runtime_write_be32(runtime_transport_send_payload_bytes + 28, 0);
    crc = runtime_crc32(runtime_transport_send_payload_bytes, 32);
    runtime_write_be32(runtime_transport_send_payload_bytes + 12, crc);
    runtime_tcp_hello_crc32 = crc;
    runtime_transport_prepared_send_length = 32;
}

static void runtime_prepare_tcp_literal_test(void)
{
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_transport_send_payload_bytes[0] = 0x54;
    runtime_transport_send_payload_bytes[1] = 0x45;
    runtime_transport_send_payload_bytes[2] = 0x53;
    runtime_transport_send_payload_bytes[3] = 0x54;
    runtime_transport_prepared_send_length = 4;
    runtime_tcp_send_offset = 0;
    runtime_tcp_send_completed_bytes = 0;
}

static void runtime_prepare_tcp_literal_alt1(void)
{
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_transport_send_payload_bytes[0] = 0x41;
    runtime_transport_send_payload_bytes[1] = 0x4C;
    runtime_transport_send_payload_bytes[2] = 0x54;
    runtime_transport_send_payload_bytes[3] = 0x31;
    runtime_transport_prepared_send_length = 4;
    runtime_tcp_send_offset = 0;
    runtime_tcp_send_completed_bytes = 0;
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

static u32 runtime_transport_is_recvfrom_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_RECVFROM_ONCE;
}

static u32 runtime_transport_is_recv_send_once_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_RECV_SEND_ONCE;
}

static u32 runtime_transport_is_recv_send_loop_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_RETAIL_WRAPPER_RECV_SEND_LOOP;
}

static u32 runtime_transport_is_cp3w_frame_validation_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_FRAME_VALIDATION;
}

static u32 runtime_transport_is_cp3w_ping_pong_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_PING_PONG;
}

static u32 runtime_transport_is_cp3w_hello_session_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_HELLO_SESSION;
}

static u32 runtime_transport_is_cp3w_game_identity_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_GAME_IDENTITY;
}

static u32 runtime_transport_is_cp3w_inventory_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && (PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_INVENTORY
            || PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_INVENTORY_SERVICE);
}

static u32 runtime_transport_is_unbounded_cp3w_inventory_service(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_INVENTORY_SERVICE;
}

static u32 runtime_transport_is_native_wc24_bootstrap_mode(void)
{
    return PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
        && PRIME3_IOS_UDP_DIAGNOSTIC_MODE
            == RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_NATIVE_WC24_BOOTSTRAP_BEACON_ONCE;
}

static u32 runtime_transport_is_cp3w_mode(void)
{
    return runtime_transport_is_cp3w_frame_validation_mode()
        || runtime_transport_is_cp3w_ping_pong_mode()
        || runtime_transport_is_cp3w_hello_session_mode()
        || runtime_transport_is_cp3w_game_identity_mode()
        || runtime_transport_is_cp3w_inventory_mode();
}

static u32 runtime_transport_uses_receive_mode(void)
{
    return runtime_transport_is_recvfrom_once_mode()
        || runtime_transport_is_recv_send_once_mode()
        || runtime_transport_is_recv_send_loop_mode()
        || runtime_transport_is_cp3w_mode();
}

static u32 runtime_transport_uses_send_mode(void)
{
    return runtime_transport_is_recv_send_once_mode() || runtime_transport_is_recv_send_loop_mode()
        || runtime_transport_is_cp3w_mode() || runtime_transport_is_native_wc24_bootstrap_mode();
}

static u32 runtime_transport_validate_loop_limit(void)
{
    return runtime_transport_is_unbounded_cp3w_inventory_service()
        || (runtime_transport_configured_exchange_limit > 0
            && runtime_transport_configured_exchange_limit <= RUNTIME_EXCHANGE_COUNTER_LIMIT_MAX);
}

static u32 runtime_transport_exchange_limit_reached(void)
{
    return !runtime_transport_is_unbounded_cp3w_inventory_service()
        && runtime_transport_cp3w_datagrams_processed >= runtime_transport_configured_exchange_limit;
}

static void runtime_transport_note_loop_complete(void)
{
    runtime_transport_loop_complete_transition_count += 1;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_LOOP_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
}

static void runtime_transport_note_cp3w_loop_complete(void)
{
    runtime_transport_loop_complete_transition_count += 1;
    runtime_transport_cp3w_final_datagram_index = runtime_transport_cp3w_datagrams_processed;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_LOOP_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
}

static void runtime_transport_note_cp3w_ping_pong_loop_complete(void)
{
    runtime_transport_loop_complete_transition_count += 1;
    runtime_transport_cp3w_final_datagram_index = runtime_transport_cp3w_datagrams_processed;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_PING_PONG_LOOP_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
}

static void runtime_transport_note_cp3w_hello_session_loop_complete(void)
{
    runtime_transport_loop_complete_transition_count += 1;
    runtime_transport_cp3w_final_datagram_index = runtime_transport_cp3w_datagrams_processed;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_HELLO_SESSION_LOOP_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
}

static void runtime_transport_note_cp3w_game_identity_loop_complete(void)
{
    runtime_transport_loop_complete_transition_count += 1;
    runtime_transport_cp3w_final_datagram_index = runtime_transport_cp3w_datagrams_processed;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_LOOP_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
}

static void runtime_transport_note_cp3w_inventory_loop_complete(void)
{
    runtime_transport_loop_complete_transition_count += 1;
    runtime_transport_cp3w_final_datagram_index = runtime_transport_cp3w_datagrams_processed;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_LOOP_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
}

static void runtime_transport_record_cp3w_frame_result(u32 result)
{
    runtime_transport_cp3w_last_frame_result = result;
    if (result == RUNTIME_CP3W_FRAME_RESULT_VALID) {
        runtime_transport_cp3w_frames_valid += 1;
        return;
    }

    runtime_transport_cp3w_frames_invalid += 1;
    if (result == RUNTIME_CP3W_FRAME_RESULT_TOO_SHORT) {
        runtime_transport_cp3w_frames_too_short += 1;
    } else if (result == RUNTIME_CP3W_FRAME_RESULT_INVALID_MAGIC) {
        runtime_transport_cp3w_frames_invalid_magic += 1;
    } else if (result == RUNTIME_CP3W_FRAME_RESULT_INVALID_VERSION) {
        runtime_transport_cp3w_frames_invalid_version += 1;
    } else if (result == RUNTIME_CP3W_FRAME_RESULT_UNSUPPORTED_TYPE) {
        runtime_transport_cp3w_frames_unsupported_type += 1;
    } else if (result == RUNTIME_CP3W_FRAME_RESULT_NONZERO_FLAGS) {
        runtime_transport_cp3w_frames_nonzero_flags += 1;
    } else if (result == RUNTIME_CP3W_FRAME_RESULT_LENGTH_MISMATCH) {
        runtime_transport_cp3w_frames_length_mismatch += 1;
    } else if (result == RUNTIME_CP3W_FRAME_RESULT_PAYLOAD_TOO_LARGE) {
        runtime_transport_cp3w_frames_payload_too_large += 1;
    } else if (result == RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD) {
        runtime_transport_cp3w_frames_invalid_payload += 1;
    } else {
        runtime_transport_cp3w_frames_malformed += 1;
    }
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

static void runtime_transport_prepare_loop_reply(void)
{
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_memcpy(
        runtime_transport_send_payload_bytes,
        (const volatile void*)runtime_send_payload_ascii,
        RUNTIME_SEND_PAYLOAD_LENGTH
    );
    runtime_transport_prepared_send_length = RUNTIME_SEND_PAYLOAD_LENGTH;
}

static void runtime_transport_prepare_cp3w_response(u32 request_id)
{
    u32 crc = 0;
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_memcpy(runtime_transport_send_payload_bytes, runtime_cp3w_magic, sizeof(runtime_cp3w_magic));
    runtime_transport_send_payload_bytes[4] = 1;
    runtime_transport_send_payload_bytes[5] = RUNTIME_CP3W_PACKET_KIND_RESPONSE;
    runtime_transport_send_payload_bytes[6] = RUNTIME_CP3W_COMMAND_RESERVED_MAILBOX;
    runtime_transport_send_payload_bytes[7] = RUNTIME_CP3W_RESPONSE_STATUS_OK;
    runtime_write_be32(runtime_transport_send_payload_bytes + 8, request_id);
    runtime_write_be32(runtime_transport_send_payload_bytes + 12, RUNTIME_CP3W_RESPONSE_PAYLOAD_LENGTH);
    runtime_memcpy(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE,
        (const volatile void*)runtime_cp3w_response_payload_ascii,
        RUNTIME_CP3W_RESPONSE_PAYLOAD_LENGTH
    );
    crc = runtime_crc32(
        runtime_transport_send_payload_bytes,
        RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_RESPONSE_PAYLOAD_LENGTH
    );
    runtime_write_be32(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_RESPONSE_PAYLOAD_LENGTH,
        crc
    );
    runtime_transport_prepared_send_length = RUNTIME_CP3W_RESPONSE_PACKET_LENGTH;
    runtime_transport_cp3w_last_response_id = request_id;
    runtime_transport_cp3w_last_response_status = RUNTIME_CP3W_RESPONSE_STATUS_OK;
}

static void runtime_transport_prepare_cp3w_ping_response(u32 request_id, u32 payload_length)
{
    u32 crc = 0;
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_memcpy(runtime_transport_send_payload_bytes, runtime_cp3w_magic, sizeof(runtime_cp3w_magic));
    runtime_transport_send_payload_bytes[4] = 1;
    runtime_transport_send_payload_bytes[5] = RUNTIME_CP3W_PACKET_KIND_RESPONSE;
    runtime_transport_send_payload_bytes[6] = RUNTIME_CP3W_COMMAND_PING;
    runtime_transport_send_payload_bytes[7] = RUNTIME_CP3W_RESPONSE_STATUS_OK;
    runtime_write_be32(runtime_transport_send_payload_bytes + 8, request_id);
    runtime_write_be32(runtime_transport_send_payload_bytes + 12, payload_length);
    if (payload_length != 0) {
        runtime_memcpy(
            runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE,
            runtime_transport_receive_payload_buffer + RUNTIME_CP3W_HEADER_SIZE,
            payload_length
        );
    }
    crc = runtime_crc32(runtime_transport_send_payload_bytes, RUNTIME_CP3W_HEADER_SIZE + payload_length);
    runtime_write_be32(runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + payload_length, crc);
    runtime_transport_prepared_send_length = RUNTIME_CP3W_HEADER_SIZE + payload_length + RUNTIME_CP3W_CRC_SIZE;
    runtime_transport_cp3w_last_response_id = request_id;
    runtime_transport_cp3w_last_response_status = RUNTIME_CP3W_RESPONSE_STATUS_OK;
}

static void runtime_transport_prepare_cp3w_hello_response(u32 request_id)
{
    u32 crc = 0;
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_memcpy(runtime_transport_send_payload_bytes, runtime_cp3w_magic, sizeof(runtime_cp3w_magic));
    runtime_transport_send_payload_bytes[4] = RUNTIME_CP3W_SUPPORTED_PROTOCOL_VERSION;
    runtime_transport_send_payload_bytes[5] = RUNTIME_CP3W_PACKET_KIND_RESPONSE;
    runtime_transport_send_payload_bytes[6] = RUNTIME_CP3W_COMMAND_HELLO;
    runtime_transport_send_payload_bytes[7] = RUNTIME_CP3W_RESPONSE_STATUS_OK;
    runtime_write_be32(runtime_transport_send_payload_bytes + 8, request_id);
    runtime_write_be32(runtime_transport_send_payload_bytes + 12, RUNTIME_CP3W_HELLO_RESPONSE_PAYLOAD_LENGTH);
    runtime_transport_send_payload_bytes[RUNTIME_CP3W_HEADER_SIZE] = (u8)runtime_transport_cp3w_selected_protocol_version;
    runtime_write_be32(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + 1,
        runtime_transport_cp3w_runtime_capabilities
    );
    runtime_write_be32(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + 5,
        runtime_transport_cp3w_accepted_capabilities
    );
    runtime_write_be32(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + 9,
        runtime_transport_cp3w_session_id
    );
    runtime_write_be32(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + 13,
        runtime_transport_cp3w_runtime_build_id
    );
    runtime_transport_send_payload_bytes[RUNTIME_CP3W_HEADER_SIZE + 17] = PRIME3_IOS_UDP_DIAGNOSTIC_MODE;
    runtime_transport_send_payload_bytes[RUNTIME_CP3W_HEADER_SIZE + 18] = RUNTIME_CP3W_HELLO_METADATA_VERSION;
    runtime_transport_send_payload_bytes[RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_HELLO_RESPONSE_FIXED_SIZE] =
        RUNTIME_CP3W_RUNTIME_NAME_LENGTH;
    runtime_memcpy(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_HELLO_RESPONSE_FIXED_SIZE + 1,
        (const volatile void*)runtime_cp3w_runtime_name_ascii,
        RUNTIME_CP3W_RUNTIME_NAME_LENGTH
    );
    crc = runtime_crc32(
        runtime_transport_send_payload_bytes,
        RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_HELLO_RESPONSE_PAYLOAD_LENGTH
    );
    runtime_write_be32(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_HELLO_RESPONSE_PAYLOAD_LENGTH,
        crc
    );
    runtime_transport_prepared_send_length =
        RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_HELLO_RESPONSE_PAYLOAD_LENGTH + RUNTIME_CP3W_CRC_SIZE;
    runtime_transport_cp3w_last_response_id = request_id;
    runtime_transport_cp3w_last_response_status = RUNTIME_CP3W_RESPONSE_STATUS_OK;
}

static u32 runtime_transport_is_valid_mem1_range(u32 address, u32 size)
{
    u32 end = address + size;
    return address != 0 && (address & 3U) == 0 && address >= RUNTIME_MEM1_START
        && end >= address && end <= RUNTIME_MEM1_END;
}

static u32 runtime_transport_prime3_executable_recognized(void)
{
    const volatile u8* marker = (const volatile u8*)RUNTIME_PRIME3_NTSC_BUILD_STRING_ADDRESS;
    return marker[0] == '!' && marker[1] == '#' && marker[2] == '$' && marker[3] == 'M';
}

static void runtime_transport_prepare_cp3w_game_identity_response(u32 request_id, u32 availability)
{
    u32 crc = 0;
    volatile u8* payload = runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE;
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_memcpy(runtime_transport_send_payload_bytes, runtime_cp3w_magic, sizeof(runtime_cp3w_magic));
    runtime_transport_send_payload_bytes[4] = RUNTIME_CP3W_SUPPORTED_PROTOCOL_VERSION;
    runtime_transport_send_payload_bytes[5] = RUNTIME_CP3W_PACKET_KIND_RESPONSE;
    runtime_transport_send_payload_bytes[6] = RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY;
    runtime_transport_send_payload_bytes[7] = RUNTIME_CP3W_RESPONSE_STATUS_OK;
    runtime_write_be32(runtime_transport_send_payload_bytes + 8, request_id);
    runtime_write_be32(runtime_transport_send_payload_bytes + 12, RUNTIME_CP3W_GAME_IDENTITY_PAYLOAD_SIZE);
    payload[0] = RUNTIME_CP3W_GAME_IDENTITY_SCHEMA_VERSION;
    payload[1] = RUNTIME_CP3W_GAME_ID;
    payload[2] = RUNTIME_CP3W_PLATFORM_ID;
    payload[3] = RUNTIME_CP3W_REGION_ID;
    runtime_write_be16(payload + 4, RUNTIME_CP3W_REVISION_ID);
    payload[6] = RUNTIME_CP3W_SUPPORTED_PROTOCOL_VERSION;
    payload[7] = PRIME3_IOS_UDP_DIAGNOSTIC_MODE;
    runtime_write_be32(payload + 8, RUNTIME_CP3W_PROFILE_ID);
    runtime_write_be32(payload + 12, RUNTIME_CP3W_PROFILE_FINGERPRINT);
    runtime_write_be32(payload + 16, RUNTIME_CP3W_RUNTIME_BUILD_ID);
    runtime_write_be32(payload + 20, availability);
    runtime_write_be32(payload + 24, 0);
    crc = runtime_crc32(
        runtime_transport_send_payload_bytes,
        RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_GAME_IDENTITY_PAYLOAD_SIZE
    );
    runtime_write_be32(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_GAME_IDENTITY_PAYLOAD_SIZE,
        crc
    );
    runtime_transport_prepared_send_length =
        RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_GAME_IDENTITY_PAYLOAD_SIZE + RUNTIME_CP3W_CRC_SIZE;
    runtime_transport_cp3w_last_response_id = request_id;
    runtime_transport_cp3w_last_response_status = RUNTIME_CP3W_RESPONSE_STATUS_OK;
    runtime_transport_cp3w_game_identity_last_status = RUNTIME_CP3W_RESPONSE_STATUS_OK;
    runtime_transport_cp3w_game_identity_last_availability = availability;
}

static u32 runtime_transport_prepare_cp3w_inventory_response(
    u32 request_id,
    u32 game_state,
    u32 inventory_root,
    u32 availability,
    u32 sequence
)
{
    u32 i = 0;
    u32 crc = 0;
    u32 current_game_state = 0;
    u32 current_inventory_root = 0;
    volatile u8* payload = runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE;
    volatile u8* records = payload + RUNTIME_CP3W_INVENTORY_HEADER_SIZE;
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_memcpy(runtime_transport_send_payload_bytes, runtime_cp3w_magic, sizeof(runtime_cp3w_magic));
    runtime_transport_send_payload_bytes[4] = RUNTIME_CP3W_SUPPORTED_PROTOCOL_VERSION;
    runtime_transport_send_payload_bytes[5] = RUNTIME_CP3W_PACKET_KIND_RESPONSE;
    runtime_transport_send_payload_bytes[6] = RUNTIME_CP3W_COMMAND_GET_INVENTORY;
    runtime_transport_send_payload_bytes[7] = RUNTIME_CP3W_RESPONSE_STATUS_OK;
    runtime_write_be32(runtime_transport_send_payload_bytes + 8, request_id);
    runtime_write_be32(runtime_transport_send_payload_bytes + 12, RUNTIME_CP3W_INVENTORY_PAYLOAD_SIZE);
    payload[0] = RUNTIME_CP3W_INVENTORY_SCHEMA_VERSION;
    payload[1] = RUNTIME_CP3W_INVENTORY_RECORD_COUNT;
    payload[2] = RUNTIME_CP3W_INVENTORY_RECORD_SIZE;
    payload[3] = 0;
    runtime_write_be32(payload + 8, sequence);

    if (
        (availability & RUNTIME_CP3W_INVENTORY_AVAILABILITY_ROOT_VALID) != 0
        && (availability & RUNTIME_CP3W_INVENTORY_AVAILABILITY_RANGE_VALID) != 0
    ) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_READ_RECORDS, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        for (i = 0; i < RUNTIME_CP3W_INVENTORY_RECORD_COUNT; i += 1) {
            u32 slot = inventory_root + 0x54U + ((u32)runtime_cp3w_inventory_item_ids[i] * 0x0CU);
            runtime_write_be32(records + i * RUNTIME_CP3W_INVENTORY_RECORD_SIZE, *(const volatile u32*)slot);
            runtime_write_be32(records + i * RUNTIME_CP3W_INVENTORY_RECORD_SIZE + 4, *(const volatile u32*)(slot + 4U));
        }
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_REVALIDATE_ROOT,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        current_game_state = *(const volatile u32*)RUNTIME_PRIME3_NTSC_GAME_STATE_POINTER_ADDRESS;
        if (current_game_state == game_state && runtime_transport_is_valid_mem1_range(current_game_state, 0x28U)) {
            current_inventory_root = *(const volatile u32*)(current_game_state + 0x24U);
        }
        if (current_inventory_root == inventory_root) {
            availability |= RUNTIME_CP3W_INVENTORY_AVAILABILITY_SNAPSHOT_AVAILABLE
                | RUNTIME_CP3W_INVENTORY_AVAILABILITY_CONSISTENCY_PASSED;
            runtime_transport_cp3w_inventory_consistency_successes += 1;
            runtime_transport_cp3w_inventory_available_snapshots += 1;
        } else {
            runtime_memzero(records, RUNTIME_CP3W_INVENTORY_RECORD_COUNT * RUNTIME_CP3W_INVENTORY_RECORD_SIZE);
            availability |= RUNTIME_CP3W_INVENTORY_AVAILABILITY_TEMPORARILY_UNAVAILABLE
                | RUNTIME_CP3W_INVENTORY_AVAILABILITY_INCONSISTENT;
            runtime_transport_cp3w_inventory_consistency_failures += 1;
            runtime_transport_cp3w_inventory_unavailable_snapshots += 1;
        }
    } else {
        availability |= RUNTIME_CP3W_INVENTORY_AVAILABILITY_TEMPORARILY_UNAVAILABLE;
        runtime_transport_cp3w_inventory_unavailable_snapshots += 1;
    }
    runtime_write_be32(payload + 4, availability);
    crc = runtime_crc32(
        runtime_transport_send_payload_bytes,
        RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_INVENTORY_PAYLOAD_SIZE
    );
    runtime_write_be32(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_INVENTORY_PAYLOAD_SIZE,
        crc
    );
    runtime_transport_prepared_send_length =
        RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_INVENTORY_PAYLOAD_SIZE + RUNTIME_CP3W_CRC_SIZE;
    runtime_transport_cp3w_last_response_id = request_id;
    runtime_transport_cp3w_last_response_status = RUNTIME_CP3W_RESPONSE_STATUS_OK;
    runtime_transport_cp3w_inventory_last_status = RUNTIME_CP3W_RESPONSE_STATUS_OK;
    runtime_transport_cp3w_inventory_last_availability = availability;
    return availability;
}

static void runtime_transport_prepare_cp3w_error_response(
    u32 request_id,
    u32 command,
    u32 error_code,
    const char* message,
    u32 message_length
)
{
    u32 crc = 0;
    u32 packet_payload_length = RUNTIME_CP3W_ERROR_HEADER_SIZE + message_length;
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_memcpy(runtime_transport_send_payload_bytes, runtime_cp3w_magic, sizeof(runtime_cp3w_magic));
    runtime_transport_send_payload_bytes[4] = RUNTIME_CP3W_SUPPORTED_PROTOCOL_VERSION;
    runtime_transport_send_payload_bytes[5] = RUNTIME_CP3W_PACKET_KIND_RESPONSE;
    runtime_transport_send_payload_bytes[6] = (u8)command;
    runtime_transport_send_payload_bytes[7] = RUNTIME_CP3W_RESPONSE_STATUS_ERROR;
    runtime_write_be32(runtime_transport_send_payload_bytes + 8, request_id);
    runtime_write_be32(runtime_transport_send_payload_bytes + 12, packet_payload_length);
    runtime_write_be16(runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE, (u16)error_code);
    runtime_write_be16(runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + 2, (u16)command);
    runtime_write_be16(runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + 4, (u16)message_length);
    runtime_memcpy(
        runtime_transport_send_payload_bytes + RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_ERROR_HEADER_SIZE,
        (const volatile void*)message,
        message_length
    );
    crc = runtime_crc32(
        runtime_transport_send_payload_bytes,
        RUNTIME_CP3W_HEADER_SIZE + packet_payload_length
    );
    runtime_write_be32(
        runtime_transport_send_payload_bytes
            + RUNTIME_CP3W_HEADER_SIZE
            + packet_payload_length,
        crc
    );
    runtime_transport_prepared_send_length = RUNTIME_CP3W_HEADER_SIZE + packet_payload_length + RUNTIME_CP3W_CRC_SIZE;
    runtime_transport_cp3w_last_response_id = request_id;
    runtime_transport_cp3w_last_response_status = RUNTIME_CP3W_RESPONSE_STATUS_ERROR;
}

static u32 runtime_transport_cp3w_hello_request_matches_negotiated(u32 payload_length)
{
    u32 name_length = 0;
    u32 index = 0;
    if (payload_length < RUNTIME_CP3W_HELLO_REQUEST_FIXED_SIZE + RUNTIME_CP3W_HELLO_NAME_LENGTH_SIZE) {
        return 0;
    }
    name_length = runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_HELLO_REQUEST_FIXED_SIZE];
    if (name_length != runtime_transport_cp3w_hello_client_name_length) {
        return 0;
    }
    if ((u32)runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE] != runtime_transport_cp3w_hello_min_protocol_version) {
        return 0;
    }
    if ((u32)runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE + 1]
        != runtime_transport_cp3w_hello_max_protocol_version) {
        return 0;
    }
    if (runtime_read_be32(runtime_transport_receive_payload_buffer + RUNTIME_CP3W_HEADER_SIZE + 2)
        != runtime_transport_cp3w_client_capabilities) {
        return 0;
    }
    if (runtime_read_be32(runtime_transport_receive_payload_buffer + RUNTIME_CP3W_HEADER_SIZE + 6)
        != runtime_transport_cp3w_client_nonce) {
        return 0;
    }
    while (index < name_length) {
        if (
            runtime_transport_receive_payload_buffer[
                RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_HELLO_REQUEST_FIXED_SIZE + 1 + index
            ] != runtime_transport_cp3w_hello_client_name_bytes[index]
        ) {
            return 0;
        }
        index += 1;
    }
    return 1;
}

static void runtime_transport_copy_cp3w_hello_request_state(u32 payload_length)
{
    u32 name_length = payload_length - RUNTIME_CP3W_HELLO_REQUEST_FIXED_SIZE - RUNTIME_CP3W_HELLO_NAME_LENGTH_SIZE;
    u32 index = 0;
    runtime_transport_cp3w_hello_min_protocol_version = runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE];
    runtime_transport_cp3w_hello_max_protocol_version = runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE + 1];
    runtime_transport_cp3w_client_capabilities =
        runtime_read_be32(runtime_transport_receive_payload_buffer + RUNTIME_CP3W_HEADER_SIZE + 2);
    runtime_transport_cp3w_client_nonce =
        runtime_read_be32(runtime_transport_receive_payload_buffer + RUNTIME_CP3W_HEADER_SIZE + 6);
    runtime_transport_cp3w_hello_client_name_length = name_length;
    runtime_memzero(
        runtime_transport_cp3w_hello_client_name_bytes,
        sizeof(runtime_transport_cp3w_hello_client_name_bytes)
    );
    while (index < name_length) {
        runtime_transport_cp3w_hello_client_name_bytes[index] =
            runtime_transport_receive_payload_buffer[
                RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_HELLO_REQUEST_FIXED_SIZE + 1 + index
            ];
        index += 1;
    }
}

static u32 runtime_transport_compute_cp3w_session_id(u32 client_nonce, u32 accepted_capabilities)
{
    u8 canonical[17];
    runtime_memzero(canonical, sizeof(canonical));
    canonical[0] = RUNTIME_CP3W_SUPPORTED_PROTOCOL_VERSION;
    runtime_write_be32(canonical + 1, client_nonce);
    runtime_write_be32(canonical + 5, RUNTIME_CP3W_RUNTIME_BUILD_ID);
    runtime_write_be32(canonical + 9, runtime_transport_cp3w_runtime_capabilities);
    runtime_write_be32(canonical + 13, accepted_capabilities);
    return runtime_crc32(canonical, sizeof(canonical));
}

static s32 runtime_transport_validate_cp3w_hello_payload(u32 payload_length)
{
    u32 name_length = 0;
    if (payload_length < RUNTIME_CP3W_HELLO_REQUEST_FIXED_SIZE + RUNTIME_CP3W_HELLO_NAME_LENGTH_SIZE) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD);
        return -1;
    }
    name_length = runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_HELLO_REQUEST_FIXED_SIZE];
    if (name_length > RUNTIME_CP3W_HELLO_MAX_NAME_LENGTH) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD);
        return -1;
    }
    if (payload_length != RUNTIME_CP3W_HELLO_REQUEST_FIXED_SIZE + RUNTIME_CP3W_HELLO_NAME_LENGTH_SIZE + name_length) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD);
        return -1;
    }
    return 0;
}

static s32 runtime_transport_validate_cp3w_frame(void)
{
    u32 payload_length = 0;
    u32 actual_payload_length = 0;
    u32 expected_total_length = 0;
    u32 computed_crc = 0;
    u32 received_crc = 0;
    u32 request_id = 0;
    runtime_transport_cp3w_datagrams_processed = runtime_transport_receive_count;
    runtime_transport_cp3w_last_message_type = 0;
    runtime_transport_cp3w_last_declared_payload_length = 0;
    runtime_transport_cp3w_last_actual_payload_length = runtime_transport_last_receive_length;
    runtime_transport_cp3w_last_request_id = 0;

    if (runtime_transport_last_receive_length < (RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_CRC_SIZE)) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_TOO_SHORT);
        return -1;
    }
    if (
        runtime_transport_receive_payload_buffer[0] != runtime_cp3w_magic[0]
        || runtime_transport_receive_payload_buffer[1] != runtime_cp3w_magic[1]
        || runtime_transport_receive_payload_buffer[2] != runtime_cp3w_magic[2]
        || runtime_transport_receive_payload_buffer[3] != runtime_cp3w_magic[3]
    ) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_MAGIC);
        return -1;
    }
    if (runtime_transport_receive_payload_buffer[4] != 1) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_VERSION);
        return -1;
    }
    runtime_transport_cp3w_last_message_type = runtime_transport_receive_payload_buffer[5];
    if (
        runtime_transport_receive_payload_buffer[5] != RUNTIME_CP3W_PACKET_KIND_REQUEST
        || runtime_transport_receive_payload_buffer[6] != RUNTIME_CP3W_COMMAND_RESERVED_MAILBOX
    ) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_UNSUPPORTED_TYPE);
        return -1;
    }
    if (runtime_transport_receive_payload_buffer[7] != RUNTIME_CP3W_RESPONSE_STATUS_OK) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_NONZERO_FLAGS);
        return -1;
    }

    request_id = runtime_read_be32(runtime_transport_receive_payload_buffer + 8);
    payload_length = runtime_read_be32(runtime_transport_receive_payload_buffer + 12);
    runtime_transport_cp3w_last_request_id = request_id;
    runtime_transport_cp3w_last_declared_payload_length = payload_length;
    actual_payload_length = runtime_transport_last_receive_length - RUNTIME_CP3W_HEADER_SIZE - RUNTIME_CP3W_CRC_SIZE;
    runtime_transport_cp3w_last_actual_payload_length = actual_payload_length;
    if (payload_length > RUNTIME_UDP_RECEIVE_CAPACITY - RUNTIME_CP3W_HEADER_SIZE - RUNTIME_CP3W_CRC_SIZE) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_PAYLOAD_TOO_LARGE);
        return -1;
    }
    expected_total_length = RUNTIME_CP3W_HEADER_SIZE + payload_length + RUNTIME_CP3W_CRC_SIZE;
    if (expected_total_length != runtime_transport_last_receive_length) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_LENGTH_MISMATCH);
        return -1;
    }
    computed_crc = runtime_crc32(runtime_transport_receive_payload_buffer, runtime_transport_last_receive_length - 4);
    received_crc = runtime_read_be32(runtime_transport_receive_payload_buffer + runtime_transport_last_receive_length - 4);
    if (computed_crc != received_crc) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_MALFORMED);
        return -1;
    }
    if (payload_length != RUNTIME_CP3W_REQUEST_PAYLOAD_LENGTH) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD);
        return -1;
    }
    if (
        runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE] != (u8)runtime_cp3w_request_payload_ascii[0]
        || runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE + 1]
            != (u8)runtime_cp3w_request_payload_ascii[1]
    ) {
        /* fall through to full comparison */
    }
    {
        u32 index = 0;
        while (index < RUNTIME_CP3W_REQUEST_PAYLOAD_LENGTH) {
            if (
                runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE + index]
                != (u8)runtime_cp3w_request_payload_ascii[index]
            ) {
                runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD);
                return -1;
            }
            index += 1;
        }
    }

    runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_VALID);
    runtime_transport_prepare_cp3w_response(request_id);
    return 0;
}

static s32 runtime_transport_validate_cp3w_ping_pong_frame(void)
{
    u32 payload_length = 0;
    u32 actual_payload_length = 0;
    u32 expected_total_length = 0;
    u32 computed_crc = 0;
    u32 received_crc = 0;
    u32 request_id = 0;
    runtime_transport_cp3w_datagrams_processed = runtime_transport_receive_count;
    runtime_transport_cp3w_last_message_type = 0;
    runtime_transport_cp3w_last_declared_payload_length = 0;
    runtime_transport_cp3w_last_actual_payload_length = runtime_transport_last_receive_length;
    runtime_transport_cp3w_last_request_id = 0;
    runtime_transport_cp3w_last_command = 0;
    runtime_transport_cp3w_last_response_status = 0;
    runtime_transport_cp3w_last_ping_payload_length = 0;
    runtime_transport_cp3w_last_dispatch_result = 0;
    if (runtime_transport_last_receive_length < (RUNTIME_CP3W_HEADER_SIZE + RUNTIME_CP3W_CRC_SIZE)) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_TOO_SHORT);
        return -1;
    }
    if (
        runtime_transport_receive_payload_buffer[0] != runtime_cp3w_magic[0]
        || runtime_transport_receive_payload_buffer[1] != runtime_cp3w_magic[1]
        || runtime_transport_receive_payload_buffer[2] != runtime_cp3w_magic[2]
        || runtime_transport_receive_payload_buffer[3] != runtime_cp3w_magic[3]
    ) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_MAGIC);
        return -1;
    }
    if (runtime_transport_receive_payload_buffer[4] != 1) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_VERSION);
        return -1;
    }
    runtime_transport_cp3w_last_message_type = runtime_transport_receive_payload_buffer[5];
    runtime_transport_cp3w_last_command = runtime_transport_receive_payload_buffer[6];
    if (runtime_transport_receive_payload_buffer[5] != RUNTIME_CP3W_PACKET_KIND_REQUEST) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_UNSUPPORTED_TYPE);
        return -1;
    }
    if (runtime_transport_receive_payload_buffer[7] != RUNTIME_CP3W_RESPONSE_STATUS_OK) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_NONZERO_FLAGS);
        return -1;
    }

    request_id = runtime_read_be32(runtime_transport_receive_payload_buffer + 8);
    payload_length = runtime_read_be32(runtime_transport_receive_payload_buffer + 12);
    runtime_transport_cp3w_last_request_id = request_id;
    runtime_transport_cp3w_last_declared_payload_length = payload_length;
    actual_payload_length = runtime_transport_last_receive_length - RUNTIME_CP3W_HEADER_SIZE - RUNTIME_CP3W_CRC_SIZE;
    runtime_transport_cp3w_last_actual_payload_length = actual_payload_length;
    if (payload_length > RUNTIME_UDP_RECEIVE_CAPACITY - RUNTIME_CP3W_HEADER_SIZE - RUNTIME_CP3W_CRC_SIZE) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_PAYLOAD_TOO_LARGE);
        return -1;
    }
    expected_total_length = RUNTIME_CP3W_HEADER_SIZE + payload_length + RUNTIME_CP3W_CRC_SIZE;
    if (expected_total_length != runtime_transport_last_receive_length) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_LENGTH_MISMATCH);
        return -1;
    }
    computed_crc = runtime_crc32(runtime_transport_receive_payload_buffer, runtime_transport_last_receive_length - 4);
    received_crc = runtime_read_be32(runtime_transport_receive_payload_buffer + runtime_transport_last_receive_length - 4);
    if (computed_crc != received_crc) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_MALFORMED);
        return -1;
    }

    if (
        runtime_transport_cp3w_last_command != RUNTIME_CP3W_COMMAND_HELLO
        && runtime_transport_cp3w_last_command != RUNTIME_CP3W_COMMAND_READ_MEMORY
        && runtime_transport_cp3w_last_command != RUNTIME_CP3W_COMMAND_PING
        && runtime_transport_cp3w_last_command != RUNTIME_CP3W_COMMAND_DISCONNECT
        && runtime_transport_cp3w_last_command != RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY
        && runtime_transport_cp3w_last_command != RUNTIME_CP3W_COMMAND_GET_INVENTORY
        && runtime_transport_cp3w_last_command != RUNTIME_CP3W_COMMAND_RESERVED_MAILBOX
    ) {
        runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_UNSUPPORTED_TYPE);
        return -1;
    }

    runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_VALID);
    return 0;
}

static s32 runtime_transport_dispatch_cp3w_ping_pong_request(void)
{
    u32 command = runtime_transport_cp3w_last_command;
    u32 payload_length = runtime_transport_cp3w_last_declared_payload_length;
    runtime_transport_cp3w_requests_dispatched += 1;
    runtime_transport_cp3w_last_dispatch_result = 0;

    if (command == RUNTIME_CP3W_COMMAND_PING) {
        if (payload_length > RUNTIME_CP3W_MAX_PING_PAYLOAD_LENGTH) {
            runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD);
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD;
            return -1;
        }
        runtime_transport_cp3w_ping_requests_received += 1;
        runtime_transport_cp3w_last_ping_payload_length = payload_length;
        runtime_transport_prepare_cp3w_ping_response(runtime_transport_cp3w_last_request_id, payload_length);
        runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_FRAME_RESULT_VALID;
        return 0;
    }

    runtime_transport_cp3w_unsupported_commands_received += 1;
    runtime_transport_prepare_cp3w_error_response(
        runtime_transport_cp3w_last_request_id,
        command,
        RUNTIME_CP3W_ERROR_CODE_UNKNOWN_COMMAND,
        runtime_cp3w_unsupported_message_ascii,
        RUNTIME_CP3W_UNSUPPORTED_MESSAGE_LENGTH
    );
    runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_ERROR_CODE_UNKNOWN_COMMAND;
    return 1;
}

static s32 runtime_transport_dispatch_cp3w_hello_session_request(void)
{
    u32 command = runtime_transport_cp3w_last_command;
    u32 payload_length = runtime_transport_cp3w_last_declared_payload_length;
    runtime_transport_cp3w_requests_dispatched += 1;
    runtime_transport_cp3w_last_dispatch_result = 0;
    runtime_transport_cp3w_runtime_build_id = RUNTIME_CP3W_RUNTIME_BUILD_ID;

    if (command == RUNTIME_CP3W_COMMAND_HELLO) {
        u32 selected_version = 0;
        u32 offered_capabilities = 0;
        u32 client_nonce = 0;
        u32 accepted_capabilities = 0;
        u32 runtime_capabilities = RUNTIME_CP3W_RUNTIME_CAPABILITIES;
        if (runtime_transport_is_cp3w_game_identity_mode() || runtime_transport_is_cp3w_inventory_mode()) {
            runtime_capabilities |= RUNTIME_CP3W_CAPABILITY_GAME_IDENTITY;
        }
        if (runtime_transport_is_cp3w_inventory_mode()) {
            runtime_capabilities |= RUNTIME_CP3W_CAPABILITY_INVENTORY_STATE;
        }
        runtime_transport_cp3w_hello_requests_received += 1;
        if (runtime_transport_validate_cp3w_hello_payload(payload_length) != 0) {
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD;
            return -1;
        }
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_PROCESS_HELLO, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        selected_version = RUNTIME_CP3W_SUPPORTED_PROTOCOL_VERSION;
        offered_capabilities = runtime_read_be32(runtime_transport_receive_payload_buffer + RUNTIME_CP3W_HEADER_SIZE + 2);
        client_nonce = runtime_read_be32(runtime_transport_receive_payload_buffer + RUNTIME_CP3W_HEADER_SIZE + 6);
        if (
            runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE] > selected_version
            || runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE + 1] < selected_version
            || runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE]
                > runtime_transport_receive_payload_buffer[RUNTIME_CP3W_HEADER_SIZE + 1]
        ) {
            runtime_transport_cp3w_hello_version_rejections += 1;
            runtime_transport_prepare_cp3w_error_response(
                runtime_transport_cp3w_last_request_id,
                command,
                RUNTIME_CP3W_ERROR_CODE_UNSUPPORTED_VERSION,
                runtime_cp3w_unsupported_version_message_ascii,
                RUNTIME_CP3W_UNSUPPORTED_VERSION_MESSAGE_LENGTH
            );
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_ERROR_CODE_UNSUPPORTED_VERSION;
            return 2;
        }

        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_NEGOTIATE_HELLO_VERSION, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        if (runtime_transport_cp3w_negotiated_flag == 0) {
            accepted_capabilities = offered_capabilities & runtime_capabilities;
            runtime_transport_copy_cp3w_hello_request_state(payload_length);
            runtime_transport_cp3w_runtime_capabilities = runtime_capabilities;
            runtime_transport_cp3w_accepted_capabilities = accepted_capabilities;
            runtime_transport_cp3w_selected_protocol_version = selected_version;
            runtime_transport_cp3w_session_id =
                runtime_transport_compute_cp3w_session_id(client_nonce, accepted_capabilities);
            runtime_transport_cp3w_negotiated_flag = 1;
            runtime_transport_cp3w_hello_successes += 1;
            runtime_transport_prepare_cp3w_hello_response(runtime_transport_cp3w_last_request_id);
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_FRAME_RESULT_VALID;
            return 3;
        }
        if (runtime_transport_cp3w_hello_request_matches_negotiated(payload_length) != 0) {
            runtime_transport_cp3w_hello_duplicate_requests += 1;
            runtime_transport_prepare_cp3w_hello_response(runtime_transport_cp3w_last_request_id);
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_COMMAND_HELLO;
            return 4;
        }

        runtime_transport_cp3w_hello_renegotiation_rejections += 1;
        runtime_transport_prepare_cp3w_error_response(
            runtime_transport_cp3w_last_request_id,
            command,
            RUNTIME_CP3W_ERROR_CODE_INVALID_STATE,
            runtime_cp3w_invalid_state_message_ascii,
            RUNTIME_CP3W_INVALID_STATE_MESSAGE_LENGTH
        );
        runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_ERROR_CODE_INVALID_STATE;
        return 5;
    }

    if (
        runtime_transport_cp3w_negotiated_flag == 0
        && (command == RUNTIME_CP3W_COMMAND_PING
            || command == RUNTIME_CP3W_COMMAND_READ_MEMORY
            || command == RUNTIME_CP3W_COMMAND_DISCONNECT
            || command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY
            || command == RUNTIME_CP3W_COMMAND_GET_INVENTORY)
    ) {
        runtime_transport_cp3w_pre_hello_gated_commands += 1;
        if (command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY) {
            runtime_transport_cp3w_game_identity_requests += 1;
            runtime_transport_cp3w_game_identity_pre_hello_rejections += 1;
            runtime_transport_cp3w_game_identity_last_request_id = runtime_transport_cp3w_last_request_id;
        }
        if (command == RUNTIME_CP3W_COMMAND_GET_INVENTORY) {
            runtime_transport_cp3w_inventory_requests += 1;
            runtime_transport_cp3w_inventory_pre_hello_rejections += 1;
            runtime_transport_cp3w_inventory_last_request_id = runtime_transport_cp3w_last_request_id;
        }
        runtime_transport_prepare_cp3w_error_response(
            runtime_transport_cp3w_last_request_id,
            command,
            RUNTIME_CP3W_ERROR_CODE_NOT_NEGOTIATED,
            command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY
                ? runtime_cp3w_identity_not_negotiated_message_ascii
                : command == RUNTIME_CP3W_COMMAND_GET_INVENTORY
                ? runtime_cp3w_inventory_not_negotiated_message_ascii
                : runtime_cp3w_not_negotiated_message_ascii,
            command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY
                ? RUNTIME_CP3W_IDENTITY_NOT_NEGOTIATED_MESSAGE_LENGTH
                : command == RUNTIME_CP3W_COMMAND_GET_INVENTORY
                ? RUNTIME_CP3W_INVENTORY_NOT_NEGOTIATED_MESSAGE_LENGTH
                : RUNTIME_CP3W_NOT_NEGOTIATED_MESSAGE_LENGTH
        );
        runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_ERROR_CODE_NOT_NEGOTIATED;
        return 6;
    }

    if (command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY) {
        u32 availability = 0;
        u32 game_state = 0;
        u32 inventory_root = 0;
        u32 state_manager_owner = 0;
        u32 player = 0;
        u32 player_vtable = 0;
        runtime_transport_cp3w_game_identity_requests += 1;
        runtime_transport_cp3w_game_identity_last_request_id = runtime_transport_cp3w_last_request_id;
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_VALIDATE_CAPABILITY,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        if ((runtime_transport_cp3w_accepted_capabilities & RUNTIME_CP3W_CAPABILITY_GAME_IDENTITY) == 0) {
            runtime_transport_cp3w_game_identity_capability_rejections += 1;
            runtime_transport_prepare_cp3w_error_response(
                runtime_transport_cp3w_last_request_id,
                command,
                RUNTIME_CP3W_ERROR_CODE_CAPABILITY_NOT_NEGOTIATED,
                runtime_cp3w_identity_capability_message_ascii,
                RUNTIME_CP3W_IDENTITY_CAPABILITY_MESSAGE_LENGTH
            );
            runtime_transport_cp3w_game_identity_last_status = RUNTIME_CP3W_RESPONSE_STATUS_ERROR;
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_ERROR_CODE_CAPABILITY_NOT_NEGOTIATED;
            return 8;
        }
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_VALIDATE_REQUEST,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        if (payload_length != 0) {
            runtime_transport_cp3w_game_identity_invalid_payload_rejections += 1;
            runtime_transport_prepare_cp3w_error_response(
                runtime_transport_cp3w_last_request_id,
                command,
                RUNTIME_CP3W_ERROR_CODE_INVALID_PAYLOAD_LENGTH,
                runtime_cp3w_identity_invalid_payload_message_ascii,
                RUNTIME_CP3W_IDENTITY_INVALID_PAYLOAD_MESSAGE_LENGTH
            );
            runtime_transport_cp3w_game_identity_last_status = RUNTIME_CP3W_RESPONSE_STATUS_ERROR;
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_ERROR_CODE_INVALID_PAYLOAD_LENGTH;
            return 9;
        }
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_VALIDATE_EXECUTABLE,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        runtime_transport_cp3w_game_identity_executable_validations += 1;
        runtime_transport_cp3w_game_identity_executable_recognized =
            runtime_transport_prime3_executable_recognized();
        if (runtime_transport_cp3w_game_identity_executable_recognized != 0) {
            availability |= RUNTIME_CP3W_AVAILABILITY_EXECUTABLE_RECOGNIZED;
            runtime_set_phase(
                RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_RESOLVE_GAME_STATE,
                RUNTIME_TRANSPORT_POLL_ACTION_WAIT
            );
            game_state = *(const volatile u32*)RUNTIME_PRIME3_NTSC_GAME_STATE_POINTER_ADDRESS;
            runtime_transport_cp3w_game_identity_game_state_pointer = game_state;
            if (runtime_transport_is_valid_mem1_range(game_state, 0x2CU)) {
                availability |= RUNTIME_CP3W_AVAILABILITY_GAME_STATE_POINTER_VALID;
                availability |= RUNTIME_CP3W_AVAILABILITY_WORLD_STATE_AVAILABLE;
                runtime_transport_cp3w_game_identity_game_state_valid += 1;
                inventory_root = *(const volatile u32*)(game_state + 0x24U);
                runtime_transport_cp3w_game_identity_inventory_root_pointer = inventory_root;
                if (runtime_transport_is_valid_mem1_range(inventory_root, 0x5CU)) {
                    availability |= RUNTIME_CP3W_AVAILABILITY_INVENTORY_ROOT_AVAILABLE;
                    runtime_transport_cp3w_game_identity_inventory_root_available += 1;
                }
            } else {
                runtime_transport_cp3w_game_identity_game_state_invalid += 1;
            }
            runtime_set_phase(
                RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_RESOLVE_PLAYER_STATE,
                RUNTIME_TRANSPORT_POLL_ACTION_WAIT
            );
            state_manager_owner = *(const volatile u32*)(RUNTIME_PRIME3_NTSC_CSTATE_MANAGER_GLOBAL_ADDRESS + 0x28U);
            if (runtime_transport_is_valid_mem1_range(state_manager_owner, 0x2188U)) {
                player = *(const volatile u32*)(state_manager_owner + 0x2184U);
                runtime_transport_cp3w_game_identity_player_state_pointer = player;
                if (runtime_transport_is_valid_mem1_range(player, 4U)) {
                    player_vtable = *(const volatile u32*)player;
                    if (player_vtable == RUNTIME_PRIME3_NTSC_CPLAYER_VTABLE) {
                        availability |= RUNTIME_CP3W_AVAILABILITY_PLAYER_STATE_POINTER_VALID;
                        runtime_transport_cp3w_game_identity_player_state_valid += 1;
                    } else {
                        runtime_transport_cp3w_game_identity_player_state_invalid += 1;
                    }
                } else {
                    runtime_transport_cp3w_game_identity_player_state_invalid += 1;
                }
            } else {
                runtime_transport_cp3w_game_identity_player_state_invalid += 1;
            }
        } else {
            runtime_transport_cp3w_game_identity_executable_failures += 1;
            runtime_transport_cp3w_game_identity_game_state_invalid += 1;
            runtime_transport_cp3w_game_identity_player_state_invalid += 1;
        }
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_BUILD_RESPONSE,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        runtime_transport_prepare_cp3w_game_identity_response(
            runtime_transport_cp3w_last_request_id,
            availability
        );
        runtime_transport_cp3w_game_identity_successes += 1;
        runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_FRAME_RESULT_VALID;
        return 10;
    }

    if (command == RUNTIME_CP3W_COMMAND_GET_INVENTORY) {
        u32 availability = 0;
        u32 game_state = 0;
        u32 inventory_root = 0;
        runtime_transport_cp3w_inventory_requests += 1;
        runtime_transport_cp3w_inventory_last_request_id = runtime_transport_cp3w_last_request_id;
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_VALIDATE_CAPABILITY,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        if ((runtime_transport_cp3w_accepted_capabilities & RUNTIME_CP3W_CAPABILITY_INVENTORY_STATE) == 0) {
            runtime_transport_cp3w_inventory_capability_rejections += 1;
            runtime_transport_prepare_cp3w_error_response(
                runtime_transport_cp3w_last_request_id,
                command,
                RUNTIME_CP3W_ERROR_CODE_CAPABILITY_NOT_NEGOTIATED,
                runtime_cp3w_inventory_capability_message_ascii,
                RUNTIME_CP3W_INVENTORY_CAPABILITY_MESSAGE_LENGTH
            );
            runtime_transport_cp3w_inventory_last_status = RUNTIME_CP3W_RESPONSE_STATUS_ERROR;
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_ERROR_CODE_CAPABILITY_NOT_NEGOTIATED;
            return 11;
        }
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_VALIDATE_REQUEST,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        if (payload_length != 0) {
            runtime_transport_cp3w_inventory_invalid_payload_rejections += 1;
            runtime_transport_prepare_cp3w_error_response(
                runtime_transport_cp3w_last_request_id,
                command,
                RUNTIME_CP3W_ERROR_CODE_INVALID_PAYLOAD_LENGTH,
                runtime_cp3w_inventory_invalid_payload_message_ascii,
                RUNTIME_CP3W_INVENTORY_INVALID_PAYLOAD_MESSAGE_LENGTH
            );
            runtime_transport_cp3w_inventory_last_status = RUNTIME_CP3W_RESPONSE_STATUS_ERROR;
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_ERROR_CODE_INVALID_PAYLOAD_LENGTH;
            return 12;
        }
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_VALIDATE_IDENTITY,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        if (runtime_transport_prime3_executable_recognized() != 0) {
            availability |= RUNTIME_CP3W_INVENTORY_AVAILABILITY_EXECUTABLE_RECOGNIZED;
            runtime_set_phase(
                RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_RESOLVE_GAME_STATE,
                RUNTIME_TRANSPORT_POLL_ACTION_WAIT
            );
            game_state = *(const volatile u32*)RUNTIME_PRIME3_NTSC_GAME_STATE_POINTER_ADDRESS;
            if (runtime_transport_is_valid_mem1_range(game_state, 0x28U)) {
                availability |= RUNTIME_CP3W_INVENTORY_AVAILABILITY_GAME_STATE_POINTER_VALID;
                runtime_transport_cp3w_inventory_game_state_valid += 1;
                runtime_set_phase(
                    RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_RESOLVE_ROOT,
                    RUNTIME_TRANSPORT_POLL_ACTION_WAIT
                );
                inventory_root = *(const volatile u32*)(game_state + 0x24U);
                runtime_transport_cp3w_inventory_last_root = inventory_root;
                if (runtime_transport_is_valid_mem1_range(inventory_root, 4U)) {
                    availability |= RUNTIME_CP3W_INVENTORY_AVAILABILITY_ROOT_VALID;
                    runtime_transport_cp3w_inventory_root_valid += 1;
                    runtime_set_phase(
                        RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_VALIDATE_RANGE,
                        RUNTIME_TRANSPORT_POLL_ACTION_WAIT
                    );
                    if (runtime_transport_is_valid_mem1_range(inventory_root, 0x398U)) {
                        availability |= RUNTIME_CP3W_INVENTORY_AVAILABILITY_RANGE_VALID;
                    } else {
                        runtime_transport_cp3w_inventory_range_failures += 1;
                    }
                } else {
                    runtime_transport_cp3w_inventory_root_invalid += 1;
                }
            } else {
                runtime_transport_cp3w_inventory_game_state_invalid += 1;
            }
        } else {
            runtime_transport_cp3w_inventory_executable_failures += 1;
        }
        runtime_transport_cp3w_inventory_snapshot_sequence += 1;
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_BUILD_RESPONSE,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        availability = runtime_transport_prepare_cp3w_inventory_response(
            runtime_transport_cp3w_last_request_id,
            game_state,
            inventory_root,
            availability,
            runtime_transport_cp3w_inventory_snapshot_sequence
        );
        runtime_transport_cp3w_inventory_last_availability = availability;
        runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_FRAME_RESULT_VALID;
        return 13;
    }

    if (command == RUNTIME_CP3W_COMMAND_PING) {
        if (payload_length > RUNTIME_CP3W_MAX_PING_PAYLOAD_LENGTH) {
            runtime_transport_record_cp3w_frame_result(RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD);
            runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_FRAME_RESULT_INVALID_PAYLOAD;
            return -1;
        }
        runtime_transport_cp3w_ping_requests_received += 1;
        runtime_transport_cp3w_last_ping_payload_length = payload_length;
        runtime_transport_prepare_cp3w_ping_response(runtime_transport_cp3w_last_request_id, payload_length);
        runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_FRAME_RESULT_VALID;
        return 1;
    }

    if (command == RUNTIME_CP3W_COMMAND_DISCONNECT) {
        runtime_transport_cp3w_negotiated_flag = 0;
        runtime_transport_cp3w_accepted_capabilities = 0;
        runtime_transport_cp3w_selected_protocol_version = 0;
        runtime_transport_cp3w_session_id = 0;
        runtime_transport_cp3w_client_nonce = 0;
        runtime_transport_cp3w_hello_client_name_length = 0;
        runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_FRAME_RESULT_VALID;
        return 14;
    }

    runtime_transport_cp3w_unsupported_commands_received += 1;
    runtime_transport_prepare_cp3w_error_response(
        runtime_transport_cp3w_last_request_id,
        command,
        RUNTIME_CP3W_ERROR_CODE_UNKNOWN_COMMAND,
        runtime_cp3w_unsupported_message_ascii,
        RUNTIME_CP3W_UNSUPPORTED_MESSAGE_LENGTH
    );
    runtime_transport_cp3w_last_dispatch_result = RUNTIME_CP3W_ERROR_CODE_UNKNOWN_COMMAND;
    return 7;
}

static s32 runtime_transport_dispatch_cp3w_game_identity_request(void)
{
    return runtime_transport_dispatch_cp3w_hello_session_request();
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

#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
static void runtime_instruction_cache_sync(const volatile void* address, u32 size)
{
    u32 aligned = (u32)address & ~31U;
    u32 end = ((u32)address + size + 31U) & ~31U;
    while (aligned < end) {
        __asm__ volatile("dcbf 0,%0" : : "r"(aligned) : "memory");
        aligned += 32;
    }
    __asm__ volatile("sync" ::: "memory");
    aligned = (u32)address & ~31U;
    while (aligned < end) {
        __asm__ volatile("icbi 0,%0" : : "r"(aligned) : "memory");
        aligned += 32;
    }
    __asm__ volatile("sync; isync" ::: "memory");
}

static void runtime_native_install_post_copy_hook(void)
{
    volatile u32* hook = (volatile u32*)RUNTIME_NATIVE_POST_COPY_HOOK_ADDRESS;
    s32 displacement = (s32)((u32)runtime_native_post_copy_wrapper - RUNTIME_NATIVE_POST_COPY_HOOK_ADDRESS);
    if (*hook != RUNTIME_NATIVE_POST_COPY_HOOK_EXPECTED) {
        runtime_native_post_copy_hook_result = -1;
        return;
    }
    if (
        (displacement & 3) != 0
        || displacement < -0x02000000
        || displacement > 0x01FFFFFC
    ) {
        runtime_native_post_copy_hook_result = -2;
        return;
    }
    *hook = 0x48000000U | ((u32)displacement & 0x03FFFFFCU);
    runtime_instruction_cache_sync(hook, sizeof(*hook));
    runtime_native_post_copy_hook_result = 1;
}
#endif

static volatile runtime_operation_context* runtime_context_for_operation(u32 operation)
{
    if (operation == RUNTIME_TRANSPORT_OP_NWC24_STARTUP) {
        return &runtime_transport_nwc24_context;
    }
    if (operation == RUNTIME_TRANSPORT_OP_CLOSE_KD) {
        return &runtime_transport_kd_close_context;
    }
    if (operation == RUNTIME_TRANSPORT_OP_OPEN_IP) {
        return &runtime_transport_open_ip_context;
    }
    if (operation == RUNTIME_TRANSPORT_OP_STARTUP) {
        return &runtime_transport_startup_context;
    }
    if (operation == RUNTIME_TRANSPORT_OP_GETHOSTID) {
        return &runtime_transport_get_host_id_context;
    }
    if (operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET) {
        return &runtime_transport_socket_context;
    }
    if (operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET) {
        return &runtime_transport_bind_context;
    }
    if (
        operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE
        || operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_FOR_RECOVERY
        || operation == RUNTIME_TRANSPORT_OP_GETSOCKNAME
    ) {
        return &runtime_transport_cleanup_close_context;
    }
    if (operation == RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET) {
        return &runtime_transport_receive_context;
    }
    if (operation == RUNTIME_TRANSPORT_OP_TCP_ECHO_RECEIVE) {
        return &runtime_tcp_echo_receive_context;
    }
    if (operation == RUNTIME_TRANSPORT_OP_SEND_SOCKET || operation == RUNTIME_TRANSPORT_OP_TCP_SEND) {
        return &runtime_transport_send_context;
    }
    return 0;
}

static void runtime_sync_context_for_operation(u32 operation)
{
    if (operation == RUNTIME_TRANSPORT_OP_OPEN_IP) {
        runtime_sync_open_ip_context_evidence();
    } else if (operation == RUNTIME_TRANSPORT_OP_STARTUP) {
        runtime_sync_startup_context_evidence();
    } else if (operation == RUNTIME_TRANSPORT_OP_GETHOSTID) {
        runtime_sync_get_host_id_context_evidence();
    } else if (operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET) {
        runtime_sync_socket_context_evidence();
    } else if (operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET) {
        runtime_sync_bind_context_evidence();
    } else if (
        operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE
        || operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_FOR_RECOVERY
        || operation == RUNTIME_TRANSPORT_OP_GETSOCKNAME
    ) {
        runtime_sync_cleanup_close_context_evidence();
    } else if (operation == RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET) {
        runtime_sync_receive_context_evidence();
    } else if (operation == RUNTIME_TRANSPORT_OP_TCP_ECHO_RECEIVE) {
        runtime_tcp_echo_receive_callback_count = runtime_tcp_echo_receive_context.callback_exit_count;
    } else if (operation == RUNTIME_TRANSPORT_OP_SEND_SOCKET || operation == RUNTIME_TRANSPORT_OP_TCP_SEND) {
        runtime_sync_send_context_evidence();
    }
}

#if PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
static s32 runtime_ios_callback(s32 result, void* usrdata) __attribute_section_code__;

static s32 runtime_ios_callback(s32 result, void* usrdata)
{
    volatile runtime_operation_context* context = runtime_context_for_operation(runtime_transport_pending_operation);
    if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_NONE) {
        runtime_transport_rejected_callback_count += 1;
        return 0;
    }
    if (runtime_transport_callback_pending != 0) {
        if (context != 0 && usrdata == (void*)context) {
            context->duplicate_callback_count += 1;
            runtime_sync_context_for_operation(runtime_transport_pending_operation);
        }
        runtime_transport_rejected_callback_count += 1;
        return 0;
    }
    runtime_diag_increment(&runtime_callback_entry_count);
    if (context != 0) {
        if (usrdata != (void*)context) {
            context->stale_callback_count += 1;
            runtime_sync_context_for_operation(runtime_transport_pending_operation);
            runtime_transport_rejected_callback_count += 1;
            return 0;
        }
        context->callback_entry_count += 1;
        if (context->expected_generation != runtime_transport_pending_generation) {
            context->stale_callback_count += 1;
            runtime_sync_context_for_operation(runtime_transport_pending_operation);
            runtime_transport_rejected_callback_count += 1;
            return 0;
        }
        if (context->completion_flag != 0) {
            context->duplicate_callback_count += 1;
            runtime_sync_context_for_operation(runtime_transport_pending_operation);
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
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_STARTUP) {
        runtime_transport_startup_context.callback_exit_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_GETHOSTID) {
        runtime_transport_get_host_id_context.callback_exit_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET) {
        runtime_transport_socket_context.callback_exit_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET) {
        runtime_transport_bind_context.callback_exit_count += 1;
    } else if (
        runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE
        || runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_FOR_RECOVERY
        || runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_GETSOCKNAME
    ) {
        runtime_transport_cleanup_close_context.callback_exit_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET) {
        runtime_transport_receive_context.callback_exit_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_TCP_ECHO_RECEIVE) {
        runtime_tcp_echo_receive_context.callback_exit_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_SEND_SOCKET) {
        runtime_transport_send_context.callback_exit_count += 1;
    }
    runtime_sync_context_for_operation(runtime_transport_pending_operation);
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
                || runtime_transport_is_nwc24_close_open_ip_startup_once_mode()
                || runtime_transport_is_get_host_id_once_mode()
                || runtime_transport_is_create_socket_once_mode()
                || runtime_transport_is_bind_once_mode()
                || runtime_transport_is_native_wc24_bootstrap_mode()
                || runtime_transport_uses_receive_mode())
            || runtime_transport_ip_fd != -1
            || (
                runtime_transport_uses_receive_mode()
                    ? (runtime_transport_kd_fd != -1 || runtime_transport_kd_closed != 0)
                    : (runtime_transport_kd_fd != -1 || runtime_transport_kd_closed == 0)
            )
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
            || runtime_transport_is_nwc24_close_open_ip_startup_once_mode()
            || runtime_transport_is_get_host_id_once_mode()
            || runtime_transport_is_create_socket_once_mode()
            || runtime_transport_is_bind_once_mode()
            || runtime_transport_is_native_wc24_bootstrap_mode()
            || runtime_transport_uses_receive_mode())
        || operation != RUNTIME_TRANSPORT_OP_CLOSE_KD
        || fd < 0
        || fd != runtime_transport_kd_fd
        || runtime_transport_kd_closed != 0
        || runtime_transport_nwc24_callback_count == 0
        || runtime_transport_nwc24_callback_count != runtime_transport_nwc24_submit_count
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
                || runtime_transport_is_nwc24_close_open_ip_startup_once_mode()
                || runtime_transport_is_get_host_id_once_mode()
                || runtime_transport_is_create_socket_once_mode()
                || runtime_transport_is_bind_once_mode()
                || runtime_transport_is_native_wc24_bootstrap_mode()
                || runtime_transport_uses_receive_mode())
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
            !(runtime_transport_is_startup_once_mode()
                || runtime_transport_is_nwc24_close_open_ip_startup_once_mode()
                || runtime_transport_is_get_host_id_once_mode()
                || runtime_transport_is_create_socket_once_mode()
                || runtime_transport_is_bind_once_mode()
                || runtime_transport_is_native_wc24_bootstrap_mode()
                || runtime_transport_uses_receive_mode())
            || fd < 0
            || fd != runtime_transport_ip_fd
            || ioctl != IOCTL_SO_STARTUP
            || buffer_in != 0
            || len_in != 0
            || buffer_io != 0
            || len_io != 0
            || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
            || runtime_transport_startup_submit_count == 0
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
    } else if (operation == RUNTIME_TRANSPORT_OP_GETHOSTID) {
        if (
            !(runtime_transport_is_get_host_id_once_mode()
                || runtime_transport_is_create_socket_once_mode()
                || runtime_transport_is_bind_once_mode()
                || runtime_transport_is_native_wc24_bootstrap_mode()
                || runtime_transport_uses_receive_mode())
            || fd < 0
            || fd != runtime_transport_ip_fd
            || ioctl != IOCTL_SO_GETHOSTID
            || buffer_in != 0
            || len_in != 0
            || buffer_io != 0
            || len_io != 0
            || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
            || runtime_transport_get_host_id_submit_count == 0
            || runtime_transport_kd_fd != -1
            || runtime_transport_kd_closed == 0
            || runtime_transport_service_started == 0
        ) {
            runtime_transport_last_ios_result = -1;
            runtime_transport_last_submit_result = -1;
            runtime_record_submit_evidence(operation, -1, runtime_transport_pending_generation);
            runtime_diag_record_submit_return(-1);
            return -1;
        }
        runtime_transport_get_host_id_target_address = RUNTIME_VERIFIED_IOS_IOCTL_ASYNC_ADDRESS;
        runtime_transport_get_host_id_command = (u32)ioctl;
        runtime_transport_get_host_id_submitted_fd = fd;
        runtime_transport_get_host_id_callback_pointer = (u32)runtime_ios_callback;
        runtime_transport_get_host_id_context_pointer = (u32)&runtime_transport_get_host_id_context;
        runtime_transport_get_host_id_service_started_before_submit = runtime_transport_service_started;
        runtime_transport_ip_fd_before_get_host_id = runtime_transport_ip_fd;
        runtime_transport_get_host_id_pending_before_submit = runtime_transport_pending_operation;
        runtime_transport_get_host_id_phase_before_submit = runtime_transport_phase;
        runtime_transport_get_host_id_pre_call_args[0] = (u32)fd;
        runtime_transport_get_host_id_pre_call_args[1] = (u32)ioctl;
        runtime_transport_get_host_id_pre_call_args[2] = (u32)buffer_in;
        runtime_transport_get_host_id_pre_call_args[3] = (u32)len_in;
        runtime_transport_get_host_id_pre_call_args[4] = (u32)buffer_io;
        runtime_transport_get_host_id_pre_call_args[5] = (u32)len_io;
        runtime_transport_get_host_id_pre_call_args[6] = (u32)runtime_ios_callback;
        runtime_transport_get_host_id_pre_call_args[7] = (u32)&runtime_transport_get_host_id_context;
        runtime_memzero(&runtime_transport_get_host_id_context, sizeof(runtime_transport_get_host_id_context));
        runtime_transport_get_host_id_context.expected_generation = runtime_transport_pending_generation + 1;
        runtime_sync_get_host_id_context_evidence();
    } else if (operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET) {
        if (
            !(
                runtime_transport_is_create_socket_once_mode()
                || runtime_transport_is_bind_once_mode()
                || runtime_transport_is_native_wc24_bootstrap_mode()
                || runtime_transport_uses_receive_mode()
            )
            || fd < 0
            || fd != runtime_transport_ip_fd
            || ioctl != IOCTL_SO_SOCKET
            || buffer_in != &runtime_transport_socket_request
            || len_in != RUNTIME_SOCKET_REQUEST_LOGICAL_SIZE
            || buffer_io != 0
            || len_io != 0
            || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
            || runtime_transport_socket_submit_count == 0
            || runtime_transport_get_host_id_callback_count == 0
            || runtime_transport_get_host_id_callback_count != runtime_transport_get_host_id_submit_count
            || runtime_transport_host_id_available == 0
            || runtime_transport_host_id_ready == 0
            || runtime_transport_service_started == 0
            || runtime_transport_kd_fd != -1
            || runtime_transport_kd_closed == 0
            || runtime_transport_socket_fd != -1
        ) {
            runtime_transport_last_ios_result = -1;
            runtime_transport_last_submit_result = -1;
            runtime_record_submit_evidence(operation, -1, runtime_transport_pending_generation);
            runtime_diag_record_submit_return(-1);
            return -1;
        }
        runtime_transport_socket_target_address = RUNTIME_VERIFIED_IOS_IOCTL_ASYNC_ADDRESS;
        runtime_transport_socket_command = (u32)ioctl;
        runtime_transport_socket_submitted_fd = fd;
        runtime_transport_socket_callback_pointer = (u32)runtime_ios_callback;
        runtime_transport_socket_context_pointer = (u32)&runtime_transport_socket_context;
        runtime_transport_socket_fd_before_submit = runtime_transport_socket_fd;
        runtime_transport_socket_request_address = (u32)&runtime_transport_socket_request;
        runtime_transport_socket_request_storage_size = sizeof(runtime_transport_socket_request);
        runtime_transport_socket_request_logical_size = RUNTIME_SOCKET_REQUEST_LOGICAL_SIZE;
        runtime_transport_socket_request_alignment = 0x20;
        runtime_transport_socket_family_value = runtime_transport_socket_request.family;
        runtime_transport_socket_type_value = runtime_transport_socket_request.type;
        runtime_transport_socket_protocol_value = runtime_transport_socket_request.protocol;
        runtime_memcpy(
            runtime_transport_socket_request_bytes,
            (volatile const void*)&runtime_transport_socket_request,
            RUNTIME_SOCKET_REQUEST_LOGICAL_SIZE
        );
        runtime_transport_socket_pre_call_args[0] = (u32)fd;
        runtime_transport_socket_pre_call_args[1] = (u32)ioctl;
        runtime_transport_socket_pre_call_args[2] = (u32)buffer_in;
        runtime_transport_socket_pre_call_args[3] = (u32)len_in;
        runtime_transport_socket_pre_call_args[4] = (u32)buffer_io;
        runtime_transport_socket_pre_call_args[5] = (u32)len_io;
        runtime_transport_socket_pre_call_args[6] = (u32)runtime_ios_callback;
        runtime_transport_socket_pre_call_args[7] = (u32)&runtime_transport_socket_context;
        runtime_memzero(&runtime_transport_socket_context, sizeof(runtime_transport_socket_context));
        runtime_transport_socket_context.expected_generation = runtime_transport_pending_generation + 1;
        runtime_sync_socket_context_evidence();
    } else if (operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET) {
        if (
            !(runtime_transport_is_bind_once_mode()
                || runtime_transport_uses_receive_mode())
            || fd < 0
            || fd != runtime_transport_ip_fd
            || ioctl != IOCTL_SO_CONNECT
            || buffer_in != &runtime_transport_bind_params
            || len_in != 32
            || buffer_io != 0
            || len_io != 0
            || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
            || runtime_transport_bind_submit_count == 0
            || runtime_transport_socket_ready == 0
            || runtime_transport_socket_fd < 0
            || runtime_transport_get_host_id_callback_count == 0
            || runtime_transport_get_host_id_callback_count != runtime_transport_get_host_id_submit_count
            || runtime_transport_host_id_ready == 0
            || runtime_transport_service_started == 0
            || runtime_transport_kd_fd != -1
            || runtime_transport_kd_closed == 0
        ) {
            runtime_transport_last_ios_result = -1;
            runtime_transport_last_submit_result = -1;
            runtime_record_submit_evidence(operation, -1, runtime_transport_pending_generation);
            runtime_diag_record_submit_return(-1);
            return -1;
        }
        runtime_transport_bind_target_address = RUNTIME_VERIFIED_IOS_IOCTL_ASYNC_ADDRESS;
        runtime_transport_bind_command = (u32)ioctl;
        runtime_transport_bind_submitted_fd = fd;
        runtime_transport_bind_callback_pointer = (u32)runtime_ios_callback;
        runtime_transport_bind_context_pointer = (u32)&runtime_transport_bind_context;
        runtime_transport_bind_request_address = (u32)&runtime_transport_bind_params;
        runtime_transport_bind_request_storage_size = sizeof(runtime_transport_bind_params);
        runtime_transport_bind_request_logical_size = 32;
        runtime_transport_bind_request_alignment = 0x20;
        runtime_transport_bind_sockaddr_length = runtime_transport_bind_params.address[0];
        runtime_transport_bind_family_value = runtime_transport_bind_params.address[1];
        runtime_transport_bind_port_value =
            ((u32)runtime_transport_bind_params.address[2] << 8) | (u32)runtime_transport_bind_params.address[3];
        runtime_transport_bind_address_value =
            ((u32)runtime_transport_bind_params.address[4] << 24) | ((u32)runtime_transport_bind_params.address[5] << 16)
            | ((u32)runtime_transport_bind_params.address[6] << 8) | (u32)runtime_transport_bind_params.address[7];
        runtime_memcpy(
            runtime_transport_bind_request_bytes,
            (volatile const void*)&runtime_transport_bind_params,
            36
        );
        runtime_transport_bind_pre_call_args[0] = (u32)fd;
        runtime_transport_bind_pre_call_args[1] = (u32)ioctl;
        runtime_transport_bind_pre_call_args[2] = (u32)buffer_in;
        runtime_transport_bind_pre_call_args[3] = (u32)len_in;
        runtime_transport_bind_pre_call_args[4] = (u32)buffer_io;
        runtime_transport_bind_pre_call_args[5] = (u32)len_io;
        runtime_transport_bind_pre_call_args[6] = (u32)runtime_ios_callback;
        runtime_transport_bind_pre_call_args[7] = (u32)&runtime_transport_bind_context;
        runtime_memzero(&runtime_transport_bind_context, sizeof(runtime_transport_bind_context));
        runtime_transport_bind_context.expected_generation = runtime_transport_pending_generation + 1;
        runtime_sync_bind_context_evidence();
    } else if (operation == RUNTIME_TRANSPORT_OP_GETSOCKNAME) {
        if (
            !runtime_transport_uses_receive_mode()
            || fd < 0
            || fd != runtime_transport_ip_fd
            || ioctl != IOCTL_SO_GETSOCKNAME
            || buffer_in != &runtime_transport_getsockname_request
            || len_in != 4
            || buffer_io != runtime_transport_getsockname_address
            || len_io != RUNTIME_WII_SOCKADDR_IN_SIZE
            || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
            || runtime_transport_socket_fd < 0
            || runtime_transport_bound_flag == 0
        ) {
            runtime_transport_last_ios_result = -1;
            runtime_transport_last_submit_result = -1;
            return -1;
        }
        runtime_memzero(&runtime_transport_cleanup_close_context, sizeof(runtime_transport_cleanup_close_context));
        runtime_transport_cleanup_close_context.expected_generation = runtime_transport_pending_generation + 1;
    } else if (
        operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE
        || operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_FOR_RECOVERY
    ) {
        if (
            !(runtime_transport_is_bind_once_mode()
                || runtime_transport_uses_receive_mode())
            || fd < 0
            || fd != runtime_transport_ip_fd
            || ioctl != IOCTL_SO_CLOSE
            || buffer_in != &runtime_transport_cleanup_close_request
            || len_in != 4
            || buffer_io != 0
            || len_io != 0
            || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
            || runtime_transport_socket_fd < 0
        ) {
            runtime_transport_last_ios_result = -1;
            runtime_transport_last_submit_result = -1;
            runtime_record_submit_evidence(operation, -1, runtime_transport_pending_generation);
            runtime_diag_record_submit_return(-1);
            return -1;
        }
        runtime_transport_cleanup_close_target_address = RUNTIME_VERIFIED_IOS_IOCTL_ASYNC_ADDRESS;
        runtime_transport_cleanup_close_command = (u32)ioctl;
        runtime_transport_cleanup_close_submitted_fd = fd;
        runtime_transport_cleanup_close_callback_pointer = (u32)runtime_ios_callback;
        runtime_transport_cleanup_close_context_pointer = (u32)&runtime_transport_cleanup_close_context;
        runtime_transport_cleanup_close_request_address = (u32)&runtime_transport_cleanup_close_request;
        runtime_transport_cleanup_close_request_storage_size = sizeof(runtime_transport_cleanup_close_request);
        runtime_transport_cleanup_close_request_logical_size = 4;
        runtime_transport_cleanup_close_request_alignment = 0x20;
        runtime_transport_cleanup_close_request_value = runtime_transport_cleanup_close_request;
        runtime_memcpy(
            runtime_transport_cleanup_close_request_bytes,
            (volatile const void*)&runtime_transport_cleanup_close_request,
            4
        );
        runtime_transport_cleanup_close_pre_call_args[0] = (u32)fd;
        runtime_transport_cleanup_close_pre_call_args[1] = (u32)ioctl;
        runtime_transport_cleanup_close_pre_call_args[2] = (u32)buffer_in;
        runtime_transport_cleanup_close_pre_call_args[3] = (u32)len_in;
        runtime_transport_cleanup_close_pre_call_args[4] = (u32)buffer_io;
        runtime_transport_cleanup_close_pre_call_args[5] = (u32)len_io;
        runtime_transport_cleanup_close_pre_call_args[6] = (u32)runtime_ios_callback;
        runtime_transport_cleanup_close_pre_call_args[7] = (u32)&runtime_transport_cleanup_close_context;
        runtime_memzero(&runtime_transport_cleanup_close_context, sizeof(runtime_transport_cleanup_close_context));
        runtime_transport_cleanup_close_context.expected_generation = runtime_transport_pending_generation + 1;
        runtime_sync_cleanup_close_context_evidence();
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
    } else if (operation == RUNTIME_TRANSPORT_OP_STARTUP) {
        runtime_transport_startup_context.expected_generation = runtime_transport_pending_generation;
        runtime_transport_startup_context.completion_generation = 0;
        runtime_transport_startup_context.completion_flag = 0;
        runtime_transport_startup_context.completion_result = 0;
        runtime_transport_startup_context.callback_entry_count = 0;
        runtime_transport_startup_context.callback_exit_count = 0;
        runtime_transport_startup_context.stale_callback_count = 0;
        runtime_transport_startup_context.duplicate_callback_count = 0;
    } else if (operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET) {
        runtime_transport_socket_context.expected_generation = runtime_transport_pending_generation;
        runtime_transport_socket_context.completion_generation = 0;
        runtime_transport_socket_context.completion_flag = 0;
        runtime_transport_socket_context.completion_result = 0;
        runtime_transport_socket_context.callback_entry_count = 0;
        runtime_transport_socket_context.callback_exit_count = 0;
        runtime_transport_socket_context.stale_callback_count = 0;
        runtime_transport_socket_context.duplicate_callback_count = 0;
    } else if (operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET) {
        runtime_transport_bind_context.expected_generation = runtime_transport_pending_generation;
        runtime_transport_bind_context.completion_generation = 0;
        runtime_transport_bind_context.completion_flag = 0;
        runtime_transport_bind_context.completion_result = 0;
        runtime_transport_bind_context.callback_entry_count = 0;
        runtime_transport_bind_context.callback_exit_count = 0;
        runtime_transport_bind_context.stale_callback_count = 0;
        runtime_transport_bind_context.duplicate_callback_count = 0;
    } else if (
        operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE
        || operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_FOR_RECOVERY
        || operation == RUNTIME_TRANSPORT_OP_GETSOCKNAME
    ) {
        runtime_transport_cleanup_close_context.expected_generation = runtime_transport_pending_generation;
        runtime_transport_cleanup_close_context.completion_generation = 0;
        runtime_transport_cleanup_close_context.completion_flag = 0;
        runtime_transport_cleanup_close_context.completion_result = 0;
        runtime_transport_cleanup_close_context.callback_entry_count = 0;
        runtime_transport_cleanup_close_context.callback_exit_count = 0;
        runtime_transport_cleanup_close_context.stale_callback_count = 0;
        runtime_transport_cleanup_close_context.duplicate_callback_count = 0;
    } else {
        runtime_transport_get_host_id_context.expected_generation = runtime_transport_pending_generation;
        runtime_transport_get_host_id_context.completion_generation = 0;
        runtime_transport_get_host_id_context.completion_flag = 0;
        runtime_transport_get_host_id_context.completion_result = 0;
        runtime_transport_get_host_id_context.callback_entry_count = 0;
        runtime_transport_get_host_id_context.callback_exit_count = 0;
        runtime_transport_get_host_id_context.stale_callback_count = 0;
        runtime_transport_get_host_id_context.duplicate_callback_count = 0;
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
            ? (void*)&runtime_transport_nwc24_context
            : operation == RUNTIME_TRANSPORT_OP_STARTUP
                ? (void*)&runtime_transport_startup_context
                : operation == RUNTIME_TRANSPORT_OP_GETHOSTID
                    ? (void*)&runtime_transport_get_host_id_context
                    : operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET
                        ? (void*)&runtime_transport_socket_context
                        : operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET
                            ? (void*)&runtime_transport_bind_context
                            : (void*)&runtime_transport_cleanup_close_context
    );
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_record_submit_evidence(operation, result, runtime_transport_pending_generation);
    runtime_diag_record_submit_return(result);
    if (
        (operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET && result != 0)
        || (operation != RUNTIME_TRANSPORT_OP_CREATE_SOCKET && result != 0)
    ) {
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        return -1;
    }
    runtime_set_phase(next_phase, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
    return 0;
}

static s32 runtime_submit_ioctlv_receive(u32 next_phase)
{
    s32 result = 0;
    runtime_diag_increment(&runtime_ios_submit_attempt_count);
    runtime_diag_increment(&runtime_c_before_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL);
    if (
        !runtime_transport_uses_receive_mode()
        || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
        || runtime_transport_ip_fd < 0
        || runtime_transport_socket_fd < 0
        || runtime_transport_socket_ready == 0
        || runtime_transport_host_id_ready == 0
        || runtime_transport_bound_flag == 0
        || runtime_transport_receive_submit_count == 0
        || runtime_transport_receive_submit_count != runtime_transport_receive_arm_count
    ) {
        runtime_transport_last_ios_result = -1;
        runtime_transport_last_submit_result = -1;
        runtime_transport_receive_submit_result = -1;
        runtime_transport_receive_submit_result_u32 = 0xFFFFFFFFU;
        runtime_record_submit_evidence(RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET, -1, runtime_transport_pending_generation);
        runtime_diag_record_submit_return(-1);
        return -1;
    }

    runtime_memzero(&runtime_transport_receive_request, sizeof(runtime_transport_receive_request));
    runtime_memzero(runtime_transport_receive_vectors, sizeof(runtime_transport_receive_vectors));
    runtime_memzero(runtime_transport_receive_payload_buffer, sizeof(runtime_transport_receive_payload_buffer));
    runtime_transport_receive_request.socket = runtime_transport_socket_fd;
    runtime_transport_receive_request.flags = 0;
    runtime_transport_receive_vectors[0].data = (void*)&runtime_transport_receive_request;
    runtime_transport_receive_vectors[0].len = RUNTIME_RECEIVE_REQUEST_LOGICAL_SIZE;
    runtime_transport_receive_vectors[1].data = (void*)runtime_transport_receive_payload_buffer;
    runtime_transport_receive_vectors[1].len = RUNTIME_UDP_RECEIVE_CAPACITY;

    runtime_transport_receive_target_address = PRIME3_RETAIL_IOS_IOCTLV_ASYNC_ADDRESS;
    runtime_transport_receive_command = IOCTLV_SO_RECVFROM;
    runtime_transport_receive_submitted_fd = runtime_transport_ip_fd;
    runtime_transport_receive_submitted_socket = runtime_transport_socket_fd;
    runtime_transport_receive_input_vector_count = RUNTIME_RECEIVE_INPUT_VECTOR_COUNT;
    runtime_transport_receive_output_vector_count = RUNTIME_RECEIVE_OUTPUT_VECTOR_COUNT;
    runtime_transport_receive_request_address = (u32)&runtime_transport_receive_request;
    runtime_transport_receive_request_storage_size = sizeof(runtime_transport_receive_request);
    runtime_transport_receive_request_logical_size = RUNTIME_RECEIVE_REQUEST_LOGICAL_SIZE;
    runtime_transport_receive_request_alignment = 0x20;
    runtime_transport_receive_request_flags = 0;
    runtime_transport_receive_vector_address = (u32)runtime_transport_receive_vectors;
    runtime_transport_receive_vector_storage_size = sizeof(runtime_transport_receive_vectors);
    runtime_transport_receive_vector_logical_size = RUNTIME_RECEIVE_VECTOR_COUNT * sizeof(runtime_ioctlv);
    runtime_transport_receive_vector_alignment = 0x20;
    runtime_transport_receive_vector_0_pointer = (u32)runtime_transport_receive_vectors[0].data;
    runtime_transport_receive_vector_0_length = runtime_transport_receive_vectors[0].len;
    runtime_transport_receive_vector_1_pointer = (u32)runtime_transport_receive_vectors[1].data;
    runtime_transport_receive_vector_1_length = runtime_transport_receive_vectors[1].len;
    runtime_transport_receive_vector_2_pointer = 0;
    runtime_transport_receive_vector_2_length = 0;
    runtime_transport_receive_payload_buffer_address = (u32)runtime_transport_receive_payload_buffer;
    runtime_transport_receive_payload_capacity = RUNTIME_UDP_RECEIVE_CAPACITY;
    runtime_transport_receive_payload_alignment = 0x20;
    runtime_transport_receive_source_address = 0;
    runtime_transport_receive_source_logical_size = 0;
    runtime_transport_receive_source_alignment = 0;
    runtime_transport_receive_callback_pointer = (u32)runtime_ios_callback;
    runtime_transport_receive_context_pointer = (u32)&runtime_transport_receive_context;
    runtime_memcpy(
        runtime_transport_receive_request_bytes,
        (volatile const void*)&runtime_transport_receive_request,
        RUNTIME_RECEIVE_REQUEST_LOGICAL_SIZE
    );
    runtime_memzero(&runtime_transport_receive_context, sizeof(runtime_transport_receive_context));
    runtime_transport_receive_context.expected_generation = runtime_transport_pending_generation + 1;
    runtime_sync_receive_context_evidence();

    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    runtime_transport_receive_context.expected_generation = runtime_transport_pending_generation;
    result = runtime_call_retail_ios_ioctlv_async(
        runtime_transport_ip_fd,
        IOCTLV_SO_RECVFROM,
        RUNTIME_RECEIVE_INPUT_VECTOR_COUNT,
        RUNTIME_RECEIVE_OUTPUT_VECTOR_COUNT,
        (runtime_ioctlv*)runtime_transport_receive_vectors,
        runtime_ios_callback,
        (void*)&runtime_transport_receive_context
    );
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_transport_receive_submit_result = result;
    runtime_transport_receive_submit_result_u32 = (u32)result;
    runtime_record_submit_evidence(RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET, result, runtime_transport_pending_generation);
    runtime_diag_record_submit_return(result);
    if (result != 0) {
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        return result > 0 ? 1 : -1;
    }
    runtime_set_phase(next_phase, RUNTIME_TRANSPORT_POLL_ACTION_RECV);
    return 0;
}

static void runtime_protocol_prepare_frame(u32 message_type, volatile u8* frame)
{
    runtime_memzero(frame, RUNTIME_TCP_FRAME_SIZE);
    runtime_write_be32(frame + 0, RUNTIME_PROTOCOL_MAGIC);
    frame[4] = RUNTIME_PROTOCOL_VERSION;
    frame[5] = (u8)message_type;
    runtime_write_be16(frame + 6, RUNTIME_TCP_FRAME_SIZE);
    runtime_write_be32(frame + 8, runtime_protocol_client_tx_sequence);
    runtime_write_be32(frame + 12, runtime_protocol_server_rx_sequence);
    runtime_write_be32(frame + 16, 36);
    runtime_write_be32(frame + 20, 0);
    if (message_type == RUNTIME_PROTOCOL_CLIENT_HELLO) {
        runtime_write_be32(frame + 24, 0x524D3345);
        runtime_write_be32(frame + 28, PRIME3_CP3W_RUNTIME_BUILD_ID);
        runtime_write_be32(frame + 32, RUNTIME_PROTOCOL_CAPABILITIES);
        runtime_write_be32(frame + 36, runtime_protocol_client_nonce);
        runtime_write_be32(frame + 40, 0);
        runtime_write_be32(frame + 44, 0);
        runtime_write_be32(frame + 48, RUNTIME_PROTOCOL_QUEUE_DEPTH);
        runtime_write_be32(frame + 52, RUNTIME_PROTOCOL_QUEUE_DEPTH);
    } else if (message_type == RUNTIME_PROTOCOL_CLIENT_TEST) {
        runtime_write_be32(frame + 24, 0x43545354);
        runtime_write_be32(frame + 28, runtime_protocol_client_nonce);
        runtime_write_be32(frame + 32, runtime_poll_counter);
    } else if (message_type == RUNTIME_PROTOCOL_TRACKER_SNAPSHOT) {
        u32 game_state = *(const volatile u32*)RUNTIME_PRIME3_NTSC_GAME_STATE_POINTER_ADDRESS;
        u32 inventory_root = 0;
        runtime_write_be32(frame + 24, 1);
        runtime_write_be32(frame + 28, 0);
        runtime_write_be32(frame + 32, 1);
        runtime_write_be32(frame + 36, 0);
        runtime_write_be32(frame + 40, RUNTIME_PROTOCOL_VERSION);
        runtime_write_be32(frame + 44, 12);
        if (game_state >= RUNTIME_MEM1_START && game_state < RUNTIME_MEM1_END - 0x28U) {
            inventory_root = *(const volatile u32*)(game_state + 0x24U);
        }
        if (inventory_root >= RUNTIME_MEM1_START && inventory_root < RUNTIME_MEM1_END - 0x80U) {
            u32 first_slot = inventory_root + 0x54U + ((u32)runtime_cp3w_inventory_item_ids[0] * 0x0CU);
            runtime_write_be32(frame + 48, *(const volatile u32*)first_slot);
            runtime_write_be32(frame + 52, *(const volatile u32*)(first_slot + 4));
            runtime_write_be32(frame + 56, *(const volatile u32*)(first_slot + 8));
        }
    } else if (message_type == RUNTIME_PROTOCOL_CP3D_DIAGNOSTIC_REQUEST) {
        runtime_write_be32(frame + 24, 0x43503344);
        runtime_write_be32(frame + 28, runtime_poll_counter);
        runtime_write_be32(frame + 32, runtime_protocol_frames_sent);
        runtime_write_be32(frame + 36, runtime_protocol_frames_received);
    }
    runtime_write_be32(frame + RUNTIME_TCP_FRAME_CRC_OFFSET, runtime_crc32(frame, RUNTIME_TCP_FRAME_CRC_OFFSET));
    runtime_protocol_frames_encoded += 1;
}

static s32 runtime_protocol_enqueue_outbound(u32 message_type, const volatile u8* frame)
{
    volatile runtime_protocol_queue_slot* slot = 0;
    if (runtime_protocol_outbound_count >= RUNTIME_PROTOCOL_QUEUE_DEPTH) {
        runtime_protocol_queue_overflow_count += 1;
        return -1;
    }
    slot = &runtime_protocol_outbound_queue[runtime_protocol_outbound_tail];
    if (slot->occupied != 0) {
        runtime_protocol_queue_overflow_count += 1;
        return -1;
    }
    slot->occupied = 1;
    slot->message_type = message_type;
    slot->sequence = runtime_read_be32(frame + 8);
    runtime_memcpy(slot->frame, frame, RUNTIME_TCP_FRAME_SIZE);
    runtime_protocol_outbound_tail = (runtime_protocol_outbound_tail + 1) % RUNTIME_PROTOCOL_QUEUE_DEPTH;
    runtime_protocol_outbound_count += 1;
    if (runtime_protocol_outbound_count > runtime_protocol_outbound_high_water) {
        runtime_protocol_outbound_high_water = runtime_protocol_outbound_count;
    }
    return 0;
}

static s32 runtime_protocol_enqueue_inbound(u32 message_type, u32 sequence)
{
    volatile runtime_protocol_queue_slot* slot = 0;
    if (runtime_protocol_inbound_count >= RUNTIME_PROTOCOL_QUEUE_DEPTH) {
        runtime_protocol_queue_overflow_count += 1;
        return -1;
    }
    slot = &runtime_protocol_inbound_queue[runtime_protocol_inbound_tail];
    if (slot->occupied != 0) {
        runtime_protocol_queue_overflow_count += 1;
        return -1;
    }
    slot->occupied = 1;
    slot->message_type = message_type;
    slot->sequence = sequence;
    runtime_memcpy(slot->frame, runtime_transport_receive_payload_buffer, RUNTIME_TCP_FRAME_SIZE);
    runtime_protocol_inbound_tail = (runtime_protocol_inbound_tail + 1) % RUNTIME_PROTOCOL_QUEUE_DEPTH;
    runtime_protocol_inbound_count += 1;
    if (runtime_protocol_inbound_count > runtime_protocol_inbound_high_water) {
        runtime_protocol_inbound_high_water = runtime_protocol_inbound_count;
    }
    return 0;
}

static void runtime_protocol_fail(u32 phase)
{
    runtime_protocol_handshake_failure_count += 1;
    runtime_tcp_echo_last_failure_phase = phase;
    runtime_tcp_send_outcome_close_pending = 1;
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
}

static s32 runtime_submit_tcp_echo_receive(u32 next_phase)
{
    s32 result = 0;
    u32 remaining = RUNTIME_TCP_FRAME_SIZE - runtime_tcp_echo_receive_offset;
    runtime_diag_increment(&runtime_ios_submit_attempt_count);
    runtime_diag_increment(&runtime_c_before_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL);
    if (
        runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
        || runtime_transport_ip_fd < 0
        || runtime_transport_socket_fd < 0
        || runtime_transport_socket_ready == 0
        || remaining == 0
    ) {
        runtime_tcp_echo_receive_submit_result = -1;
        return -1;
    }

    runtime_memzero(&runtime_transport_receive_request, sizeof(runtime_transport_receive_request));
    runtime_memzero(runtime_transport_receive_vectors, sizeof(runtime_transport_receive_vectors));
    runtime_transport_receive_request.socket = runtime_transport_socket_fd;
    runtime_transport_receive_request.flags = 0;
    runtime_transport_receive_vectors[0].data = (void*)&runtime_transport_receive_request;
    runtime_transport_receive_vectors[0].len = RUNTIME_RECEIVE_REQUEST_LOGICAL_SIZE;
    runtime_transport_receive_vectors[1].data = (void*)(runtime_transport_receive_payload_buffer + runtime_tcp_echo_receive_offset);
    runtime_transport_receive_vectors[1].len = remaining;
    runtime_memzero(&runtime_tcp_echo_receive_context, sizeof(runtime_tcp_echo_receive_context));
    runtime_tcp_echo_receive_context.expected_generation = runtime_transport_pending_generation + 1;
    runtime_cache_flush(&runtime_transport_receive_request, RUNTIME_RECEIVE_REQUEST_LOGICAL_SIZE);
    runtime_cache_flush(runtime_transport_receive_vectors, sizeof(runtime_transport_receive_vectors));

    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_TCP_ECHO_RECEIVE;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    runtime_tcp_echo_receive_context.expected_generation = runtime_transport_pending_generation;
    result = runtime_call_retail_ios_ioctlv_async(
        runtime_transport_ip_fd,
        IOCTLV_SO_RECVFROM,
        1,
        1,
        (runtime_ioctlv*)runtime_transport_receive_vectors,
        runtime_ios_callback,
        (void*)&runtime_tcp_echo_receive_context
    );
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_tcp_echo_receive_submit_result = result;
    runtime_record_submit_evidence(RUNTIME_TRANSPORT_OP_TCP_ECHO_RECEIVE, result, runtime_transport_pending_generation);
    runtime_diag_record_submit_return(result);
    if (result != 0) {
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        return -1;
    }
    runtime_set_phase(next_phase, RUNTIME_TRANSPORT_POLL_ACTION_RECV);
    return 0;
}

static s32 runtime_submit_ioctlv_send(u32 next_phase)
{
    s32 result = 0;
    runtime_diag_increment(&runtime_ios_submit_attempt_count);
    runtime_diag_increment(&runtime_c_before_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_BEFORE_VENEER_CALL);
    if (
        runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_TCP_HELLO
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_TEST
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_ALT1
    ) {
        goto tcp_send_guard_passed;
    }
    if (
        !runtime_transport_uses_send_mode()
        || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
        || runtime_transport_ip_fd < 0
        || runtime_transport_socket_fd < 0
        || runtime_transport_socket_ready == 0
        || runtime_transport_host_id_ready == 0
        || runtime_transport_bound_flag == 0
        || (runtime_transport_is_native_wc24_bootstrap_mode()
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                ? (runtime_transport_send_submit_count == 0
                    || runtime_transport_send_submit_count > RUNTIME_NATIVE_BEACON_ATTEMPT_LIMIT)
#else
                ? runtime_transport_send_submit_count == 0
#endif
                : runtime_transport_is_cp3w_frame_validation_mode()
                ? (runtime_transport_cp3w_frames_valid == 0 || runtime_transport_send_submit_count == 0)
                : runtime_transport_is_cp3w_ping_pong_mode()
                ? (runtime_transport_cp3w_requests_dispatched == 0 || runtime_transport_send_submit_count == 0)
                : runtime_transport_is_cp3w_hello_session_mode()
                ? (runtime_transport_cp3w_requests_dispatched == 0 || runtime_transport_send_submit_count == 0)
                : runtime_transport_is_cp3w_game_identity_mode()
                ? (runtime_transport_cp3w_requests_dispatched == 0 || runtime_transport_send_submit_count == 0)
                : runtime_transport_is_cp3w_inventory_mode()
                ? (runtime_transport_cp3w_requests_dispatched == 0 || runtime_transport_send_submit_count == 0)
                : (runtime_transport_receive_count == 0 || runtime_transport_send_submit_count == 0
                    || runtime_transport_send_submit_count != runtime_transport_receive_count))
    ) {
        runtime_transport_last_ios_result = -1;
        runtime_transport_last_submit_result = -1;
        runtime_transport_send_submit_result = -1;
        runtime_record_submit_evidence(RUNTIME_TRANSPORT_OP_SEND_SOCKET, -1, runtime_transport_pending_generation);
        runtime_diag_record_submit_return(-1);
        return -1;
    }
tcp_send_guard_passed:
    if (runtime_transport_prepared_send_length == 0 || runtime_transport_prepared_send_length > RUNTIME_UDP_SEND_CAPACITY) {
        runtime_transport_last_ios_result = -1;
        runtime_transport_last_submit_result = -1;
        runtime_transport_send_submit_result = -1;
        runtime_record_submit_evidence(RUNTIME_TRANSPORT_OP_SEND_SOCKET, -1, runtime_transport_pending_generation);
        runtime_diag_record_submit_return(-1);
        return -1;
    }

    runtime_memzero(&runtime_transport_send_request, sizeof(runtime_transport_send_request));
    runtime_memzero(runtime_transport_send_vectors, sizeof(runtime_transport_send_vectors));
    runtime_transport_send_request.socket = (u32)runtime_transport_socket_fd;
    runtime_transport_send_request.flags = 0;
    runtime_transport_send_request.has_destaddr = 0;
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_ALT1) {
        runtime_transport_send_vectors[0].data = (void*)&runtime_transport_send_request;
        runtime_transport_send_vectors[0].len = RUNTIME_SEND_REQUEST_LOGICAL_SIZE;
        runtime_transport_send_vectors[1].data = (void*)runtime_transport_send_payload_bytes;
        runtime_transport_send_vectors[1].len = 4;
    } else {
        runtime_transport_send_vectors[0].data = (void*)(runtime_transport_send_payload_bytes + runtime_tcp_send_offset);
        runtime_transport_send_vectors[0].len = runtime_transport_prepared_send_length - runtime_tcp_send_offset;
        runtime_transport_send_vectors[1].data = (void*)&runtime_transport_send_request;
        runtime_transport_send_vectors[1].len = RUNTIME_SEND_REQUEST_LOGICAL_SIZE;
    }

    runtime_transport_send_target_address = PRIME3_RETAIL_IOS_IOCTLV_ASYNC_ADDRESS;
    runtime_transport_send_command = IOCTLV_SO_SENDTO;
    runtime_transport_send_submitted_fd = runtime_transport_ip_fd;
    runtime_transport_send_submitted_socket = runtime_transport_socket_fd;
    runtime_transport_send_input_vector_count = RUNTIME_SEND_INPUT_VECTOR_COUNT;
    runtime_transport_send_output_vector_count = RUNTIME_SEND_OUTPUT_VECTOR_COUNT;
    runtime_transport_send_request_address = (u32)&runtime_transport_send_request;
    runtime_transport_send_request_storage_size = sizeof(runtime_transport_send_request);
    runtime_transport_send_request_logical_size = RUNTIME_SEND_REQUEST_LOGICAL_SIZE;
    runtime_transport_send_request_alignment = 0x20;
    runtime_transport_send_request_flags = 0;
    runtime_transport_send_has_destaddr = 0;
    runtime_transport_send_vector_address = (u32)runtime_transport_send_vectors;
    runtime_transport_send_vector_storage_size = sizeof(runtime_transport_send_vectors);
    runtime_transport_send_vector_logical_size = RUNTIME_SEND_VECTOR_COUNT * sizeof(runtime_ioctlv);
    runtime_transport_send_vector_alignment = 0x20;
    runtime_transport_send_vector_0_pointer = (u32)runtime_transport_send_vectors[0].data;
    runtime_transport_send_vector_0_length = runtime_transport_send_vectors[0].len;
    runtime_transport_send_vector_1_pointer = (u32)runtime_transport_send_vectors[1].data;
    runtime_transport_send_vector_1_length = runtime_transport_send_vectors[1].len;
    runtime_transport_send_payload_address = (u32)runtime_transport_send_payload_bytes;
    runtime_transport_send_payload_capacity = RUNTIME_UDP_SEND_CAPACITY;
    runtime_transport_send_payload_alignment = 0x20;
    runtime_transport_send_destination_address = 0;
    runtime_transport_send_destination_logical_size = 0;
    runtime_transport_send_destination_storage_size = 0;
    runtime_transport_send_destination_alignment = 0;
    runtime_transport_send_callback_pointer = (u32)runtime_ios_callback;
    runtime_transport_send_context_pointer = (u32)&runtime_transport_send_context;
    runtime_memcpy(
        runtime_transport_send_request_bytes,
        (volatile const void*)&runtime_transport_send_request,
        RUNTIME_SEND_REQUEST_LOGICAL_SIZE
    );
    runtime_memzero(&runtime_transport_send_context, sizeof(runtime_transport_send_context));
    runtime_transport_send_context.expected_generation = runtime_transport_pending_generation + 1;
    runtime_sync_send_context_evidence();

    runtime_transport_pending_operation = (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_TEST
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_ALT1)
        ? RUNTIME_TRANSPORT_OP_TCP_SEND
        : RUNTIME_TRANSPORT_OP_SEND_SOCKET;
    runtime_transport_pending_generation += 1;
    runtime_transport_callback_pending = 0;
    runtime_transport_last_ios_result = 0;
    runtime_transport_send_validated_result = 0;
    runtime_transport_send_context.expected_generation = runtime_transport_pending_generation;
    runtime_send13_diagnostic_block.magic = 0x53313344;
    runtime_send13_diagnostic_block.phase_before = runtime_transport_phase;
    runtime_send13_diagnostic_block.pending_operation = runtime_transport_pending_operation;
    runtime_send13_diagnostic_block.callback_generation = runtime_transport_pending_generation;
    runtime_send13_diagnostic_block.userdata_valid = 1;
    runtime_send13_diagnostic_block.ip_fd = runtime_transport_ip_fd;
    runtime_send13_diagnostic_block.socket_fd = runtime_transport_socket_fd;
    runtime_send13_diagnostic_block.vector0_address = (u32)runtime_transport_send_vectors[0].data;
    runtime_send13_diagnostic_block.vector0_length = runtime_transport_send_vectors[0].len;
    runtime_send13_diagnostic_block.vector1_address = (u32)runtime_transport_send_vectors[1].data;
    runtime_send13_diagnostic_block.vector1_length = runtime_transport_send_vectors[1].len;
    runtime_send13_diagnostic_block.request_address = (u32)&runtime_transport_send_request;
    runtime_memcpy(runtime_send13_diagnostic_block.request_bytes, (volatile const void*)&runtime_transport_send_request, 40);
    runtime_memcpy(runtime_send13_diagnostic_block.payload_bytes, runtime_transport_send_payload_bytes, 16);
    runtime_cache_flush(runtime_transport_send_payload_bytes + runtime_tcp_send_offset, runtime_transport_send_vectors[0].len);
    runtime_cache_flush(&runtime_transport_send_request, RUNTIME_SEND_REQUEST_LOGICAL_SIZE);
    runtime_cache_flush(runtime_transport_send_vectors, sizeof(runtime_transport_send_vectors));
    result = runtime_call_retail_ios_ioctlv_async(
        runtime_transport_ip_fd,
        IOCTLV_SO_SENDTO,
        RUNTIME_SEND_INPUT_VECTOR_COUNT,
        RUNTIME_SEND_OUTPUT_VECTOR_COUNT,
        (runtime_ioctlv*)runtime_transport_send_vectors,
        runtime_ios_callback,
        (void*)&runtime_transport_send_context
    );
    runtime_diag_increment(&runtime_c_after_veneer_call_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_C_AFTER_VENEER_CALL);
    runtime_transport_last_submit_result = result;
    runtime_transport_send_submit_result = result;
    runtime_record_submit_evidence(runtime_transport_pending_operation, result, runtime_transport_pending_generation);
    runtime_diag_record_submit_return(result);
    if (result != 0) {
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        return result > 0 ? 1 : -1;
    }
    runtime_set_phase(next_phase, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
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
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CONNECT_TCP
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_VERIFY_BOUND_ENDPOINT
    ) {
        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP) {
            runtime_cache_invalidate(runtime_transport_nwc24_output_buffer, sizeof(runtime_transport_nwc24_output_buffer));
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET) {
            runtime_cache_invalidate(&runtime_transport_socket_request, sizeof(runtime_transport_socket_request));
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_VERIFY_BOUND_ENDPOINT) {
            runtime_cache_invalidate(
                runtime_transport_getsockname_address,
                sizeof(runtime_transport_getsockname_address)
            );
        } else {
            runtime_cache_invalidate(&runtime_transport_bind_params, sizeof(runtime_transport_bind_params));
        }
    }
    runtime_record_operation_callback();
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
    return 0;
}

static s32 runtime_consume_receive_completion(void)
{
    u32 accepted_length = 0;
    u16 source_port = 0;
    if (runtime_transport_callback_pending == 0) {
        runtime_transport_polls_while_receive_pending = runtime_poll_counter;
        runtime_set_phase(runtime_transport_phase, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        return 1;
    }
    runtime_transport_callback_pending = 0;
    if (runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET) {
        runtime_transport_rejected_callback_count += 1;
        runtime_record_receive_error(RUNTIME_TRANSPORT_PHASE_RECEIVE_STALE_CALLBACK, runtime_transport_last_ios_result);
        return -1;
    }
    if (runtime_transport_callback_generation != runtime_transport_pending_generation) {
        runtime_transport_rejected_callback_count += 1;
        runtime_record_receive_error(RUNTIME_TRANSPORT_PHASE_RECEIVE_STALE_CALLBACK, runtime_transport_last_ios_result);
        return -1;
    }
    runtime_record_operation_callback();
    runtime_sync_receive_context_evidence();
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
    if (runtime_transport_receive_stale_callback_count != 0) {
        runtime_record_receive_error(RUNTIME_TRANSPORT_PHASE_RECEIVE_STALE_CALLBACK, runtime_transport_last_ios_result);
        return -1;
    }
    if (runtime_transport_receive_duplicate_callback_count != 0) {
        runtime_record_receive_error(
            RUNTIME_TRANSPORT_PHASE_RECEIVE_DUPLICATE_CALLBACK,
            runtime_transport_last_ios_result
        );
        return -1;
    }
    if (runtime_transport_last_ios_result < 0) {
        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST) {
            runtime_tcp_send_outcome_close_pending = 1;
            runtime_transport_retry_deadline = runtime_poll_counter + 240;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_WAIT_TCP_SEND_OUTCOME_CLOSE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
            return 0;
        }
        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST) {
            runtime_tcp_send_outcome_close_pending = 1;
            runtime_transport_retry_deadline = runtime_poll_counter + 120;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_WAIT_TCP_SEND_OUTCOME_CLOSE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
            return 0;
        }
        runtime_record_receive_error(RUNTIME_TRANSPORT_PHASE_RECEIVE_ASYNC_FAILED, runtime_transport_last_ios_result);
        return -1;
    }
    if ((u32)runtime_transport_last_ios_result > RUNTIME_UDP_RECEIVE_CAPACITY) {
        runtime_transport_receive_bytes = 0;
        runtime_transport_last_receive_length = 0;
        runtime_record_receive_error(
            RUNTIME_TRANSPORT_PHASE_RECEIVE_OVERSIZED_RESULT,
            runtime_transport_last_ios_result
        );
        return -1;
    }

    runtime_cache_invalidate(runtime_transport_receive_payload_buffer, RUNTIME_UDP_RECEIVE_CAPACITY);
    runtime_cache_invalidate(runtime_transport_receive_source_bytes, sizeof(runtime_transport_receive_source_bytes));
    accepted_length = (u32)runtime_transport_last_ios_result;
    if (runtime_transport_receive_count == 0xFFFFFFFFU) {
        runtime_record_receive_error(
            RUNTIME_TRANSPORT_PHASE_EXCHANGE_COUNTER_OVERFLOW,
            runtime_transport_last_ios_result
        );
        return -1;
    }
    if (runtime_transport_receive_count != 0) {
        runtime_transport_previous_peer_ipv4 = runtime_transport_last_peer_ipv4;
        runtime_transport_previous_peer_port = runtime_transport_last_peer_port;
    }
    runtime_transport_receive_count += 1;
    runtime_transport_last_packet_receive_poll = runtime_poll_counter;
    runtime_transport_current_exchange_index = runtime_transport_receive_count;
    runtime_transport_receive_bytes += accepted_length;
    runtime_transport_last_receive_length = accepted_length;
    runtime_memcpy(
        runtime_transport_last_receive_preview,
        runtime_transport_receive_payload_buffer,
        accepted_length < RUNTIME_PREVIEW_SIZE ? accepted_length : RUNTIME_PREVIEW_SIZE
    );
    if (accepted_length < RUNTIME_PREVIEW_SIZE) {
        runtime_copy_preview(
            runtime_transport_last_receive_preview,
            runtime_transport_receive_payload_buffer,
            accepted_length
        );
    }
    runtime_memcpy(
        runtime_transport_receive_source_bytes,
        (volatile const void*)runtime_transport_receive_source_bytes,
        RUNTIME_WII_SOCKADDR_IN_SIZE
    );
    runtime_transport_last_peer_length = runtime_transport_receive_source_bytes[0];
    runtime_transport_last_peer_family = runtime_transport_receive_source_bytes[1];
    if (
        runtime_transport_receive_source_bytes[0] == RUNTIME_WII_SOCKADDR_IN_SIZE
        && runtime_transport_receive_source_bytes[1] == AF_INET
    ) {
        source_port = (u16)(
            ((u16)runtime_transport_receive_source_bytes[2] << 8) | runtime_transport_receive_source_bytes[3]
        );
        runtime_transport_last_peer_port = source_port;
        runtime_transport_last_peer_ipv4 = ((u32)runtime_transport_receive_source_bytes[4] << 24)
            | ((u32)runtime_transport_receive_source_bytes[5] << 16)
            | ((u32)runtime_transport_receive_source_bytes[6] << 8)
            | (u32)runtime_transport_receive_source_bytes[7];
    } else {
        runtime_transport_last_peer_port = 0;
        runtime_transport_last_peer_ipv4 = 0;
    }
    runtime_transport_polls_after_receive = runtime_poll_counter;
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE_TCP_ACK) {
        if (
            accepted_length >= 16
            && runtime_read_be32(runtime_transport_receive_payload_buffer) == 0x43503354
            && runtime_transport_receive_payload_buffer[4] == 1
            && runtime_transport_receive_payload_buffer[5] == 2
        ) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_TCP_ESTABLISHED, RUNTIME_TRANSPORT_POLL_ACTION_RECV);
            return 0;
        }
        runtime_record_receive_error(RUNTIME_TRANSPORT_PHASE_RECEIVE_INVALID_POSITIVE, runtime_transport_last_ios_result);
        return -1;
    }
    runtime_set_phase(
        runtime_transport_is_cp3w_mode()
            ? RUNTIME_TRANSPORT_PHASE_CP3W_VALIDATE_FRAME
            : runtime_transport_uses_send_mode()
            ? RUNTIME_TRANSPORT_PHASE_SUBMIT_SEND_ONCE
            : RUNTIME_TRANSPORT_PHASE_RECEIVED_DATAGRAM,
        RUNTIME_TRANSPORT_POLL_ACTION_RECV
    );
    return 0;
}

static s32 runtime_consume_tcp_echo_receive(void)
{
    u32 remaining = 0;
    u32 received = 0;
    if (runtime_transport_callback_pending == 0) {
        runtime_set_phase(runtime_transport_phase, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        return 1;
    }
    runtime_transport_callback_pending = 0;
    if (
        runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_TCP_ECHO_RECEIVE
        || runtime_transport_callback_generation != runtime_transport_pending_generation
        || runtime_tcp_echo_receive_context.completion_flag == 0
        || runtime_tcp_echo_receive_context.completion_generation != runtime_transport_pending_generation
    ) {
        runtime_transport_rejected_callback_count += 1;
        runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
        runtime_tcp_echo_receive_error_count += 1;
        runtime_tcp_echo_last_failure_phase = RUNTIME_TRANSPORT_PHASE_WAIT_ECHO_RECV;
        runtime_tcp_send_outcome_close_pending = 1;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        return 0;
    }
    runtime_record_operation_callback();
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
    runtime_tcp_echo_receive_callback_result = runtime_transport_last_ios_result;
    if (runtime_transport_last_ios_result < 0) {
        runtime_tcp_echo_receive_error_count += 1;
        runtime_tcp_echo_last_failure_phase = RUNTIME_TRANSPORT_PHASE_WAIT_ECHO_RECV;
        runtime_tcp_send_outcome_close_pending = 1;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        return 0;
    }
    if (runtime_transport_last_ios_result == 0) {
        runtime_tcp_echo_peer_close_count += 1;
        runtime_tcp_echo_last_failure_phase = RUNTIME_TRANSPORT_PHASE_DISCONNECTED;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DISCONNECTED, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        return 0;
    }
    remaining = RUNTIME_TCP_FRAME_SIZE - runtime_tcp_echo_receive_offset;
    received = (u32)runtime_transport_last_ios_result;
    if (received > remaining) {
        runtime_tcp_echo_receive_error_count += 1;
        runtime_tcp_echo_last_failure_phase = RUNTIME_TRANSPORT_PHASE_WAIT_ECHO_RECV;
        runtime_tcp_send_outcome_close_pending = 1;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        return 0;
    }
    runtime_cache_invalidate(runtime_transport_receive_payload_buffer + runtime_tcp_echo_receive_offset, received);
    runtime_tcp_echo_receive_offset += received;
    runtime_tcp_echo_receive_bytes += received;
    if (received < remaining) {
        runtime_tcp_echo_partial_receive_count += 1;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SUBMIT_ECHO_RECV, RUNTIME_TRANSPORT_POLL_ACTION_RECV);
        return 0;
    }
    runtime_set_phase(RUNTIME_TRANSPORT_PHASE_VALIDATE_FRAME, RUNTIME_TRANSPORT_POLL_ACTION_RECV);
    return 0;
}

static s32 runtime_consume_send_completion(void)
{
    u32 heartbeat = runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_HEARTBEAT;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    u32 native_beacon = runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON;
#endif
    if (runtime_transport_callback_pending == 0) {
        runtime_transport_polls_while_send_pending = runtime_poll_counter;
        runtime_set_phase(runtime_transport_phase, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        return 1;
    }
    runtime_transport_callback_pending = 0;
    if (
        runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_SEND_SOCKET
        && runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_TCP_SEND
    ) {
        runtime_transport_rejected_callback_count += 1;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        if (native_beacon != 0) {
            runtime_native_record_beacon_completion_failure(
                RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON,
                runtime_transport_last_ios_result
            );
            return -1;
        }
#endif
        runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_STALE_CALLBACK, runtime_transport_last_ios_result);
        return -1;
    }
    if (runtime_transport_callback_generation != runtime_transport_pending_generation) {
        runtime_transport_rejected_callback_count += 1;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        if (native_beacon != 0) {
            runtime_native_record_beacon_completion_failure(
                RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON,
                runtime_transport_last_ios_result
            );
            return -1;
        }
#endif
        runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_STALE_CALLBACK, runtime_transport_last_ios_result);
        return -1;
    }
    runtime_record_operation_callback();
    runtime_sync_send_context_evidence();
    runtime_send13_diagnostic_block.callback_invoked = 1;
    runtime_send13_diagnostic_block.callback_result = runtime_transport_last_ios_result;
    runtime_send13_diagnostic_block.callback_generation = runtime_transport_callback_generation;
    runtime_send13_diagnostic_block.userdata_valid =
        runtime_transport_send_context.expected_generation == runtime_transport_callback_generation;
    runtime_transport_pending_operation = RUNTIME_TRANSPORT_OP_NONE;
    if (runtime_transport_send_stale_callback_count != 0) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        if (native_beacon != 0) {
            runtime_native_record_beacon_completion_failure(
                RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON,
                runtime_transport_last_ios_result
            );
            return -1;
        }
#endif
        runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_STALE_CALLBACK, runtime_transport_last_ios_result);
        return -1;
    }
    if (runtime_transport_send_duplicate_callback_count != 0) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        if (native_beacon != 0) {
            runtime_native_record_beacon_completion_failure(
                RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON,
                runtime_transport_last_ios_result
            );
            return -1;
        }
#endif
        runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_DUPLICATE_CALLBACK, runtime_transport_last_ios_result);
        return -1;
    }
    if (runtime_transport_last_ios_result < 0) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        if (native_beacon != 0) {
            runtime_native_record_beacon_completion_failure(
                RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON,
                runtime_transport_last_ios_result
            );
            return -1;
        }
#endif
        runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_ASYNC_FAILED, runtime_transport_last_ios_result);
        return -1;
    }
    if (runtime_transport_last_ios_result == 0) {
        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
            return 0;
        }
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        if (native_beacon != 0) {
            runtime_native_record_beacon_completion_failure(
                RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON,
                runtime_transport_last_ios_result
            );
            return -1;
        }
#endif
        runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_INVALID_POSITIVE, runtime_transport_last_ios_result);
        return -1;
    }
    if (
        runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_HELLO
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST
    ) {
        u32 remaining = runtime_transport_prepared_send_length - runtime_tcp_send_offset;
        if ((u32)runtime_transport_last_ios_result > remaining) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_INVALID_POSITIVE, runtime_transport_last_ios_result);
            return -1;
        }
        runtime_tcp_send_offset += (u32)runtime_transport_last_ios_result;
        runtime_tcp_send_completed_bytes = runtime_tcp_send_offset;
        if (runtime_tcp_send_offset < runtime_transport_prepared_send_length) {
            runtime_set_phase(
                runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST
                    ? RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_TEST
                    : RUNTIME_TRANSPORT_PHASE_SEND_TCP_HELLO,
                RUNTIME_TRANSPORT_POLL_ACTION_SEND
            );
            return 0;
        }
    } else if ((u32)runtime_transport_last_ios_result != runtime_transport_prepared_send_length) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        if (native_beacon != 0) {
            runtime_native_record_beacon_completion_failure(
                RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON,
                runtime_transport_last_ios_result
            );
            return -1;
        }
#endif
        runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_INVALID_POSITIVE, runtime_transport_last_ios_result);
        return -1;
    }

    if (runtime_transport_send_count == 0xFFFFFFFFU || runtime_transport_completed_exchange_count == 0xFFFFFFFFU) {
        runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_EXCHANGE_COUNTER_OVERFLOW, runtime_transport_last_ios_result);
        return -1;
    }
    runtime_transport_send_validated_result = (u32)runtime_transport_last_ios_result;
    runtime_transport_send_count += 1;
    runtime_transport_send_bytes += runtime_transport_prepared_send_length;
    runtime_transport_last_send_length = runtime_transport_prepared_send_length;
    runtime_copy_preview(
        runtime_transport_last_send_preview,
        runtime_transport_send_payload_bytes,
        runtime_transport_prepared_send_length
    );
    runtime_transport_completed_exchange_count += 1;
    runtime_transport_last_completed_exchange_index = runtime_transport_completed_exchange_count;
    runtime_transport_polls_after_send = runtime_poll_counter;
    runtime_transport_last_packet_send_poll = runtime_poll_counter;
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST) {
        runtime_tcp_send_outcome_close_pending = 1;
        runtime_transport_retry_deadline = runtime_poll_counter + 360;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_WAIT_TCP_SEND_OUTCOME_CLOSE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        return 0;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_ALT1) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        return 0;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_HELLO) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_RECEIVE_TCP_ACK, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        return 0;
    }
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    if (native_beacon != 0) {
        runtime_native_beacon_success_count += 1;
        runtime_native_last_beacon_completion_result = runtime_transport_last_ios_result;
        runtime_transport_last_heartbeat_result = runtime_transport_last_ios_result;
        runtime_native_set_stage(RUNTIME_NATIVE_STAGE_BEACON_COMPLETE);
        if (runtime_native_first_successful_beacon_poll == 0) {
            runtime_native_first_successful_beacon_poll = runtime_poll_counter;
        }
        runtime_native_last_successful_beacon_poll = runtime_poll_counter;
        if (runtime_native_beacon_attempt_count >= RUNTIME_NATIVE_BEACON_ATTEMPT_LIMIT) {
            runtime_transport_cleanup_deferred_count += 1;
            runtime_transport_cleanup_count = runtime_transport_cleanup_deferred_count;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_NATIVE_BEACON_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        } else {
            runtime_native_next_beacon_poll =
                runtime_poll_counter + RUNTIME_NATIVE_BEACON_RETRY_POLL_INTERVAL;
            runtime_native_next_beacon_timebase =
                runtime_native_read_timebase() + RUNTIME_NATIVE_INTERVAL_TIMEBASE_TICKS;
            runtime_set_phase(
                RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON_INTERVAL,
                RUNTIME_TRANSPORT_POLL_ACTION_WAIT
            );
        }
        return 0;
    }
#endif
    if (heartbeat != 0) {
        runtime_transport_last_heartbeat_result = runtime_transport_last_ios_result;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE != 23
        if (runtime_transport_is_native_wc24_bootstrap_mode()) {
            /* Keep the native SDK references and beacon socket alive for inspection. */
            runtime_transport_cleanup_deferred_count += 1;
            runtime_transport_cleanup_count = runtime_transport_cleanup_deferred_count;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
            return 0;
        }
#endif
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        return 0;
    }
    if (runtime_transport_is_cp3w_frame_validation_mode()) {
        runtime_transport_cp3w_framed_responses_completed += 1;
        if (!runtime_transport_validate_loop_limit()) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID, runtime_transport_last_ios_result);
            return -1;
        }
        if (runtime_transport_cp3w_datagrams_processed >= runtime_transport_configured_exchange_limit) {
            runtime_transport_note_cp3w_loop_complete();
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        }
        return 0;
    }
    if (runtime_transport_is_cp3w_ping_pong_mode()) {
        if (runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK) {
            runtime_transport_cp3w_pong_responses_completed += 1;
        } else if (runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_ERROR) {
            runtime_transport_cp3w_unsupported_responses_completed += 1;
        }
        if (!runtime_transport_validate_loop_limit()) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID, runtime_transport_last_ios_result);
            return -1;
        }
        if (runtime_transport_cp3w_datagrams_processed >= runtime_transport_configured_exchange_limit) {
            runtime_transport_note_cp3w_ping_pong_loop_complete();
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        }
        return 0;
    }
    if (runtime_transport_is_cp3w_hello_session_mode()) {
        if (runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_HELLO) {
            runtime_transport_cp3w_hello_responses_completed += 1;
        } else if (runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK) {
            runtime_transport_cp3w_pong_responses_completed += 1;
        } else if (runtime_transport_cp3w_last_dispatch_result == RUNTIME_CP3W_ERROR_CODE_NOT_NEGOTIATED) {
            runtime_transport_cp3w_not_negotiated_responses_completed += 1;
        } else if (runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_ERROR) {
            runtime_transport_cp3w_unsupported_responses_completed += 1;
        }
        if (!runtime_transport_validate_loop_limit()) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID, runtime_transport_last_ios_result);
            return -1;
        }
        if (runtime_transport_cp3w_datagrams_processed >= runtime_transport_configured_exchange_limit) {
            runtime_transport_note_cp3w_hello_session_loop_complete();
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        }
        return 0;
    }
    if (runtime_transport_is_cp3w_inventory_mode()) {
        if (runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_HELLO) {
            runtime_transport_cp3w_hello_responses_completed += 1;
        } else if (
            runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY
            && runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK
        ) {
            runtime_transport_cp3w_game_identity_responses_completed += 1;
        } else if (
            runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_GET_INVENTORY
            && runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK
        ) {
            runtime_transport_cp3w_inventory_responses_completed += 1;
            runtime_set_phase(
                RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_RESPONSE_COMPLETE,
                RUNTIME_TRANSPORT_POLL_ACTION_SEND
            );
        } else if (runtime_transport_cp3w_last_dispatch_result == RUNTIME_CP3W_ERROR_CODE_NOT_NEGOTIATED) {
            runtime_transport_cp3w_not_negotiated_responses_completed += 1;
        } else if (
            runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_PING
            && runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK
        ) {
            runtime_transport_cp3w_pong_responses_completed += 1;
        } else if (runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_ERROR) {
            runtime_transport_cp3w_unsupported_responses_completed += 1;
        }
        if (!runtime_transport_validate_loop_limit()) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID, runtime_transport_last_ios_result);
            return -1;
        }
        if (runtime_transport_exchange_limit_reached()) {
            runtime_transport_note_cp3w_inventory_loop_complete();
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        }
        return 0;
    }
    if (runtime_transport_is_cp3w_game_identity_mode()) {
        if (runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_HELLO) {
            runtime_transport_cp3w_hello_responses_completed += 1;
        } else if (
            runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY
            && runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK
        ) {
            runtime_transport_cp3w_game_identity_responses_completed += 1;
            runtime_set_phase(
                RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_RESPONSE_COMPLETE,
                RUNTIME_TRANSPORT_POLL_ACTION_SEND
            );
        } else if (runtime_transport_cp3w_last_dispatch_result == RUNTIME_CP3W_ERROR_CODE_NOT_NEGOTIATED) {
            runtime_transport_cp3w_not_negotiated_responses_completed += 1;
        } else if (
            runtime_transport_cp3w_last_dispatch_result == RUNTIME_CP3W_ERROR_CODE_CAPABILITY_NOT_NEGOTIATED
        ) {
            runtime_transport_cp3w_game_identity_capability_errors_completed += 1;
        } else if (
            runtime_transport_cp3w_last_dispatch_result == RUNTIME_CP3W_ERROR_CODE_INVALID_PAYLOAD_LENGTH
        ) {
            runtime_transport_cp3w_game_identity_invalid_payload_errors_completed += 1;
        } else if (
            runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_PING
            && runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK
        ) {
            runtime_transport_cp3w_pong_responses_completed += 1;
        } else if (runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_ERROR) {
            runtime_transport_cp3w_unsupported_responses_completed += 1;
        }
        if (!runtime_transport_validate_loop_limit()) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID, runtime_transport_last_ios_result);
            return -1;
        }
        if (runtime_transport_cp3w_datagrams_processed >= runtime_transport_configured_exchange_limit) {
            runtime_transport_note_cp3w_game_identity_loop_complete();
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        }
        return 0;
    }
    if (runtime_transport_is_recv_send_loop_mode()) {
        if (!runtime_transport_validate_loop_limit()) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID, runtime_transport_last_ios_result);
            return -1;
        }
        if (runtime_transport_completed_exchange_count >= runtime_transport_configured_exchange_limit) {
            runtime_transport_note_loop_complete();
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        }
    } else {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SENT_DATAGRAM, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
    }
    return 0;
}

static void runtime_record_init_error(s32 result)
{
    runtime_transport_last_error = result;
    runtime_transport_last_ios_result = result;
    runtime_transport_last_error_phase = runtime_transport_phase;
    if (runtime_transport_uses_receive_mode()) {
        runtime_schedule_retry(runtime_transport_phase, result, 0);
    } else {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FAILED, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
    }
}

static void runtime_record_receive_error(u32 phase, s32 result)
{
    runtime_transport_last_socket_error = result;
    runtime_transport_last_error = result;
    runtime_transport_last_ios_result = result;
    runtime_transport_last_error_phase = phase;
    if (runtime_transport_uses_receive_mode() && result < 0) {
        runtime_transport_transient_receive_error_count += 1;
        runtime_schedule_retry(phase, result, 1);
    } else {
        runtime_transport_fatal_receive_error_count += 1;
        runtime_set_phase(phase, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
    }
}

static void runtime_record_send_error(u32 phase, s32 result)
{
    runtime_transport_last_socket_error = result;
    runtime_transport_last_error = result;
    runtime_transport_last_ios_result = result;
    runtime_transport_last_error_phase = phase;
    runtime_transport_send_failure_count += 1;
    if (runtime_transport_uses_receive_mode() && result < 0) {
        runtime_schedule_retry(phase, result, 1);
    } else {
        runtime_set_phase(phase, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
    }
}

static void runtime_record_socket_error(s32 result)
{
    runtime_transport_last_socket_error = result;
    runtime_transport_last_error = result;
    runtime_transport_last_ios_result = result;
    runtime_transport_last_error_phase = runtime_transport_phase;
    if (runtime_transport_uses_receive_mode()) {
        runtime_schedule_retry(runtime_transport_phase, result, runtime_transport_socket_fd >= 0);
    } else {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FAILED, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
    }
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
        runtime_transport_get_host_id_service_started_after_completion = runtime_transport_service_started;
        runtime_transport_ip_fd_after_get_host_id = runtime_transport_ip_fd;
        runtime_transport_get_host_id_pending_after_completion = runtime_transport_pending_operation;
        runtime_transport_get_host_id_phase_after_completion = runtime_transport_phase;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CREATE_SOCKET) {
        runtime_transport_socket_callback_count += 1;
        runtime_transport_socket_fd_after_completion = runtime_transport_socket_fd;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_BIND_SOCKET) {
        runtime_transport_bind_callback_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE) {
        runtime_transport_cleanup_close_callback_count += 1;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET) {
        runtime_transport_receive_callback_result = runtime_transport_last_ios_result;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_TCP_ECHO_RECEIVE) {
        runtime_tcp_echo_receive_callback_result = runtime_transport_last_ios_result;
    } else if (runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_SEND_SOCKET) {
        runtime_transport_send_callback_result = runtime_transport_last_ios_result;
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
    } else if (operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE) {
        runtime_transport_cleanup_close_submit_result = result;
        runtime_transport_cleanup_close_submit_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET) {
        runtime_transport_receive_submit_result = result;
        runtime_transport_receive_submit_result_u32 = (u32)result;
        runtime_transport_receive_submit_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_SEND_SOCKET) {
    runtime_transport_send_submit_result = result;
    runtime_memcpy(runtime_tcp_send_r3_r9, runtime_abi_probe_pre_call_args, sizeof(runtime_tcp_send_r3_r9));
    runtime_memcpy(runtime_send13_diagnostic_block.args, runtime_abi_probe_pre_call_args, sizeof(runtime_send13_diagnostic_block.args));
    runtime_send13_diagnostic_block.submit_result = result;
    runtime_send13_diagnostic_block.phase_after = runtime_transport_phase;
        runtime_transport_send_submit_generation = generation;
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
    } else if (operation == RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE) {
        runtime_transport_cleanup_close_callback_result = result;
        runtime_transport_cleanup_close_callback_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_RECEIVE_SOCKET) {
        runtime_transport_receive_callback_result = result;
        runtime_transport_receive_callback_generation = generation;
    } else if (operation == RUNTIME_TRANSPORT_OP_SEND_SOCKET) {
        runtime_transport_send_callback_result = result;
        runtime_transport_send_callback_generation = generation;
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

static void runtime_sync_get_host_id_context_evidence(void)
{
    runtime_transport_get_host_id_callback_exit_count = runtime_transport_get_host_id_context.callback_exit_count;
    runtime_transport_get_host_id_stale_callback_count = runtime_transport_get_host_id_context.stale_callback_count;
    runtime_transport_get_host_id_duplicate_callback_count = runtime_transport_get_host_id_context.duplicate_callback_count;
}

static void runtime_sync_socket_context_evidence(void)
{
    runtime_transport_socket_callback_exit_count = runtime_transport_socket_context.callback_exit_count;
    runtime_transport_socket_stale_callback_count = runtime_transport_socket_context.stale_callback_count;
    runtime_transport_socket_duplicate_callback_count = runtime_transport_socket_context.duplicate_callback_count;
}

static void runtime_sync_bind_context_evidence(void)
{
    runtime_transport_bind_callback_exit_count = runtime_transport_bind_context.callback_exit_count;
    runtime_transport_bind_stale_callback_count = runtime_transport_bind_context.stale_callback_count;
    runtime_transport_bind_duplicate_callback_count = runtime_transport_bind_context.duplicate_callback_count;
}

static void runtime_sync_cleanup_close_context_evidence(void)
{
    runtime_transport_cleanup_close_callback_exit_count = runtime_transport_cleanup_close_context.callback_exit_count;
    runtime_transport_cleanup_close_stale_callback_count = runtime_transport_cleanup_close_context.stale_callback_count;
    runtime_transport_cleanup_close_duplicate_callback_count =
        runtime_transport_cleanup_close_context.duplicate_callback_count;
}

static void runtime_sync_receive_context_evidence(void)
{
    runtime_transport_receive_callback_exit_count = runtime_transport_receive_context.callback_exit_count;
    runtime_transport_receive_stale_callback_count = runtime_transport_receive_context.stale_callback_count;
    runtime_transport_receive_duplicate_callback_count = runtime_transport_receive_context.duplicate_callback_count;
}

static void runtime_sync_send_context_evidence(void)
{
    runtime_transport_send_callback_exit_count = runtime_transport_send_context.callback_exit_count;
    runtime_transport_send_stale_callback_count = runtime_transport_send_context.stale_callback_count;
    runtime_transport_send_duplicate_callback_count = runtime_transport_send_context.duplicate_callback_count;
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
    runtime_transport_get_host_id_target_address = 0;
    runtime_transport_get_host_id_command = 0;
    runtime_transport_get_host_id_submitted_fd = -1;
    runtime_transport_get_host_id_callback_pointer = 0;
    runtime_transport_get_host_id_context_pointer = 0;
    runtime_transport_get_host_id_callback_exit_count = 0;
    runtime_transport_get_host_id_stale_callback_count = 0;
    runtime_transport_get_host_id_duplicate_callback_count = 0;
    runtime_transport_get_host_id_service_started_before_submit = 0;
    runtime_transport_get_host_id_service_started_after_completion = 0;
    runtime_transport_ip_fd_before_get_host_id = -1;
    runtime_transport_ip_fd_after_get_host_id = -1;
    runtime_transport_get_host_id_pending_before_submit = 0;
    runtime_transport_get_host_id_pending_after_completion = 0;
    runtime_transport_get_host_id_phase_before_submit = 0;
    runtime_transport_get_host_id_phase_after_completion = 0;
    runtime_memzero(runtime_transport_get_host_id_pre_call_args, sizeof(runtime_transport_get_host_id_pre_call_args));
    runtime_transport_socket_submit_count = 0;
    runtime_transport_socket_callback_count = 0;
    runtime_transport_socket_submit_result = 0;
    runtime_transport_socket_callback_result = 0;
    runtime_transport_socket_submit_generation = 0;
    runtime_transport_socket_callback_generation = 0;
    runtime_transport_socket_target_address = 0;
    runtime_transport_socket_command = 0;
    runtime_transport_socket_submitted_fd = -1;
    runtime_transport_socket_callback_pointer = 0;
    runtime_transport_socket_context_pointer = 0;
    runtime_transport_socket_callback_exit_count = 0;
    runtime_transport_socket_stale_callback_count = 0;
    runtime_transport_socket_duplicate_callback_count = 0;
    runtime_transport_socket_fd_before_submit = -1;
    runtime_transport_socket_fd_after_completion = -1;
    runtime_transport_socket_request_address = 0;
    runtime_transport_socket_request_storage_size = 0;
    runtime_transport_socket_request_logical_size = 0;
    runtime_transport_socket_request_alignment = 0;
    runtime_transport_socket_family_value = 0;
    runtime_transport_socket_type_value = 0;
    runtime_transport_socket_protocol_value = 0;
    runtime_transport_socket_descriptor_valid = 0;
    runtime_transport_socket_ready = 0;
    runtime_memzero(runtime_transport_socket_request_bytes, sizeof(runtime_transport_socket_request_bytes));
    runtime_memzero(runtime_transport_socket_pre_call_args, sizeof(runtime_transport_socket_pre_call_args));
    runtime_transport_bind_submit_count = 0;
    runtime_transport_bind_callback_count = 0;
    runtime_transport_bind_submit_result = 0;
    runtime_transport_bind_callback_result = 0;
    runtime_transport_bind_submit_generation = 0;
    runtime_transport_bind_callback_generation = 0;
    runtime_transport_bind_target_address = 0;
    runtime_transport_bind_command = 0;
    runtime_transport_bind_submitted_fd = -1;
    runtime_transport_bind_callback_pointer = 0;
    runtime_transport_bind_context_pointer = 0;
    runtime_transport_bind_callback_exit_count = 0;
    runtime_transport_bind_stale_callback_count = 0;
    runtime_transport_bind_duplicate_callback_count = 0;
    runtime_transport_bind_request_address = 0;
    runtime_transport_bind_request_storage_size = 0;
    runtime_transport_bind_request_logical_size = 0;
    runtime_transport_bind_request_alignment = 0;
    runtime_transport_bind_sockaddr_length = 0;
    runtime_transport_bind_family_value = 0;
    runtime_transport_bind_port_value = 0;
    runtime_transport_bind_address_value = 0;
    runtime_memzero(runtime_transport_bind_request_bytes, sizeof(runtime_transport_bind_request_bytes));
    runtime_memzero(runtime_transport_bind_pre_call_args, sizeof(runtime_transport_bind_pre_call_args));
    runtime_transport_cleanup_close_callback_count = 0;
    runtime_transport_cleanup_close_submit_result = 0;
    runtime_transport_cleanup_close_callback_result = 0;
    runtime_transport_cleanup_close_submit_generation = 0;
    runtime_transport_cleanup_close_callback_generation = 0;
    runtime_transport_cleanup_close_target_address = 0;
    runtime_transport_cleanup_close_command = 0;
    runtime_transport_cleanup_close_submitted_fd = -1;
    runtime_transport_cleanup_close_callback_pointer = 0;
    runtime_transport_cleanup_close_context_pointer = 0;
    runtime_transport_cleanup_close_callback_exit_count = 0;
    runtime_transport_cleanup_close_stale_callback_count = 0;
    runtime_transport_cleanup_close_duplicate_callback_count = 0;
    runtime_transport_cleanup_close_request_address = 0;
    runtime_transport_cleanup_close_request_storage_size = 0;
    runtime_transport_cleanup_close_request_logical_size = 0;
    runtime_transport_cleanup_close_request_alignment = 0;
    runtime_transport_cleanup_close_request_value = -1;
    runtime_memzero(
        runtime_transport_cleanup_close_request_bytes,
        sizeof(runtime_transport_cleanup_close_request_bytes)
    );
    runtime_memzero(runtime_transport_cleanup_close_pre_call_args, sizeof(runtime_transport_cleanup_close_pre_call_args));
    runtime_transport_bound_flag = 0;
    runtime_transport_bound_address = 0;
    runtime_transport_socket_closed_after_bind_failure = 0;
    runtime_transport_socket_leak_detected = 0;
    runtime_transport_kd_fd = -1;
    runtime_transport_kd_closed = 0;
    runtime_transport_ip_fd = -1;
    runtime_transport_socket_fd = -1;
    runtime_transport_host_id = 0;
    runtime_transport_host_id_available = 0;
    runtime_transport_host_id_ready = 0;
    runtime_transport_service_started = 0;
    runtime_transport_bound_port = runtime_cp3c_config_block.server_port;
    runtime_transport_receive_arm_count = 0;
    runtime_transport_receive_rearm_count = 0;
    runtime_transport_receive_submit_count = 0;
    runtime_transport_send_submit_count = 0;
    runtime_transport_receive_count = 0;
    runtime_transport_receive_bytes = 0;
    runtime_transport_send_count = 0;
    runtime_transport_send_bytes = 0;
    runtime_transport_last_receive_length = 0;
    runtime_transport_last_send_length = 0;
    runtime_transport_prepared_send_length = 0;
    runtime_transport_last_peer_ipv4 = 0;
    runtime_transport_last_peer_port = 0;
    runtime_transport_last_peer_family = 0;
    runtime_transport_last_peer_length = 0;
    runtime_transport_last_submit_result = 0;
    runtime_transport_receive_submit_result_u32 = 0;
    runtime_transport_receive_submit_result = 0;
    runtime_transport_receive_callback_result = 0;
    runtime_transport_send_submit_result = 0;
    runtime_transport_send_callback_result = 0;
    runtime_transport_send_validated_result = 0;
    runtime_transport_receive_submit_generation = 0;
    runtime_transport_receive_callback_generation = 0;
    runtime_transport_send_submit_generation = 0;
    runtime_transport_send_callback_generation = 0;
    runtime_transport_configured_exchange_limit = PRIME3_IOS_UDP_DIAGNOSTIC_LOOP_COUNT;
    runtime_transport_completed_exchange_count = 0;
    runtime_transport_current_exchange_index = 0;
    runtime_transport_last_completed_exchange_index = 0;
    runtime_transport_previous_peer_ipv4 = 0;
    runtime_transport_previous_peer_port = 0;
    runtime_transport_rearm_submission_failure_count = 0;
    runtime_transport_loop_complete_transition_count = 0;
    runtime_transport_cleanup_deferred_count = 0;
    runtime_transport_receive_target_address = 0;
    runtime_transport_receive_command = 0;
    runtime_transport_send_target_address = 0;
    runtime_transport_send_command = 0;
    runtime_transport_receive_submitted_fd = -1;
    runtime_transport_receive_submitted_socket = -1;
    runtime_transport_send_submitted_fd = -1;
    runtime_transport_send_submitted_socket = -1;
    runtime_transport_receive_input_vector_count = 0;
    runtime_transport_receive_output_vector_count = 0;
    runtime_transport_send_input_vector_count = 0;
    runtime_transport_send_output_vector_count = 0;
    runtime_transport_receive_request_address = 0;
    runtime_transport_receive_request_storage_size = 0;
    runtime_transport_receive_request_logical_size = 0;
    runtime_transport_receive_request_alignment = 0;
    runtime_transport_receive_request_flags = 0;
    runtime_transport_send_request_address = 0;
    runtime_transport_send_request_storage_size = 0;
    runtime_transport_send_request_logical_size = 0;
    runtime_transport_send_request_alignment = 0;
    runtime_transport_send_request_flags = 0;
    runtime_transport_send_has_destaddr = 0;
    runtime_transport_receive_vector_address = 0;
    runtime_transport_receive_vector_storage_size = 0;
    runtime_transport_receive_vector_logical_size = 0;
    runtime_transport_receive_vector_alignment = 0;
    runtime_transport_send_vector_address = 0;
    runtime_transport_send_vector_storage_size = 0;
    runtime_transport_send_vector_logical_size = 0;
    runtime_transport_send_vector_alignment = 0;
    runtime_transport_receive_vector_0_pointer = 0;
    runtime_transport_receive_vector_0_length = 0;
    runtime_transport_receive_vector_1_pointer = 0;
    runtime_transport_receive_vector_1_length = 0;
    runtime_transport_receive_vector_2_pointer = 0;
    runtime_transport_receive_vector_2_length = 0;
    runtime_transport_send_vector_0_pointer = 0;
    runtime_transport_send_vector_0_length = 0;
    runtime_transport_send_vector_1_pointer = 0;
    runtime_transport_send_vector_1_length = 0;
    runtime_transport_receive_payload_buffer_address = 0;
    runtime_transport_receive_payload_capacity = 0;
    runtime_transport_receive_payload_alignment = 0;
    runtime_transport_send_payload_address = 0;
    runtime_transport_send_payload_capacity = 0;
    runtime_transport_send_payload_alignment = 0;
    runtime_transport_receive_source_address = 0;
    runtime_transport_receive_source_logical_size = 0;
    runtime_transport_receive_source_alignment = 0;
    runtime_transport_send_destination_address = 0;
    runtime_transport_send_destination_logical_size = 0;
    runtime_transport_send_destination_storage_size = 0;
    runtime_transport_send_destination_alignment = 0;
    runtime_transport_receive_callback_pointer = 0;
    runtime_transport_receive_context_pointer = 0;
    runtime_transport_receive_callback_exit_count = 0;
    runtime_transport_receive_stale_callback_count = 0;
    runtime_transport_receive_duplicate_callback_count = 0;
    runtime_transport_send_callback_pointer = 0;
    runtime_transport_send_context_pointer = 0;
    runtime_transport_send_callback_exit_count = 0;
    runtime_transport_send_stale_callback_count = 0;
    runtime_transport_send_duplicate_callback_count = 0;
    runtime_tcp_counter_sequence = 1;
    runtime_tcp_counter_sent = 0;
    runtime_tcp_counter_calls = 0;
    runtime_tcp_counter_bytes = 0;
    runtime_tcp_counter_partials = 0;
    runtime_tcp_echo_expected = 0;
    runtime_tcp_echo_received = 0;
    runtime_tcp_echo_receive_offset = 0;
    runtime_tcp_echo_receive_submit_result = 0;
    runtime_tcp_echo_receive_callback_result = 0;
    runtime_tcp_echo_receive_callback_count = 0;
    runtime_tcp_echo_partial_receive_count = 0;
    runtime_tcp_echo_success_count = 0;
    runtime_tcp_echo_mismatch_count = 0;
    runtime_tcp_echo_peer_close_count = 0;
    runtime_tcp_echo_receive_error_count = 0;
    runtime_tcp_echo_last_failure_phase = 0;
    runtime_tcp_echo_received_magic = 0;
    runtime_tcp_echo_received_type = 0;
    runtime_tcp_echo_received_length = 0;
    runtime_tcp_echo_expected_crc = 0;
    runtime_tcp_echo_received_crc = 0;
    runtime_tcp_echo_last_successful_sequence = 0;
    runtime_tcp_echo_receive_bytes = 0;
    runtime_protocol_frames_encoded = 0;
    runtime_protocol_frames_sent = 0;
    runtime_protocol_frames_received = 0;
    runtime_protocol_inbound_high_water = 0;
    runtime_protocol_outbound_high_water = 0;
    runtime_protocol_queue_overflow_count = 0;
    runtime_protocol_crc_failure_count = 0;
    runtime_protocol_sequence_failure_count = 0;
    runtime_protocol_handshake_failure_count = 0;
    runtime_protocol_client_test_sent_count = 0;
    runtime_protocol_server_test_received_count = 0;
    runtime_protocol_last_sent_type = 0;
    runtime_protocol_last_received_type = 0;
    runtime_protocol_client_tx_sequence = 1;
    runtime_protocol_server_rx_sequence = 0;
    runtime_protocol_last_client_acknowledged = 0;
    runtime_protocol_client_nonce = 0x43503357;
    runtime_protocol_server_nonce = 0;
    runtime_protocol_expected_type = 0;
    runtime_protocol_outbound_head = 0;
    runtime_protocol_outbound_tail = 0;
    runtime_protocol_outbound_count = 0;
    runtime_protocol_inbound_head = 0;
    runtime_protocol_inbound_tail = 0;
    runtime_protocol_inbound_count = 0;
    runtime_memzero(runtime_protocol_outbound_queue, sizeof(runtime_protocol_outbound_queue));
    runtime_memzero(runtime_protocol_inbound_queue, sizeof(runtime_protocol_inbound_queue));
    runtime_transport_polls_before_receive = 0;
    runtime_transport_polls_while_receive_pending = 0;
    runtime_transport_polls_after_receive = 0;
    runtime_transport_polls_before_send = 0;
    runtime_transport_polls_while_send_pending = 0;
    runtime_transport_polls_after_send = 0;
    runtime_transport_polls_after_loop_complete = 0;
    runtime_transport_cp3w_datagrams_processed = 0;
    runtime_transport_cp3w_frames_valid = 0;
    runtime_transport_cp3w_frames_invalid = 0;
    runtime_transport_cp3w_frames_too_short = 0;
    runtime_transport_cp3w_frames_invalid_magic = 0;
    runtime_transport_cp3w_frames_invalid_version = 0;
    runtime_transport_cp3w_frames_unsupported_type = 0;
    runtime_transport_cp3w_frames_nonzero_flags = 0;
    runtime_transport_cp3w_frames_length_mismatch = 0;
    runtime_transport_cp3w_frames_payload_too_large = 0;
    runtime_transport_cp3w_frames_invalid_payload = 0;
    runtime_transport_cp3w_frames_malformed = 0;
    runtime_transport_cp3w_framed_responses_submitted = 0;
    runtime_transport_cp3w_framed_responses_completed = 0;
    runtime_transport_cp3w_last_request_id = 0;
    runtime_transport_cp3w_last_response_id = 0;
    runtime_transport_cp3w_last_message_type = 0;
    runtime_transport_cp3w_last_declared_payload_length = 0;
    runtime_transport_cp3w_last_actual_payload_length = 0;
    runtime_transport_cp3w_last_frame_result = 0;
    runtime_transport_cp3w_final_datagram_index = 0;
    runtime_transport_cp3w_requests_dispatched = 0;
    runtime_transport_cp3w_hello_requests_received = 0;
    runtime_transport_cp3w_hello_successes = 0;
    runtime_transport_cp3w_hello_version_rejections = 0;
    runtime_transport_cp3w_hello_responses_submitted = 0;
    runtime_transport_cp3w_hello_responses_completed = 0;
    runtime_transport_cp3w_hello_duplicate_requests = 0;
    runtime_transport_cp3w_hello_renegotiation_rejections = 0;
    runtime_transport_cp3w_pre_hello_gated_commands = 0;
    runtime_transport_cp3w_not_negotiated_responses_submitted = 0;
    runtime_transport_cp3w_not_negotiated_responses_completed = 0;
    runtime_transport_cp3w_ping_requests_received = 0;
    runtime_transport_cp3w_pong_responses_submitted = 0;
    runtime_transport_cp3w_pong_responses_completed = 0;
    runtime_transport_cp3w_unsupported_commands_received = 0;
    runtime_transport_cp3w_unsupported_responses_submitted = 0;
    runtime_transport_cp3w_unsupported_responses_completed = 0;
    runtime_transport_cp3w_negotiated_flag = 0;
    runtime_transport_cp3w_selected_protocol_version = 0;
    runtime_transport_cp3w_client_nonce = 0;
    runtime_transport_cp3w_client_capabilities = 0;
    runtime_transport_cp3w_runtime_capabilities = 0;
    runtime_transport_cp3w_accepted_capabilities = 0;
    runtime_transport_cp3w_session_id = 0;
    runtime_transport_cp3w_runtime_build_id = RUNTIME_CP3W_RUNTIME_BUILD_ID;
    runtime_transport_cp3w_hello_min_protocol_version = 0;
    runtime_transport_cp3w_hello_max_protocol_version = 0;
    runtime_transport_cp3w_hello_client_name_length = 0;
    runtime_transport_cp3w_last_command = 0;
    runtime_transport_cp3w_last_response_status = 0;
    runtime_transport_cp3w_last_ping_payload_length = 0;
    runtime_transport_cp3w_last_dispatch_result = 0;
    runtime_transport_cp3w_game_identity_requests = 0;
    runtime_transport_cp3w_game_identity_successes = 0;
    runtime_transport_cp3w_game_identity_pre_hello_rejections = 0;
    runtime_transport_cp3w_game_identity_capability_rejections = 0;
    runtime_transport_cp3w_game_identity_invalid_payload_rejections = 0;
    runtime_transport_cp3w_game_identity_executable_validations = 0;
    runtime_transport_cp3w_game_identity_executable_failures = 0;
    runtime_transport_cp3w_game_identity_game_state_valid = 0;
    runtime_transport_cp3w_game_identity_game_state_invalid = 0;
    runtime_transport_cp3w_game_identity_player_state_valid = 0;
    runtime_transport_cp3w_game_identity_player_state_invalid = 0;
    runtime_transport_cp3w_game_identity_inventory_root_available = 0;
    runtime_transport_cp3w_game_identity_responses_submitted = 0;
    runtime_transport_cp3w_game_identity_responses_completed = 0;
    runtime_transport_cp3w_game_identity_capability_errors_submitted = 0;
    runtime_transport_cp3w_game_identity_capability_errors_completed = 0;
    runtime_transport_cp3w_game_identity_invalid_payload_errors_submitted = 0;
    runtime_transport_cp3w_game_identity_invalid_payload_errors_completed = 0;
    runtime_transport_cp3w_game_identity_last_request_id = 0;
    runtime_transport_cp3w_game_identity_last_status = 0;
    runtime_transport_cp3w_game_identity_last_availability = 0;
    runtime_transport_cp3w_game_identity_last_profile_id = RUNTIME_CP3W_PROFILE_ID;
    runtime_transport_cp3w_game_identity_last_fingerprint = RUNTIME_CP3W_PROFILE_FINGERPRINT;
    runtime_transport_cp3w_game_identity_executable_recognized = 0;
    runtime_transport_cp3w_game_identity_game_state_pointer = 0;
    runtime_transport_cp3w_game_identity_player_state_pointer = 0;
    runtime_transport_cp3w_game_identity_inventory_root_pointer = 0;
    runtime_transport_cp3w_inventory_requests = 0;
    runtime_transport_cp3w_inventory_available_snapshots = 0;
    runtime_transport_cp3w_inventory_unavailable_snapshots = 0;
    runtime_transport_cp3w_inventory_pre_hello_rejections = 0;
    runtime_transport_cp3w_inventory_capability_rejections = 0;
    runtime_transport_cp3w_inventory_invalid_payload_rejections = 0;
    runtime_transport_cp3w_inventory_executable_failures = 0;
    runtime_transport_cp3w_inventory_game_state_valid = 0;
    runtime_transport_cp3w_inventory_game_state_invalid = 0;
    runtime_transport_cp3w_inventory_root_valid = 0;
    runtime_transport_cp3w_inventory_root_invalid = 0;
    runtime_transport_cp3w_inventory_range_failures = 0;
    runtime_transport_cp3w_inventory_consistency_successes = 0;
    runtime_transport_cp3w_inventory_consistency_failures = 0;
    runtime_transport_cp3w_inventory_responses_submitted = 0;
    runtime_transport_cp3w_inventory_responses_completed = 0;
    runtime_transport_cp3w_inventory_last_request_id = 0;
    runtime_transport_cp3w_inventory_last_status = 0;
    runtime_transport_cp3w_inventory_last_availability = 0;
    runtime_transport_cp3w_inventory_snapshot_sequence = 0;
    runtime_transport_cp3w_inventory_last_root = 0;
    runtime_memzero(runtime_transport_cp3w_hello_client_name_bytes, sizeof(runtime_transport_cp3w_hello_client_name_bytes));
    runtime_memzero(runtime_transport_receive_request_bytes, sizeof(runtime_transport_receive_request_bytes));
    runtime_memzero(runtime_transport_receive_source_bytes, sizeof(runtime_transport_receive_source_bytes));
    runtime_memzero(runtime_transport_send_request_bytes, sizeof(runtime_transport_send_request_bytes));
    runtime_memzero(runtime_transport_send_destination_bytes, sizeof(runtime_transport_send_destination_bytes));
    runtime_memzero(runtime_transport_send_payload_bytes, sizeof(runtime_transport_send_payload_bytes));
    runtime_memzero(runtime_transport_last_receive_preview, sizeof(runtime_transport_last_receive_preview));
    runtime_memzero(runtime_transport_last_send_preview, sizeof(runtime_transport_last_send_preview));
    runtime_memzero(runtime_transport_receive_payload_buffer, sizeof(runtime_transport_receive_payload_buffer));
    runtime_memzero(runtime_transport_nwc24_output_buffer, sizeof(runtime_transport_nwc24_output_buffer));
    runtime_memzero(&runtime_transport_nwc24_context, sizeof(runtime_transport_nwc24_context));
    runtime_memzero(&runtime_transport_kd_close_context, sizeof(runtime_transport_kd_close_context));
    runtime_memzero(&runtime_transport_open_ip_context, sizeof(runtime_transport_open_ip_context));
    runtime_memzero(&runtime_transport_startup_context, sizeof(runtime_transport_startup_context));
    runtime_memzero(&runtime_transport_get_host_id_context, sizeof(runtime_transport_get_host_id_context));
    runtime_memzero(&runtime_transport_socket_context, sizeof(runtime_transport_socket_context));
    runtime_memzero(&runtime_transport_bind_context, sizeof(runtime_transport_bind_context));
    runtime_memzero(&runtime_transport_cleanup_close_context, sizeof(runtime_transport_cleanup_close_context));
    runtime_memzero(&runtime_transport_receive_context, sizeof(runtime_transport_receive_context));
    runtime_memzero(&runtime_tcp_echo_receive_context, sizeof(runtime_tcp_echo_receive_context));
    runtime_memzero(&runtime_transport_send_context, sizeof(runtime_transport_send_context));
    runtime_memzero(&runtime_transport_socket_request, sizeof(runtime_transport_socket_request));
    runtime_memzero(&runtime_transport_bind_params, sizeof(runtime_transport_bind_params));
    runtime_memzero(&runtime_transport_send_request, sizeof(runtime_transport_send_request));
    runtime_memzero(&runtime_transport_receive_request, sizeof(runtime_transport_receive_request));
    runtime_memzero(runtime_transport_receive_vectors, sizeof(runtime_transport_receive_vectors));
    runtime_memzero(runtime_transport_send_vectors, sizeof(runtime_transport_send_vectors));
    runtime_memzero(&runtime_network_diagnostics_block, sizeof(runtime_network_diagnostics_block));
    runtime_memzero(runtime_transport_getsockname_address, sizeof(runtime_transport_getsockname_address));
    runtime_network_diagnostics_block.magic = RUNTIME_DIAGNOSTICS_MAGIC;
    runtime_network_diagnostics_block.version = RUNTIME_DIAGNOSTICS_VERSION;
    runtime_network_diagnostics_block.size = RUNTIME_DIAGNOSTICS_SIZE;
    runtime_network_diagnostics_block.build_id = PRIME3_CP3W_RUNTIME_BUILD_ID;
    runtime_network_diagnostics_block.initial_delay_polls = RUNTIME_INITIAL_DELAY_POLL_INTERVAL;
    runtime_network_diagnostics_block.retry_delay_polls = RUNTIME_RETRY_DELAY_POLL_INTERVAL;
    runtime_network_diagnostics_block.requested_bind_address = INADDR_ANY;
    runtime_network_diagnostics_block.requested_bind_port = runtime_cp3c_config_block.server_port;
    runtime_network_diagnostics_block.byte_order_applied = 1;
    runtime_network_diagnostics_block.auto_retry_enabled = 1;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    runtime_network_diagnostics_block.ios_version = RUNTIME_NATIVE_EXECUTION_CANARY;
    runtime_network_diagnostics_block.ios_revision = RUNTIME_NATIVE_STAGE_RELOCATED_INITIALIZED;
    runtime_network_diagnostics_block.overlay_enabled = 1;
#endif
    runtime_network_diagnostics_block.last_close_descriptor = -1;
    runtime_network_diagnostics_block.last_shutdown_descriptor = -1;
    runtime_transport_retry_deadline = 0;
    runtime_transport_last_error_phase = 0;
    runtime_transport_initialization_success_count = 0;
    runtime_transport_restart_request_count = 0;
    runtime_transport_socket_recovery_count = 0;
    runtime_transport_socket_lost_count = 0;
    runtime_transport_getsockname_submit_count = 0;
    runtime_transport_getsockname_result = 0;
    runtime_transport_actual_bound_address = 0;
    runtime_transport_actual_bound_port = 0;
    runtime_transport_last_successful_bind_poll = 0;
    runtime_transport_last_packet_receive_poll = 0;
    runtime_transport_last_packet_send_poll = 0;
    runtime_transport_transient_receive_error_count = 0;
    runtime_transport_fatal_receive_error_count = 0;
    runtime_transport_send_failure_count = 0;
    runtime_transport_close_call_count = 0;
    runtime_transport_cleanup_count = 0;
    runtime_transport_last_close_descriptor = -1;
    runtime_transport_last_heartbeat_result = 0;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    runtime_native_next_host_id_poll = 0;
    runtime_native_next_host_id_timebase = 0;
    runtime_native_low_level_recovery_active = 0;
    runtime_native_first_valid_host_id_poll = 0;
    runtime_native_next_beacon_poll = 0;
    runtime_native_next_beacon_timebase = 0;
    runtime_native_beacon_attempt_count = 0;
    runtime_native_beacon_success_count = 0;
    runtime_native_beacon_submission_failure_count = 0;
    runtime_native_beacon_completion_failure_count = 0;
    runtime_native_first_successful_beacon_poll = 0;
    runtime_native_last_successful_beacon_poll = 0;
    runtime_native_last_beacon_submit_result = 0;
    runtime_native_last_beacon_completion_result = 0;
    runtime_native_overlay_top_register = 0;
    runtime_native_overlay_bottom_register = 0;
    runtime_native_overlay_geometry = 0;
    runtime_native_overlay_render_count = 0;
    runtime_native_post_copy_hook_result = 0;
    runtime_native_install_post_copy_hook();
#endif
    runtime_transport_cleanup_close_request = -1;
#if PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
    runtime_transport_phase = (runtime_transport_uses_receive_mode() || runtime_transport_is_native_wc24_bootstrap_mode())
        ? RUNTIME_TRANSPORT_PHASE_INITIAL_DELAY
        : RUNTIME_TRANSPORT_PHASE_OPEN_KD;
    runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_INIT;
#else
    runtime_transport_phase = RUNTIME_TRANSPORT_PHASE_UNINITIALIZED;
    runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
#endif
}

#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
#define RUNTIME_GLYPH5(a, b, c, d, e) ((u16)(((a) << 12) | ((b) << 9) | ((c) << 6) | ((d) << 3) | (e)))

static u16 runtime_native_overlay_glyph(u8 character)
{
    switch (character) {
    case '0': return RUNTIME_GLYPH5(7, 5, 5, 5, 7);
    case '1': return RUNTIME_GLYPH5(2, 6, 2, 2, 7);
    case '2': return RUNTIME_GLYPH5(7, 1, 7, 4, 7);
    case '3': return RUNTIME_GLYPH5(7, 1, 7, 1, 7);
    case '4': return RUNTIME_GLYPH5(5, 5, 7, 1, 1);
    case '5': return RUNTIME_GLYPH5(7, 4, 7, 1, 7);
    case '6': return RUNTIME_GLYPH5(7, 4, 7, 5, 7);
    case '7': return RUNTIME_GLYPH5(7, 1, 1, 1, 1);
    case '8': return RUNTIME_GLYPH5(7, 5, 7, 5, 7);
    case '9': return RUNTIME_GLYPH5(7, 5, 7, 1, 7);
    case 'A': return RUNTIME_GLYPH5(2, 5, 7, 5, 5);
    case 'B': return RUNTIME_GLYPH5(6, 5, 6, 5, 6);
    case 'C': return RUNTIME_GLYPH5(3, 4, 4, 4, 3);
    case 'D': return RUNTIME_GLYPH5(6, 5, 5, 5, 6);
    case 'E': return RUNTIME_GLYPH5(7, 4, 6, 4, 7);
    case 'F': return RUNTIME_GLYPH5(7, 4, 6, 4, 4);
    case 'G': return RUNTIME_GLYPH5(3, 4, 5, 5, 3);
    case 'H': return RUNTIME_GLYPH5(5, 5, 7, 5, 5);
    case 'I': return RUNTIME_GLYPH5(7, 2, 2, 2, 7);
    case 'J': return RUNTIME_GLYPH5(1, 1, 1, 5, 2);
    case 'K': return RUNTIME_GLYPH5(5, 5, 6, 5, 5);
    case 'L': return RUNTIME_GLYPH5(4, 4, 4, 4, 7);
    case 'M': return RUNTIME_GLYPH5(5, 7, 7, 5, 5);
    case 'N': return RUNTIME_GLYPH5(5, 7, 7, 7, 5);
    case 'O': return RUNTIME_GLYPH5(2, 5, 5, 5, 2);
    case 'P': return RUNTIME_GLYPH5(6, 5, 6, 4, 4);
    case 'Q': return RUNTIME_GLYPH5(2, 5, 5, 3, 1);
    case 'R': return RUNTIME_GLYPH5(6, 5, 6, 5, 5);
    case 'S': return RUNTIME_GLYPH5(3, 4, 2, 1, 6);
    case 'T': return RUNTIME_GLYPH5(7, 2, 2, 2, 2);
    case 'U': return RUNTIME_GLYPH5(5, 5, 5, 5, 7);
    case 'V': return RUNTIME_GLYPH5(5, 5, 5, 5, 2);
    case 'W': return RUNTIME_GLYPH5(5, 5, 7, 7, 5);
    case 'X': return RUNTIME_GLYPH5(5, 5, 2, 5, 5);
    case 'Y': return RUNTIME_GLYPH5(5, 5, 2, 2, 2);
    case 'Z': return RUNTIME_GLYPH5(7, 1, 2, 4, 7);
    case ':': return RUNTIME_GLYPH5(0, 2, 0, 2, 0);
    case '-': return RUNTIME_GLYPH5(0, 0, 7, 0, 0);
    case '.': return RUNTIME_GLYPH5(0, 0, 0, 0, 2);
    case '/': return RUNTIME_GLYPH5(1, 1, 2, 4, 4);
    default: return 0;
    }
}

static void runtime_native_overlay_append_text(u8* line, u32* length, const char* text)
{
    while (*text != '\0' && *length < 63) {
        line[*length] = (u8)*text;
        *length += 1;
        text += 1;
    }
}

static void runtime_native_overlay_append_u32(u8* line, u32* length, u32 value)
{
    u8 digits[10];
    u32 count = 0;
    do {
        digits[count] = (u8)('0' + value % 10);
        value /= 10;
        count += 1;
    } while (value != 0 && count < sizeof(digits));
    while (count != 0 && *length < 63) {
        count -= 1;
        line[*length] = digits[count];
        *length += 1;
    }
}

static void runtime_native_overlay_append_s32(u8* line, u32* length, s32 value)
{
    u32 magnitude;
    if (value < 0) {
        if (*length < 63) {
            line[*length] = '-';
            *length += 1;
        }
        magnitude = 0U - (u32)value;
    } else {
        magnitude = (u32)value;
    }
    runtime_native_overlay_append_u32(line, length, magnitude);
}

static void runtime_native_overlay_append_ipv4(u8* line, u32* length, u32 address)
{
    runtime_native_overlay_append_u32(line, length, address >> 24);
    runtime_native_overlay_append_text(line, length, ".");
    runtime_native_overlay_append_u32(line, length, (address >> 16) & 0xFFU);
    runtime_native_overlay_append_text(line, length, ".");
    runtime_native_overlay_append_u32(line, length, (address >> 8) & 0xFFU);
    runtime_native_overlay_append_text(line, length, ".");
    runtime_native_overlay_append_u32(line, length, address & 0xFFU);
}

static const char* runtime_native_overlay_phase_name(u32 phase)
{
    switch (phase) {
    case RUNTIME_TRANSPORT_PHASE_INITIAL_DELAY: return "INITIAL DELAY";
    case RUNTIME_TRANSPORT_PHASE_NATIVE_BOOTSTRAP: return "NATIVE BOOTSTRAP";
    case RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_HOST_ID: return "WAIT HOST ID";
    case RUNTIME_TRANSPORT_PHASE_NATIVE_HOST_ID_TIMEOUT: return "HOST ID TIMEOUT";
    case RUNTIME_TRANSPORT_PHASE_GETHOSTID: return "GET HOST ID";
    case RUNTIME_TRANSPORT_PHASE_WAIT_GETHOSTID: return "HOST ID PENDING";
    case RUNTIME_TRANSPORT_PHASE_NATIVE_CREATE_BEACON_SOCKET: return "CREATE SOCKET";
    case RUNTIME_TRANSPORT_PHASE_CREATE_SOCKET: return "SOCKET SUBMIT";
    case RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET: return "SOCKET PENDING";
    case RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON_INTERVAL: return "BEACON INTERVAL";
    case RUNTIME_TRANSPORT_PHASE_NATIVE_SUBMIT_BEACON: return "BEACON SUBMIT";
    case RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON: return "BEACON PENDING";
    case RUNTIME_TRANSPORT_PHASE_NATIVE_BEACON_COMPLETE: return "BEACON COMPLETE";
    case RUNTIME_TRANSPORT_PHASE_FAILED: return "FAILED";
    default: return "OTHER";
    }
}

typedef struct runtime_native_xfb {
    volatile u8* address;
    u32 physical_address;
    u32 width;
    u32 height;
    u32 stride;
} runtime_native_xfb;

static u32 runtime_native_xfb_range_valid(u32 physical_address, u32 byte_size);

static u32 runtime_native_decode_xfb_physical(
    u32 physical_address,
    u32 width,
    u32 height,
    u32 stride,
    runtime_native_xfb* xfb
)
{
    u32 row_bytes = stride * 2U;
    u32 byte_size;
    if (
        width < 320U || width > 720U || stride < width || stride > 2048U
        || height < 200U || height > 576U
    ) {
        return 0;
    }
    byte_size = (height - 1U) * row_bytes + width * 2U;
    if (!runtime_native_xfb_range_valid(physical_address, byte_size)) {
        return 0;
    }
    xfb->physical_address = physical_address;
    xfb->address = (volatile u8*)(0x80000000U | physical_address);
    xfb->width = width;
    xfb->height = height;
    xfb->stride = stride;
    return 1;
}

static u32 runtime_native_xfb_range_valid(u32 physical_address, u32 byte_size)
{
    u32 end = physical_address + byte_size;
    if (end < physical_address) {
        return 0;
    }
    return (physical_address >= 0x00001000U && end <= 0x01800000U)
        || (physical_address >= 0x10000000U && end <= 0x14000000U);
}

static u32 runtime_native_decode_xfb(
    u32 register_value,
    u32 page_offset,
    u32 width,
    u32 height,
    u32 stride,
    runtime_native_xfb* xfb
)
{
    u32 physical_address = register_value & 0x00FFFFFFU;
    if (page_offset != 0) {
        physical_address <<= 5;
    }
    return runtime_native_decode_xfb_physical(physical_address, width, height, stride, xfb);
}

static void runtime_native_overlay_set_luma(
    const runtime_native_xfb* xfb,
    u32 x,
    u32 y,
    u8 luma
)
{
    if (x < xfb->width && y < xfb->height) {
        xfb->address[(y * xfb->stride + x) * 2U] = luma;
    }
}

static void runtime_native_overlay_fill_rect(
    const runtime_native_xfb* xfb,
    u32 left,
    u32 top,
    u32 width,
    u32 height,
    u8 luma
)
{
    u32 y = top;
    u32 bottom = top + height;
    u32 right = left + width;
    if (bottom > xfb->height) {
        bottom = xfb->height;
    }
    if (right > xfb->width) {
        right = xfb->width;
    }
    while (y < bottom) {
        u32 x = left;
        while (x < right) {
            runtime_native_overlay_set_luma(xfb, x, y, luma);
            x += 1;
        }
        y += 1;
    }
}

static void runtime_native_overlay_border_rect(
    const runtime_native_xfb* xfb,
    u32 left,
    u32 top,
    u32 width,
    u32 height,
    u8 luma
)
{
    u32 x = left;
    u32 y = top;
    while (x < left + width) {
        runtime_native_overlay_set_luma(xfb, x, top, luma);
        runtime_native_overlay_set_luma(xfb, x, top + height - 1U, luma);
        x += 1;
    }
    while (y < top + height) {
        runtime_native_overlay_set_luma(xfb, left, y, luma);
        runtime_native_overlay_set_luma(xfb, left + width - 1U, y, luma);
        y += 1;
    }
}

static void runtime_native_overlay_draw_line(
    const runtime_native_xfb* xfb,
    u32 x_origin,
    u32 y,
    const u8* line,
    u32 length
)
{
    u32 index = 0;
    while (index < length) {
        u16 glyph = runtime_native_overlay_glyph(line[index]);
        u32 row = 0;
        while (row < 5) {
            u32 columns = (glyph >> ((4 - row) * 3)) & 7U;
            u32 column = 0;
            while (column < 3) {
                if ((columns & (1U << (2 - column))) != 0) {
                    u32 scale_y = 0;
                    while (scale_y < 2) {
                        u32 scale_x = 0;
                        while (scale_x < 2) {
                            u32 x = x_origin + index * 8 + column * 2 + scale_x;
                            runtime_native_overlay_set_luma(xfb, x, y + row * 2 + scale_y, 235);
                            scale_x += 1;
                        }
                        scale_y += 1;
                    }
                }
                column += 1;
            }
            row += 1;
        }
        index += 1;
    }
}

static void runtime_native_overlay_draw_xfb(const runtime_native_xfb* xfb)
{
    u8 line[64];
    u32 line_number = 0;
    u32 panel_width = xfb->width > 466U ? 456U : xfb->width - 10U;
    u32 panel_height = xfb->height > 190U ? 180U : xfb->height - 10U;
    u32 flush_bottom = panel_height + 8U;
    runtime_native_overlay_fill_rect(xfb, 8, 8, panel_width, panel_height, 32);
    runtime_native_overlay_border_rect(xfb, 8, 8, panel_width, panel_height, 235);
    runtime_native_overlay_fill_rect(xfb, 12, 12, 180, 18, 80);
    runtime_native_overlay_border_rect(xfb, 12, 12, 180, 18, 235);
#define RUNTIME_OVERLAY_BEGIN(label) \
    do { \
        line_number = 0; \
        runtime_native_overlay_append_text(line, &line_number, label); \
    } while (0)
#define RUNTIME_OVERLAY_DRAW(row) runtime_native_overlay_draw_line(xfb, 16, 38 + (row) * 12, line, line_number)
    RUNTIME_OVERLAY_BEGIN("STAGE ");
    runtime_native_overlay_append_u32(line, &line_number, runtime_network_diagnostics_block.ios_revision);
    runtime_native_overlay_append_text(line, &line_number, " POLL ");
    runtime_native_overlay_append_u32(
        line,
        &line_number,
        runtime_network_diagnostics_block.shutdown_call_count % 10000U
    );
    runtime_native_overlay_draw_line(xfb, 18, 16, line, line_number);
    RUNTIME_OVERLAY_BEGIN("WC24 OPEN: ");
    runtime_native_overlay_append_s32(line, &line_number, runtime_transport_nwc24_synchronous_result);
    RUNTIME_OVERLAY_DRAW(0);
    RUNTIME_OVERLAY_BEGIN("NATIVE BOOTSTRAP: ");
    runtime_native_overlay_append_s32(line, &line_number, runtime_transport_startup_callback_result);
    RUNTIME_OVERLAY_DRAW(1);
    RUNTIME_OVERLAY_BEGIN("SO DESCRIPTOR: ");
    runtime_native_overlay_append_s32(line, &line_number, runtime_transport_ip_fd);
    RUNTIME_OVERLAY_DRAW(2);
    RUNTIME_OVERLAY_BEGIN("HOST ATTEMPTS: ");
    runtime_native_overlay_append_u32(line, &line_number, runtime_transport_get_host_id_submit_count);
    RUNTIME_OVERLAY_DRAW(3);
    RUNTIME_OVERLAY_BEGIN("HOST RESULT: ");
    runtime_native_overlay_append_s32(line, &line_number, runtime_transport_get_host_id_callback_result);
    if (runtime_transport_host_id_ready != 0) {
        runtime_native_overlay_append_text(line, &line_number, " / ");
        runtime_native_overlay_append_ipv4(line, &line_number, runtime_transport_host_id);
    }
    RUNTIME_OVERLAY_DRAW(4);
    RUNTIME_OVERLAY_BEGIN("SOCKET RESULT: ");
    runtime_native_overlay_append_s32(line, &line_number, runtime_transport_socket_callback_result);
    RUNTIME_OVERLAY_DRAW(5);
    RUNTIME_OVERLAY_BEGIN("BEACON ATTEMPTS: ");
    runtime_native_overlay_append_u32(line, &line_number, runtime_native_beacon_attempt_count);
    runtime_native_overlay_append_text(line, &line_number, "/");
    runtime_native_overlay_append_u32(line, &line_number, RUNTIME_NATIVE_BEACON_ATTEMPT_LIMIT);
    RUNTIME_OVERLAY_DRAW(6);
    RUNTIME_OVERLAY_BEGIN("SUBMIT RESULT: ");
    runtime_native_overlay_append_s32(line, &line_number, runtime_native_last_beacon_submit_result);
    RUNTIME_OVERLAY_DRAW(7);
    RUNTIME_OVERLAY_BEGIN("SEND RESULT: ");
    runtime_native_overlay_append_s32(line, &line_number, runtime_native_last_beacon_completion_result);
    RUNTIME_OVERLAY_DRAW(8);
    RUNTIME_OVERLAY_BEGIN("PHASE: ");
    runtime_native_overlay_append_u32(line, &line_number, runtime_transport_phase);
    runtime_native_overlay_append_text(line, &line_number, " ");
    runtime_native_overlay_append_text(line, &line_number, runtime_native_overlay_phase_name(runtime_transport_phase));
    RUNTIME_OVERLAY_DRAW(9);
    RUNTIME_OVERLAY_BEGIN("ERROR PHASE: ");
    runtime_native_overlay_append_u32(line, &line_number, runtime_transport_last_error_phase);
    RUNTIME_OVERLAY_DRAW(10);
    RUNTIME_OVERLAY_BEGIN("LAST ERROR: ");
    runtime_native_overlay_append_s32(line, &line_number, runtime_transport_last_error);
    RUNTIME_OVERLAY_DRAW(11);
#undef RUNTIME_OVERLAY_DRAW
#undef RUNTIME_OVERLAY_BEGIN
    if (flush_bottom > xfb->height) {
        flush_bottom = xfb->height;
    }
    runtime_cache_flush(
        xfb->address + 8U * xfb->stride * 2U,
        (flush_bottom - 8U) * xfb->stride * 2U
    );
}

static void runtime_native_overlay_draw(void)
{
    volatile u16* vi = (volatile u16*)0xCC002000U;
    u32 control = vi[1];
    u32 vertical_timing = vi[0];
    u32 picture_configuration = vi[0x48U / 2U];
    u32 width = ((picture_configuration >> 8) & 0x7FU) * 16U;
    u32 stride = (picture_configuration & 0xFFU) * 16U;
    u32 height = (vertical_timing >> 4) & 0x3FFU;
    u32 register_values[4];
    u32 page_offsets[4];
    runtime_native_xfb xfb;
    u32 index = 0;
    u32 rendered_addresses[4] = {0, 0, 0, 0};
    u32 rendered_count = 0;
    register_values[0] = ((u32)vi[0x1CU / 2U] << 16) | vi[0x1EU / 2U];
    register_values[1] = ((u32)vi[0x24U / 2U] << 16) | vi[0x26U / 2U];
    register_values[2] = ((u32)vi[0x20U / 2U] << 16) | vi[0x22U / 2U];
    register_values[3] = ((u32)vi[0x28U / 2U] << 16) | vi[0x2AU / 2U];
    page_offsets[0] = (register_values[0] >> 28) & 1U;
    page_offsets[1] = page_offsets[0];
    page_offsets[2] = (register_values[2] >> 28) & 1U;
    page_offsets[3] = page_offsets[2];
    runtime_native_overlay_top_register = register_values[0];
    runtime_native_overlay_bottom_register = register_values[1];
    runtime_native_overlay_geometry = (picture_configuration << 16) | vertical_timing;
    while (index < 4U) {
        u32 duplicate = 0;
        u32 rendered_index = 0;
        if (index >= 2U && (control & 8U) == 0) {
            index += 1;
            continue;
        }
        if (!runtime_native_decode_xfb(
                register_values[index],
                page_offsets[index],
                width,
                height,
                stride,
                &xfb
            )) {
            index += 1;
            continue;
        }
        while (rendered_index < rendered_count) {
            if (rendered_addresses[rendered_index] == xfb.physical_address) {
                duplicate = 1;
                break;
            }
            rendered_index += 1;
        }
        if (duplicate == 0) {
            runtime_native_overlay_draw_xfb(&xfb);
            rendered_addresses[rendered_count] = xfb.physical_address;
            rendered_count += 1;
        }
        index += 1;
    }
    runtime_native_overlay_render_count = rendered_count;
}

void runtime_native_overlay_draw_destination(u32 destination)
{
    volatile u16* vi = (volatile u16*)0xCC002000U;
    u32 vertical_timing = vi[0];
    u32 picture_configuration = vi[0x48U / 2U];
    u32 width = ((picture_configuration >> 8) & 0x7FU) * 16U;
    u32 stride = (picture_configuration & 0xFFU) * 16U;
    u32 height = (vertical_timing >> 4) & 0x3FFU;
    u32 physical_address = destination & 0x3FFFFFFFU;
    runtime_native_xfb xfb;
    if (runtime_native_decode_xfb_physical(physical_address, width, height, stride, &xfb)) {
        runtime_native_overlay_draw_xfb(&xfb);
    }
    physical_address += width * 2U;
    if (runtime_native_decode_xfb_physical(physical_address, width, height, stride, &xfb)) {
        runtime_native_overlay_draw_xfb(&xfb);
    }
    runtime_native_overlay_draw();
}
#undef RUNTIME_GLYPH5
#endif

void runtime_poll_entry_impl(void)
{
    u32 state_machine_entered = 0;
    runtime_poll_counter += 1;
    runtime_poll_heartbeat = runtime_poll_counter;
    runtime_poll_last_sequence = runtime_poll_counter;
    runtime_diag_increment(&runtime_poll_entry_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_POLL_ENTRY);

#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    if (runtime_network_diagnostics_block.ios_version == RUNTIME_NATIVE_EXECUTION_CANARY) {
        runtime_network_diagnostics_block.shutdown_call_count += 1;
        if (runtime_network_diagnostics_block.ios_revision < RUNTIME_NATIVE_STAGE_RECURRING_HOOK_ENTERED) {
            runtime_native_set_stage(RUNTIME_NATIVE_STAGE_RECURRING_HOOK_ENTERED);
        }
    }
#endif

#if !PRIME3_ENABLE_IOS_UDP_DIAGNOSTIC
    runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
    goto runtime_poll_exit;
#endif

    runtime_last_transport_phase_before_step = runtime_transport_phase;
    runtime_diag_increment(&runtime_state_machine_entry_count);
    runtime_diag_store_marker(RUNTIME_DIAGNOSTIC_MARKER_STATE_MACHINE_ENTRY);
    state_machine_entered = 1;

#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    if (
        runtime_transport_is_native_wc24_bootstrap_mode()
        && runtime_network_diagnostics_block.ios_revision < RUNTIME_NATIVE_STAGE_MODE_RECOGNIZED
    ) {
        runtime_native_set_stage(RUNTIME_NATIVE_STAGE_MODE_RECOGNIZED);
    }
#endif

    if (runtime_network_diagnostics_block.reset_counters_request != 0) {
        runtime_network_diagnostics_block.reset_counters_request = 0;
        runtime_transport_receive_count = 0;
        runtime_transport_send_count = 0;
        runtime_transport_cp3w_frames_malformed = 0;
        runtime_transport_transient_receive_error_count = 0;
        runtime_transport_fatal_receive_error_count = 0;
        runtime_transport_send_failure_count = 0;
    }
    if (
        runtime_network_diagnostics_block.restart_request != 0
        && runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_NONE
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        && !runtime_transport_is_native_wc24_bootstrap_mode()
#endif
    ) {
        runtime_network_diagnostics_block.restart_request = 0;
        runtime_transport_restart_request_count += 1;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_RESTART_REQUESTED, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
    }
    if (
        runtime_network_diagnostics_block.heartbeat_request != 0
        && runtime_transport_pending_operation == RUNTIME_TRANSPORT_OP_NONE
        && runtime_transport_bound_flag != 0
        && runtime_transport_last_peer_family == AF_INET
    ) {
        runtime_network_diagnostics_block.heartbeat_request = 0;
        runtime_prepare_heartbeat();
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SUBMIT_HEARTBEAT, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
    }

    if (
        runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SO_STARTED
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SOCKET_READY
        || (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVED_DATAGRAM
            && !(runtime_transport_is_recvfrom_once_mode() || runtime_transport_is_recv_send_loop_mode()))
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVE_SUBMIT_FAILED
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVE_ASYNC_FAILED
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVE_INVALID_POSITIVE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVE_OVERSIZED_RESULT
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVE_STALE_CALLBACK
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVE_DUPLICATE_CALLBACK
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVE_CLEANUP_DEFERRED
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SENT_DATAGRAM
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_SUBMIT_FAILED
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_ASYNC_FAILED
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_INVALID_POSITIVE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_STALE_CALLBACK
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_DUPLICATE_CALLBACK
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_CLEANUP_DEFERRED
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_LOOP_COMPLETE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_LOOP_COMPLETE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_PING_PONG_LOOP_COMPLETE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_HELLO_SESSION_LOOP_COMPLETE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_LOOP_COMPLETE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_LOOP_COMPLETE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_REARM_SUBMIT_FAILED
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_REARM_INVALID_STATE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_EXCHANGE_COUNTER_OVERFLOW
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_FATAL_ERROR
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_HOST_ID_TIMEOUT
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_BEACON_COMPLETE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_FAILED
#endif
    ) {
        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SENT_DATAGRAM) {
            runtime_transport_polls_after_send = runtime_poll_counter;
        } else if (
            runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_LOOP_COMPLETE
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_LOOP_COMPLETE
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_PING_PONG_LOOP_COMPLETE
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_HELLO_SESSION_LOOP_COMPLETE
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_LOOP_COMPLETE
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_LOOP_COMPLETE
        ) {
            runtime_transport_polls_after_loop_complete = runtime_poll_counter;
        }
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

    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_INITIAL_DELAY) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        if (runtime_transport_is_native_wc24_bootstrap_mode()) {
            runtime_native_set_stage(RUNTIME_NATIVE_STAGE_STARTUP_DELAY);
        }
#endif
        if (runtime_poll_counter >= runtime_network_diagnostics_block.initial_delay_polls) {
            runtime_set_phase(
                runtime_transport_is_native_wc24_bootstrap_mode()
                    ? RUNTIME_TRANSPORT_PHASE_NATIVE_BOOTSTRAP
                    : RUNTIME_TRANSPORT_PHASE_OPEN_IP,
                RUNTIME_TRANSPORT_POLL_ACTION_INIT
            );
        } else {
            runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_WAIT;
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_BOOTSTRAP) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        s32 nwc24_result;
        s32 bootstrap_result;
        runtime_native_set_stage(RUNTIME_NATIVE_STAGE_BOOTSTRAP_ENTERED);
        runtime_transport_open_ip_submit_count += 1;
        nwc24_result = runtime_call_retail_nwc24_open_lib();
        *(volatile s32*)runtime_transport_nwc24_output_buffer = nwc24_result;
        runtime_transport_nwc24_synchronous_result = nwc24_result;
        if (nwc24_result < 0) {
            runtime_native_record_fatal_error(RUNTIME_TRANSPORT_PHASE_NATIVE_BOOTSTRAP, nwc24_result);
            goto runtime_poll_exit;
        }
        bootstrap_result = runtime_call_retail_network_bootstrap();
        runtime_transport_startup_callback_result = bootstrap_result;
        if (bootstrap_result != 0) {
            runtime_native_record_fatal_error(RUNTIME_TRANSPORT_PHASE_NATIVE_BOOTSTRAP, bootstrap_result);
            goto runtime_poll_exit;
        }
        runtime_transport_ip_fd = runtime_read_retail_so_fd();
        if (runtime_transport_ip_fd < 0) {
            runtime_native_record_fatal_error(RUNTIME_TRANSPORT_PHASE_NATIVE_BOOTSTRAP, runtime_transport_ip_fd);
            goto runtime_poll_exit;
        }
        runtime_transport_kd_fd = -1;
        runtime_transport_kd_closed = 1;
        runtime_transport_service_started = 0;
        runtime_native_set_stage(RUNTIME_NATIVE_STAGE_BOOTSTRAP_RETURNED);
        runtime_native_next_host_id_poll = runtime_poll_counter;
        runtime_native_next_host_id_timebase = 0;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_OPEN_KD, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
#else
        s32 nwc24_result;
        s32 bootstrap_result;
        runtime_transport_open_ip_submit_count += 1;
        nwc24_result = runtime_call_retail_nwc24_open_lib();
        *(volatile s32*)runtime_transport_nwc24_output_buffer = nwc24_result;
        runtime_transport_nwc24_synchronous_result = nwc24_result;
        if (nwc24_result < 0) {
            runtime_record_init_error(nwc24_result);
            goto runtime_poll_exit;
        }
        bootstrap_result = runtime_call_retail_network_bootstrap();
        runtime_transport_startup_callback_result = bootstrap_result;
        if (bootstrap_result != 0) {
            runtime_record_init_error(bootstrap_result);
            goto runtime_poll_exit;
        }
        runtime_transport_ip_fd = runtime_read_retail_so_fd();
        if (runtime_transport_ip_fd < 0) {
            runtime_record_init_error(runtime_transport_ip_fd);
            goto runtime_poll_exit;
        }
        runtime_transport_kd_fd = -1;
        runtime_transport_kd_closed = 1;
        runtime_transport_service_started = 1;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_GETHOSTID, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
#endif
        goto runtime_poll_exit;
    }
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_HOST_ID) {
        runtime_native_set_stage(RUNTIME_NATIVE_STAGE_HOST_ID);
        if (
            runtime_poll_counter < runtime_native_next_host_id_poll
            || !runtime_native_deadline_reached(runtime_native_next_host_id_timebase)
        ) {
            runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_WAIT;
        } else if (runtime_transport_get_host_id_submit_count >= RUNTIME_NATIVE_HOST_ID_ATTEMPT_LIMIT) {
            runtime_transport_last_error_phase = RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_HOST_ID;
            runtime_transport_last_error = runtime_transport_get_host_id_callback_result;
            if (runtime_native_low_level_recovery_active == 0 && runtime_transport_ip_fd >= 0) {
                runtime_native_low_level_recovery_active = 1;
                runtime_transport_get_host_id_submit_count = 0;
                runtime_transport_get_host_id_callback_count = 0;
                runtime_transport_get_host_id_callback_exit_count = 0;
                runtime_transport_get_host_id_submit_generation = 0;
                runtime_transport_get_host_id_callback_generation = 0;
                runtime_transport_host_id_ready = 0;
                runtime_transport_service_started = 0;
                runtime_transport_kd_fd = runtime_transport_ip_fd;
                runtime_transport_ip_fd = -1;
                runtime_transport_kd_closed = 0;
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_KD, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
            } else {
                runtime_native_set_stage(RUNTIME_NATIVE_STAGE_TERMINAL_FAILURE);
                runtime_set_phase(
                    RUNTIME_TRANSPORT_PHASE_NATIVE_HOST_ID_TIMEOUT,
                    RUNTIME_TRANSPORT_POLL_ACTION_ERROR
                );
            }
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_GETHOSTID, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_CREATE_BEACON_SOCKET) {
        runtime_native_set_stage(RUNTIME_NATIVE_STAGE_SOCKET);
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CREATE_SOCKET, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON_INTERVAL) {
        if (
            runtime_poll_counter < runtime_native_next_beacon_poll
            || !runtime_native_deadline_reached(runtime_native_next_beacon_timebase)
        ) {
            runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_WAIT;
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_NATIVE_SUBMIT_BEACON, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        }
        goto runtime_poll_exit;
    }
#endif
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_TCP_SEND_OUTCOME_CLOSE) {
        if (runtime_poll_counter < runtime_transport_retry_deadline) {
            runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_WAIT;
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RESTART_REQUESTED) {
        runtime_transport_bound_flag = 0;
        if (runtime_transport_socket_fd >= 0) {
            runtime_set_phase(
                RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_FOR_RECOVERY,
                RUNTIME_TRANSPORT_POLL_ACTION_RETRY
            );
        } else {
            runtime_transport_retry_deadline = runtime_poll_counter;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_RETRY_DELAY, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SOCKET_LOST) {
        runtime_transport_bound_flag = 0;
        if (runtime_transport_socket_fd >= 0) {
            runtime_set_phase(
                RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_FOR_RECOVERY,
                RUNTIME_TRANSPORT_POLL_ACTION_RETRY
            );
        } else {
            runtime_transport_retry_deadline =
                runtime_poll_counter + runtime_network_diagnostics_block.retry_delay_polls;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_RETRY_DELAY, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RETRY_DELAY) {
        if (runtime_poll_counter < runtime_transport_retry_deadline) {
            runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_WAIT;
            goto runtime_poll_exit;
        }
        if (
            runtime_transport_kd_fd < 0
            && runtime_transport_kd_closed == 0
            && runtime_transport_ip_fd < 0
        ) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_OPEN_KD, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        } else if (runtime_transport_kd_fd >= 0 && runtime_transport_kd_closed == 0) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_NWC24_STARTUP, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        } else if (runtime_transport_ip_fd < 0) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_OPEN_IP, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        } else if (runtime_transport_service_started == 0) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SO_STARTUP, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        } else if (runtime_transport_host_id_ready == 0) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_GETHOSTID, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CREATE_SOCKET, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        }
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
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CONNECT_TCP
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_VERIFY_BOUND_ENDPOINT
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_SOCKET_FOR_RECOVERY
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_HEARTBEAT
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON
#endif
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE_TCP_ACK
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_ECHO_RECV
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_ALT1
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_HELLO
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_WAIT_RESPONSE
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_WAIT_DISPATCH_RESPONSE
    ) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
        u32 waiting_phase = runtime_transport_phase;
#endif
        s32 wait_result = (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE_TCP_ACK)
            ? runtime_consume_receive_completion()
            : runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_ECHO_RECV
            ? runtime_consume_tcp_echo_receive()
            : (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND
                || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST
                || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_ALT1
                || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_HELLO
                || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_WAIT_RESPONSE
                || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_WAIT_DISPATCH_RESPONSE
                || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_HEARTBEAT
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON)
#else
                )
#endif
            ? runtime_consume_send_completion()
            : runtime_wait_completion();
        if (wait_result != 0) {
            if (wait_result < 0) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                    if (
                        waiting_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP
                        && runtime_native_low_level_recovery_active == 0
                    ) {
                        runtime_native_continue_after_startup_warning(runtime_transport_last_ios_result);
                        goto runtime_poll_exit;
                    }
                    if (runtime_transport_phase != RUNTIME_TRANSPORT_PHASE_FAILED) {
                        runtime_native_record_fatal_error(waiting_phase, runtime_transport_last_ios_result);
                    }
                    goto runtime_poll_exit;
                }
#endif
                if (
                    runtime_transport_phase != RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE
                    && runtime_transport_phase != RUNTIME_TRANSPORT_PHASE_WAIT_SEND
                ) {
                    runtime_record_init_error(runtime_transport_last_ios_result);
                }
            }
            goto runtime_poll_exit;
        }

        if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_KD) {
            if (runtime_transport_last_ios_result < 0) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                    runtime_native_record_fatal_error(
                        RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_KD,
                        runtime_transport_last_ios_result
                    );
                    goto runtime_poll_exit;
                }
#endif
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
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            if (
                *(volatile s32*)runtime_transport_nwc24_output_buffer == -29
                && (
                    runtime_transport_uses_receive_mode()
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                    || runtime_transport_is_native_wc24_bootstrap_mode()
#endif
                )
            ) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_READY, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
                goto runtime_poll_exit;
            }
            if (
                *(volatile s32*)runtime_transport_nwc24_output_buffer < 0
                && *(volatile s32*)runtime_transport_nwc24_output_buffer != -15
            ) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                    runtime_native_record_fatal_error(
                        RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_STARTUP,
                        *(volatile s32*)runtime_transport_nwc24_output_buffer
                    );
                    goto runtime_poll_exit;
                }
#endif
                runtime_record_init_error(*(volatile s32*)runtime_transport_nwc24_output_buffer);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_KD, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_KD) {
            if (runtime_transport_last_ios_result < 0) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                    runtime_native_record_fatal_error(
                        RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_KD,
                        runtime_transport_last_ios_result
                    );
                    goto runtime_poll_exit;
                }
#endif
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
            runtime_set_phase(
                (runtime_transport_uses_receive_mode()
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                    || (
                        runtime_transport_is_native_wc24_bootstrap_mode()
                        && runtime_native_low_level_recovery_active != 1
                    )
#endif
                )
                    ? RUNTIME_TRANSPORT_PHASE_SO_STARTUP
                    : RUNTIME_TRANSPORT_PHASE_OPEN_IP,
                RUNTIME_TRANSPORT_POLL_ACTION_INIT
            );
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_OPEN_IP) {
            if (runtime_transport_last_ios_result < 0) {
                runtime_record_init_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_ip_fd = runtime_transport_last_ios_result;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_native_low_level_recovery_active = 2;
            }
#endif
            if (runtime_transport_is_open_ip_once_mode() || runtime_transport_is_nwc24_close_open_ip_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_DIAGNOSTIC_COMPLETE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(
                (runtime_transport_uses_receive_mode()
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                    || runtime_transport_is_native_wc24_bootstrap_mode()
#endif
                )
                    ? RUNTIME_TRANSPORT_PHASE_OPEN_KD
                    : RUNTIME_TRANSPORT_PHASE_SO_STARTUP,
                RUNTIME_TRANSPORT_POLL_ACTION_INIT
            );
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP) {
            if (runtime_transport_last_ios_result < 0) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                    if (runtime_native_low_level_recovery_active == 0) {
                        runtime_native_continue_after_startup_warning(runtime_transport_last_ios_result);
                    } else {
                        runtime_native_record_fatal_error(
                            RUNTIME_TRANSPORT_PHASE_WAIT_SO_STARTUP,
                            runtime_transport_last_ios_result
                        );
                    }
                    goto runtime_poll_exit;
                }
#endif
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
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_native_set_stage(RUNTIME_NATIVE_STAGE_HOST_ID);
                runtime_native_next_host_id_poll = runtime_poll_counter;
                runtime_native_next_host_id_timebase = 0;
                runtime_set_phase(
                    RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_HOST_ID,
                    RUNTIME_TRANSPORT_POLL_ACTION_WAIT
                );
                goto runtime_poll_exit;
            }
#endif
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_GETHOSTID, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_GETHOSTID) {
            runtime_transport_get_host_id_service_started_after_completion = runtime_transport_service_started;
            runtime_transport_ip_fd_after_get_host_id = runtime_transport_ip_fd;
            runtime_transport_get_host_id_pending_after_completion = runtime_transport_pending_operation;
            runtime_transport_get_host_id_phase_after_completion = runtime_transport_phase;
            runtime_transport_host_id = 0;
            runtime_transport_host_id_available = 0;
            runtime_transport_host_id_ready = 0;
            if (!runtime_host_id_is_ready(runtime_transport_last_ios_result)) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                    runtime_native_next_host_id_poll =
                        runtime_poll_counter + RUNTIME_NATIVE_HOST_ID_RETRY_POLL_INTERVAL;
                    runtime_native_next_host_id_timebase =
                        runtime_native_read_timebase() + RUNTIME_NATIVE_INTERVAL_TIMEBASE_TICKS;
                    runtime_set_phase(
                        RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_HOST_ID,
                        RUNTIME_TRANSPORT_POLL_ACTION_WAIT
                    );
                    goto runtime_poll_exit;
                }
#endif
                if (runtime_transport_uses_receive_mode()) {
                    if (runtime_transport_last_ios_result < 0) {
                        runtime_transport_last_socket_error = runtime_transport_last_ios_result;
                        runtime_transport_last_error = runtime_transport_last_ios_result;
                    }
                    runtime_set_phase(
                        RUNTIME_TRANSPORT_PHASE_WAIT_NETWORK_READY,
                        RUNTIME_TRANSPORT_POLL_ACTION_RETRY
                    );
                    goto runtime_poll_exit;
                }
                runtime_record_socket_error(runtime_transport_last_ios_result);
                goto runtime_poll_exit;
            }
            runtime_transport_host_id = (u32)runtime_transport_last_ios_result;
            runtime_transport_host_id_available = 1;
            runtime_transport_host_id_ready = 1;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_native_first_valid_host_id_poll = runtime_poll_counter;
                runtime_native_set_stage(RUNTIME_NATIVE_STAGE_SOCKET);
                runtime_set_phase(
                    RUNTIME_TRANSPORT_PHASE_NATIVE_CREATE_BEACON_SOCKET,
                    RUNTIME_TRANSPORT_POLL_ACTION_INIT
                );
                goto runtime_poll_exit;
            }
#endif
            if (
                runtime_transport_is_create_socket_once_mode()
                || runtime_transport_is_bind_once_mode()
                || runtime_transport_is_native_wc24_bootstrap_mode()
                || runtime_transport_uses_receive_mode()
            ) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CREATE_SOCKET, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
            } else {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_HOST_ID_READY, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
            }
            goto runtime_poll_exit;
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET) {
            runtime_transport_socket_fd_after_completion = runtime_transport_socket_fd;
            runtime_transport_socket_descriptor_valid = 0;
            runtime_transport_socket_ready = 0;
            if (runtime_transport_last_ios_result < 0) {
                runtime_transport_socket_fd = -1;
                runtime_transport_socket_fd_after_completion = runtime_transport_socket_fd;
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                    runtime_native_record_fatal_error(
                        RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET,
                        runtime_transport_last_ios_result
                    );
                } else
#endif
                {
                    runtime_record_socket_error(runtime_transport_last_ios_result);
                }
                goto runtime_poll_exit;
            }
            runtime_transport_socket_fd = runtime_transport_last_ios_result;
            runtime_transport_socket_fd_after_completion = runtime_transport_socket_fd;
            runtime_transport_socket_descriptor_valid = 1;
            runtime_transport_socket_ready = 1;
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_memzero(runtime_transport_receive_source_bytes, sizeof(runtime_transport_receive_source_bytes));
                runtime_copy_sockaddr_in(
                    runtime_transport_receive_source_bytes,
                    runtime_native_beacon_ipv4,
                    (u16)PRIME3_NATIVE_BEACON_PORT
                );
                runtime_transport_last_peer_length = RUNTIME_WII_SOCKADDR_IN_SIZE;
                runtime_transport_last_peer_family = AF_INET;
                runtime_transport_last_peer_ipv4 = runtime_native_beacon_ipv4;
                runtime_transport_last_peer_port = PRIME3_NATIVE_BEACON_PORT;
                runtime_prepare_heartbeat();
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
                runtime_native_next_beacon_poll = runtime_poll_counter;
                runtime_native_next_beacon_timebase = 0;
                runtime_set_phase(
                    RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON_INTERVAL,
                    RUNTIME_TRANSPORT_POLL_ACTION_WAIT
                );
#else
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SUBMIT_HEARTBEAT, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
#endif
                goto runtime_poll_exit;
            }
            if (runtime_transport_is_create_socket_once_mode()) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SOCKET_READY, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
                goto runtime_poll_exit;
            }
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_BIND_SOCKET, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
            goto runtime_poll_exit;
        } else if (
            runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_BIND_SOCKET
            || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CONNECT_TCP
        ) {
            runtime_tcp_connect_phase_before = runtime_transport_phase;
            runtime_tcp_connect_completion_result = runtime_transport_last_ios_result;
            if (runtime_transport_last_ios_result != 0) {
                runtime_transport_last_socket_error = runtime_transport_last_ios_result;
                runtime_transport_last_error_phase = RUNTIME_TRANSPORT_PHASE_WAIT_BIND_SOCKET;
                runtime_transport_socket_closed_after_bind_failure = 0;
                runtime_transport_socket_leak_detected = 0;
                runtime_set_phase(
                    RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE,
                    RUNTIME_TRANSPORT_POLL_ACTION_ERROR
                );
                goto runtime_poll_exit;
            }
            runtime_transport_bound_flag = 1;
            runtime_tcp_send_outcome_close_pending = 0;
            runtime_tcp_send_offset = 0;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CONNECTED, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
            runtime_tcp_connect_phase_after = runtime_transport_phase;
            goto runtime_poll_exit;
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_VERIFY_BOUND_ENDPOINT) {
            u32 endpoint_structurally_valid;
            runtime_transport_getsockname_result = runtime_transport_last_ios_result;
            endpoint_structurally_valid = runtime_transport_last_ios_result == 0
                && runtime_transport_getsockname_address[0] == RUNTIME_WII_SOCKADDR_IN_SIZE
                && runtime_transport_getsockname_address[1] == AF_INET;
            if (endpoint_structurally_valid != 0) {
                u32 actual_port = runtime_read_be16(runtime_transport_getsockname_address + 2);
                if (actual_port != 0) {
                    runtime_transport_actual_bound_port = actual_port;
                    runtime_transport_actual_bound_address = runtime_read_be32(runtime_transport_getsockname_address + 4);
                    if (actual_port != runtime_cp3c_config_block.server_port) {
                        runtime_schedule_retry(RUNTIME_TRANSPORT_PHASE_WAIT_VERIFY_BOUND_ENDPOINT, -1, 0);
                        goto runtime_poll_exit;
                    }
                    runtime_enter_listening_after_bind(1);
                    goto runtime_poll_exit;
                }
            }
            runtime_record_endpoint_verification_warning(
                runtime_transport_last_ios_result != 0 ? runtime_transport_last_ios_result : -1
            );
            runtime_enter_listening_after_bind(0);
            goto runtime_poll_exit;
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_SOCKET_AFTER_BIND_FAILURE) {
            if (runtime_transport_last_ios_result != 0) {
                runtime_transport_socket_leak_detected = 1;
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FAILED_SOCKET_LEAK, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
                goto runtime_poll_exit;
            }
            runtime_transport_socket_fd = -1;
            runtime_transport_socket_fd_after_completion = -1;
            runtime_transport_socket_ready = 0;
            runtime_transport_socket_descriptor_valid = 0;
            runtime_transport_socket_closed_after_bind_failure = 1;
            runtime_transport_socket_leak_detected = 0;
            if (runtime_tcp_send_outcome_close_pending != 0) {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FAILED, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
                goto runtime_poll_exit;
            }
            if (runtime_transport_uses_receive_mode()) {
                runtime_transport_cleanup_count += 1;
                runtime_transport_retry_deadline =
                    runtime_poll_counter + runtime_network_diagnostics_block.retry_delay_polls;
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_RETRY_DELAY, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
            } else {
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_BIND_FAILED_CLEANED, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
            }
            goto runtime_poll_exit;
        } else if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_SOCKET_FOR_RECOVERY) {
            if (runtime_transport_last_ios_result != 0) {
                runtime_transport_last_socket_error = runtime_transport_last_ios_result;
                runtime_transport_last_error_phase = RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_SOCKET_FOR_RECOVERY;
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FATAL_ERROR, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
                goto runtime_poll_exit;
            }
            runtime_transport_cleanup_count += 1;
            runtime_transport_socket_fd = -1;
            runtime_transport_socket_ready = 0;
            runtime_transport_socket_descriptor_valid = 0;
            runtime_transport_bound_flag = 0;
            runtime_transport_retry_deadline =
                runtime_poll_counter + runtime_network_diagnostics_block.retry_delay_polls;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_RETRY_DELAY, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
            goto runtime_poll_exit;
        }
    }

    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_NETWORK_READY) {
        if ((runtime_poll_counter % RUNTIME_NETWORK_READY_RETRY_POLL_INTERVAL) == 0) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_GETHOSTID, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_WAIT_NETWORK_READY, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_READY) {
        if ((runtime_poll_counter % RUNTIME_NWC24_RETRY_POLL_INTERVAL) == 0) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_NWC24_STARTUP, RUNTIME_TRANSPORT_POLL_ACTION_RETRY);
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_WAIT_NWC24_READY, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        }
        goto runtime_poll_exit;
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
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_native_record_fatal_error(
                    RUNTIME_TRANSPORT_PHASE_OPEN_KD,
                    runtime_transport_last_submit_result
                );
            } else
#endif
            {
            runtime_record_init_error(runtime_transport_last_submit_result);
            }
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
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_native_record_fatal_error(
                    RUNTIME_TRANSPORT_PHASE_NWC24_STARTUP,
                    runtime_transport_last_submit_result
                );
            } else
#endif
            {
            runtime_record_init_error(runtime_transport_last_submit_result);
            }
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CLOSE_KD) {
        runtime_transport_kd_close_submit_count += 1;
        runtime_transport_close_call_count += 1;
        runtime_network_diagnostics_block.network_device_close_count += 1;
        runtime_transport_last_close_descriptor = runtime_transport_kd_fd;
        if (
            runtime_submit_close(
                runtime_transport_kd_fd,
                RUNTIME_TRANSPORT_OP_CLOSE_KD,
                RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_KD
            ) < 0
        ) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_native_record_fatal_error(
                    RUNTIME_TRANSPORT_PHASE_CLOSE_KD,
                    runtime_transport_last_submit_result
                );
            } else
#endif
            {
            runtime_record_init_error(runtime_transport_last_submit_result);
            }
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
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_native_record_fatal_error(
                    RUNTIME_TRANSPORT_PHASE_SO_STARTUP,
                    runtime_transport_last_submit_result
                );
            } else
#endif
            {
            runtime_record_socket_error(runtime_transport_last_submit_result);
            }
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
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_native_record_fatal_error(
                    RUNTIME_TRANSPORT_PHASE_GETHOSTID,
                    runtime_transport_last_submit_result
                );
            } else
#endif
            {
                runtime_record_socket_error(runtime_transport_last_submit_result);
            }
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CREATE_SOCKET) {
        runtime_transport_socket_request.family = AF_INET;
        runtime_transport_socket_request.type = SOCK_STREAM;
        runtime_transport_socket_request.protocol = IPPROTO_IP;
        runtime_transport_socket_submit_count += 1;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_SOCKET,
                &runtime_transport_socket_request,
                RUNTIME_SOCKET_REQUEST_LOGICAL_SIZE,
                0,
                0,
                RUNTIME_TRANSPORT_OP_CREATE_SOCKET,
                RUNTIME_TRANSPORT_PHASE_WAIT_CREATE_SOCKET
            ) < 0
        ) {
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
            if (runtime_transport_is_native_wc24_bootstrap_mode()) {
                runtime_native_record_fatal_error(
                    RUNTIME_TRANSPORT_PHASE_CREATE_SOCKET,
                    runtime_transport_last_submit_result
                );
            } else
#endif
            {
                runtime_record_socket_error(runtime_transport_last_submit_result);
            }
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_BIND_SOCKET) {
        runtime_memzero(&runtime_transport_bind_params, sizeof(runtime_transport_bind_params));
        runtime_transport_bind_params.socket = (u32)runtime_transport_socket_fd;
        runtime_transport_bind_params.has_addr = 1;
        runtime_copy_sockaddr_in(
            runtime_transport_bind_params.address,
            runtime_cp3c_config_block.server_ipv4,
            runtime_cp3c_config_block.server_port
        );
        runtime_transport_bind_submit_count += 1;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_CONNECT,
                &runtime_transport_bind_params,
                32,
                0,
                0,
                RUNTIME_TRANSPORT_OP_BIND_SOCKET,
                RUNTIME_TRANSPORT_PHASE_WAIT_CONNECT_TCP
            ) < 0
        ) {
            runtime_transport_socket_closed_after_bind_failure = 0;
            runtime_transport_socket_leak_detected = 0;
            runtime_set_phase(
                RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE,
                RUNTIME_TRANSPORT_POLL_ACTION_ERROR
            );
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CONNECTED) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_QUEUE_CLIENT_HELLO, RUNTIME_TRANSPORT_POLL_ACTION_INIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_QUEUE_CLIENT_HELLO
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_QUEUE_CLIENT_TEST
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_PREPARE_TRACKER_SNAPSHOT
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_PREPARE_FRAME) {
        u32 message_type = runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_QUEUE_CLIENT_HELLO
            ? RUNTIME_PROTOCOL_CLIENT_HELLO
            : runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_QUEUE_CLIENT_TEST
            ? RUNTIME_PROTOCOL_CLIENT_TEST
            : runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_PREPARE_TRACKER_SNAPSHOT
            ? RUNTIME_PROTOCOL_TRACKER_SNAPSHOT
            : RUNTIME_PROTOCOL_CP3D_DIAGNOSTIC_REQUEST;
        runtime_protocol_prepare_frame(message_type, runtime_transport_send_payload_bytes);
        if (runtime_protocol_enqueue_outbound(message_type, runtime_transport_send_payload_bytes) != 0) {
            runtime_protocol_fail(runtime_transport_phase);
            goto runtime_poll_exit;
        }
        runtime_protocol_expected_type = message_type == RUNTIME_PROTOCOL_CLIENT_HELLO
            ? RUNTIME_PROTOCOL_SERVER_HELLO_ACK
            : message_type == RUNTIME_PROTOCOL_CLIENT_TEST
            ? RUNTIME_PROTOCOL_SERVER_TEST
            : message_type == RUNTIME_PROTOCOL_TRACKER_SNAPSHOT
            ? RUNTIME_PROTOCOL_TRACKER_ACK
            : RUNTIME_PROTOCOL_CP3D_DIAGNOSTIC_ECHO;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SEND_QUEUED_FRAME, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_QUEUED_FRAME) {
        volatile runtime_protocol_queue_slot* slot = 0;
        if (runtime_protocol_outbound_count == 0) {
            runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_SEND_QUEUED_FRAME);
            goto runtime_poll_exit;
        }
        slot = &runtime_protocol_outbound_queue[runtime_protocol_outbound_head];
        if (slot->occupied == 0) {
            runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_SEND_QUEUED_FRAME);
            goto runtime_poll_exit;
        }
        runtime_memcpy(runtime_transport_send_payload_bytes, slot->frame, RUNTIME_TCP_FRAME_SIZE);
        runtime_memzero(&runtime_transport_send_request, sizeof(runtime_transport_send_request));
        runtime_transport_send_request.socket = (u32)runtime_transport_socket_fd;
        runtime_memzero(runtime_transport_send_vectors, sizeof(runtime_transport_send_vectors));
        runtime_transport_send_vectors[0].data = (void*)runtime_transport_send_payload_bytes;
        runtime_transport_send_vectors[0].len = RUNTIME_TCP_FRAME_SIZE;
        runtime_transport_send_vectors[1].data = (void*)&runtime_transport_send_request;
        runtime_transport_send_vectors[1].len = 40;
        runtime_tcp_send_offset = 0;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SEND_FRAME_SYNC, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_FRAME_SYNC) {
        u32 synchronous_call_count = 0;
        while (runtime_tcp_send_offset < RUNTIME_TCP_FRAME_SIZE && synchronous_call_count < 16) {
            u32 remaining = RUNTIME_TCP_FRAME_SIZE - runtime_tcp_send_offset;
            runtime_transport_send_vectors[0].data = (void*)(runtime_transport_send_payload_bytes + runtime_tcp_send_offset);
            runtime_transport_send_vectors[0].len = remaining;
            runtime_cache_flush(runtime_transport_send_payload_bytes + runtime_tcp_send_offset, remaining);
            runtime_cache_flush(&runtime_transport_send_request, 40);
            runtime_cache_flush(runtime_transport_send_vectors, sizeof(runtime_transport_send_vectors));
            runtime_tcp_sync_wrapper_entries += 1;
            runtime_tcp_counter_calls += 1;
            runtime_tcp_sync_pre_poll = runtime_poll_counter;
            runtime_tcp_sync_result = runtime_call_retail_ios_ioctlv_sync(
                runtime_transport_ip_fd, IOCTLV_SO_SENDTO, 2, 0, (runtime_ioctlv*)runtime_transport_send_vectors
            );
            runtime_tcp_sync_post_poll = runtime_poll_counter;
            synchronous_call_count += 1;
            if (runtime_tcp_sync_result <= 0 || (u32)runtime_tcp_sync_result > remaining) {
                runtime_tcp_send_outcome_close_pending = 1;
                runtime_set_phase(
                    RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE,
                    RUNTIME_TRANSPORT_POLL_ACTION_ERROR
                );
                goto runtime_poll_exit;
            }
            runtime_tcp_counter_bytes += (u32)runtime_tcp_sync_result;
            runtime_tcp_send_offset += (u32)runtime_tcp_sync_result;
            if ((u32)runtime_tcp_sync_result < remaining) {
                runtime_tcp_counter_partials += 1;
            }
        }
        if (runtime_tcp_send_offset == RUNTIME_TCP_FRAME_SIZE) {
            volatile runtime_protocol_queue_slot* slot = &runtime_protocol_outbound_queue[runtime_protocol_outbound_head];
            runtime_protocol_last_sent_type = slot->message_type;
            runtime_protocol_last_client_acknowledged = slot->sequence;
            runtime_protocol_frames_sent += 1;
            if (slot->message_type == RUNTIME_PROTOCOL_CLIENT_TEST) {
                runtime_protocol_client_test_sent_count += 1;
            }
            slot->occupied = 0;
            runtime_protocol_outbound_head = (runtime_protocol_outbound_head + 1) % RUNTIME_PROTOCOL_QUEUE_DEPTH;
            runtime_protocol_outbound_count -= 1;
            runtime_protocol_client_tx_sequence += 1;
            runtime_tcp_counter_sent += 1;
            runtime_tcp_echo_receive_offset = 0;
            runtime_set_phase(
                runtime_protocol_last_sent_type == RUNTIME_PROTOCOL_CLIENT_HELLO
                    ? RUNTIME_TRANSPORT_PHASE_WAIT_SERVER_HELLO_ACK
                    : runtime_protocol_last_sent_type == RUNTIME_PROTOCOL_CLIENT_TEST
                    ? RUNTIME_TRANSPORT_PHASE_WAIT_SERVER_TEST
                    : runtime_protocol_last_sent_type == RUNTIME_PROTOCOL_TRACKER_SNAPSHOT
                    ? RUNTIME_TRANSPORT_PHASE_WAIT_TRACKER_ACK
                    : RUNTIME_TRANSPORT_PHASE_RECEIVE_FRAME,
                RUNTIME_TRANSPORT_POLL_ACTION_RECV
            );
        } else {
            runtime_tcp_send_outcome_close_pending = 1;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_INTERVAL) {
        if (runtime_poll_counter >= runtime_transport_retry_deadline) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_PREPARE_FRAME, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVE_FRAME) {
        if (runtime_submit_tcp_echo_receive(RUNTIME_TRANSPORT_PHASE_WAIT_ECHO_RECV) != 0) {
            runtime_tcp_echo_receive_error_count += 1;
            runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_RECEIVE_FRAME);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SERVER_HELLO_ACK
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_SERVER_TEST
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_WAIT_TRACKER_ACK) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_RECEIVE_FRAME, RUNTIME_TRANSPORT_POLL_ACTION_RECV);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SUBMIT_ECHO_RECV) {
        if (runtime_submit_tcp_echo_receive(RUNTIME_TRANSPORT_PHASE_WAIT_ECHO_RECV) != 0) {
            runtime_tcp_echo_receive_error_count += 1;
            runtime_tcp_echo_last_failure_phase = RUNTIME_TRANSPORT_PHASE_SUBMIT_ECHO_RECV;
            runtime_tcp_send_outcome_close_pending = 1;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_VALIDATE_FRAME) {
        u32 payload_length = 0;
        u32 sequence = 0;
        u32 acknowledgement = 0;
        runtime_tcp_echo_received_magic = runtime_read_be32(runtime_transport_receive_payload_buffer + 0);
        runtime_tcp_echo_received_type = runtime_transport_receive_payload_buffer[5];
        runtime_tcp_echo_received_length = runtime_read_be16(runtime_transport_receive_payload_buffer + 6);
        sequence = runtime_read_be32(runtime_transport_receive_payload_buffer + 8);
        acknowledgement = runtime_read_be32(runtime_transport_receive_payload_buffer + 12);
        payload_length = runtime_read_be32(runtime_transport_receive_payload_buffer + 16);
        runtime_tcp_echo_received = sequence;
        runtime_tcp_echo_expected_crc = runtime_crc32(runtime_transport_receive_payload_buffer, RUNTIME_TCP_FRAME_CRC_OFFSET);
        runtime_tcp_echo_received_crc = runtime_read_be32(
            runtime_transport_receive_payload_buffer + RUNTIME_TCP_FRAME_CRC_OFFSET
        );
        if (
            runtime_tcp_echo_received_magic != RUNTIME_PROTOCOL_MAGIC
            || runtime_transport_receive_payload_buffer[4] != 1
            || runtime_tcp_echo_received_length != RUNTIME_TCP_FRAME_SIZE
            || payload_length > 36
            || runtime_tcp_echo_received_crc != runtime_tcp_echo_expected_crc
        ) {
            runtime_protocol_crc_failure_count += 1;
            runtime_tcp_echo_mismatch_count += 1;
            runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_VALIDATE_FRAME);
            goto runtime_poll_exit;
        }
        if (sequence != runtime_protocol_server_rx_sequence + 1) {
            runtime_protocol_sequence_failure_count += 1;
            runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_VALIDATE_FRAME);
            goto runtime_poll_exit;
        }
        if (runtime_tcp_echo_received_type != runtime_protocol_expected_type) {
            runtime_protocol_handshake_failure_count += 1;
            runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_VALIDATE_FRAME);
            goto runtime_poll_exit;
        }
        if (runtime_protocol_enqueue_inbound(runtime_tcp_echo_received_type, sequence) != 0) {
            runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_VALIDATE_FRAME);
            goto runtime_poll_exit;
        }
        runtime_protocol_frames_received += 1;
        runtime_protocol_last_received_type = runtime_tcp_echo_received_type;
        runtime_protocol_server_rx_sequence = sequence;
        if (runtime_tcp_echo_received_type == RUNTIME_PROTOCOL_SERVER_HELLO_ACK) {
            if (
                acknowledgement != runtime_protocol_last_client_acknowledged
                || payload_length != 36
                || runtime_read_be32(runtime_transport_receive_payload_buffer + 24) != runtime_protocol_client_nonce
                || runtime_read_be32(runtime_transport_receive_payload_buffer + 32) != 0
                || runtime_read_be32(runtime_transport_receive_payload_buffer + 44) != RUNTIME_PROTOCOL_VERSION
            ) {
                runtime_protocol_handshake_failure_count += 1;
                runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_WAIT_SERVER_HELLO_ACK);
                goto runtime_poll_exit;
            }
            runtime_protocol_server_nonce = runtime_read_be32(runtime_transport_receive_payload_buffer + 28);
            runtime_protocol_inbound_queue[runtime_protocol_inbound_head].occupied = 0;
            runtime_protocol_inbound_head = (runtime_protocol_inbound_head + 1) % RUNTIME_PROTOCOL_QUEUE_DEPTH;
            runtime_protocol_inbound_count -= 1;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_PREPARE_TRACKER_SNAPSHOT, RUNTIME_TRANSPORT_POLL_ACTION_SEND);
            goto runtime_poll_exit;
        }
        if (runtime_tcp_echo_received_type == RUNTIME_PROTOCOL_TRACKER_ACK) {
            if (acknowledgement != runtime_protocol_last_client_acknowledged) {
                runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_WAIT_TRACKER_ACK);
                goto runtime_poll_exit;
            }
            runtime_protocol_inbound_queue[runtime_protocol_inbound_head].occupied = 0;
            runtime_protocol_inbound_head = (runtime_protocol_inbound_head + 1) % RUNTIME_PROTOCOL_QUEUE_DEPTH;
            runtime_protocol_inbound_count -= 1;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_TRACKING, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
            goto runtime_poll_exit;
        }
        if (runtime_tcp_echo_received_type == RUNTIME_PROTOCOL_SERVER_TEST) {
            if (
                acknowledgement != runtime_protocol_last_client_acknowledged
                || payload_length != 36
                || runtime_read_be32(runtime_transport_receive_payload_buffer + 24) != 0x53545354
                || runtime_read_be32(runtime_transport_receive_payload_buffer + 28) != runtime_protocol_client_nonce
                || runtime_read_be32(runtime_transport_receive_payload_buffer + 32) != runtime_protocol_server_nonce
            ) {
                runtime_protocol_handshake_failure_count += 1;
                runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_WAIT_SERVER_TEST);
                goto runtime_poll_exit;
            }
            runtime_protocol_server_test_received_count += 1;
            runtime_protocol_inbound_queue[runtime_protocol_inbound_head].occupied = 0;
            runtime_protocol_inbound_head = (runtime_protocol_inbound_head + 1) % RUNTIME_PROTOCOL_QUEUE_DEPTH;
            runtime_protocol_inbound_count -= 1;
            runtime_transport_retry_deadline = runtime_poll_counter + 60;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_ESTABLISHED, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
            goto runtime_poll_exit;
        }
        if (runtime_tcp_echo_received_type == RUNTIME_PROTOCOL_CP3D_DIAGNOSTIC_ECHO) {
            runtime_tcp_echo_success_count += 1;
            runtime_tcp_echo_last_successful_sequence = sequence;
            runtime_protocol_inbound_queue[runtime_protocol_inbound_head].occupied = 0;
            runtime_protocol_inbound_head = (runtime_protocol_inbound_head + 1) % RUNTIME_PROTOCOL_QUEUE_DEPTH;
            runtime_protocol_inbound_count -= 1;
            runtime_transport_retry_deadline = runtime_poll_counter + 60;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_ESTABLISHED, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
            goto runtime_poll_exit;
        }
        runtime_protocol_fail(RUNTIME_TRANSPORT_PHASE_VALIDATE_FRAME);
        goto runtime_poll_exit;
#if 0
        runtime_tcp_echo_success_count += 1;
        runtime_tcp_echo_last_successful_sequence = runtime_tcp_echo_expected;
        runtime_tcp_counter_sequence += 1;
        runtime_transport_retry_deadline = runtime_poll_counter + 60;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_WAIT_INTERVAL, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
#endif
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_ESTABLISHED) {
#if ENABLE_TCP_DIAGNOSTICS
        if (runtime_poll_counter >= runtime_transport_retry_deadline) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_PREPARE_FRAME, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        }
#endif
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_TRACKING) {
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_DISCONNECTED) {
        runtime_tcp_send_outcome_close_pending = 1;
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_TEST) {
        runtime_transport_send_submit_count += 1;
        runtime_prepare_tcp_literal_test();
        if (runtime_submit_ioctlv_send(RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_TEST) != 0) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_SUBMIT_FAILED, runtime_transport_send_submit_result);
            runtime_tcp_send_outcome_close_pending = 1;
            runtime_transport_retry_deadline = runtime_poll_counter;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_TCP_LITERAL_ALT1) {
        runtime_transport_send_submit_count += 1;
        runtime_prepare_tcp_literal_alt1();
        if (runtime_submit_ioctlv_send(RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_LITERAL_ALT1) != 0) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_SUBMIT_FAILED, runtime_transport_send_submit_result);
            runtime_tcp_send_outcome_close_pending = 1;
            runtime_transport_retry_deadline = runtime_poll_counter;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SEND_TCP_HELLO) {
        runtime_tcp_send_hello_entered += 1;
        runtime_transport_send_submit_count += 1;
        if (runtime_tcp_send_offset == 0) {
            runtime_prepare_tcp_hello();
        }
        if (runtime_submit_ioctlv_send(RUNTIME_TRANSPORT_PHASE_WAIT_SEND_TCP_HELLO) != 0) {
            runtime_record_send_error(RUNTIME_TRANSPORT_PHASE_SEND_SUBMIT_FAILED, runtime_transport_send_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_RECEIVE_TCP_ACK) {
        runtime_transport_receive_arm_count += 1;
        runtime_transport_receive_submit_count += 1;
        if (runtime_submit_ioctlv_receive(RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE_TCP_ACK) != 0) {
            runtime_record_receive_error(RUNTIME_TRANSPORT_PHASE_RECEIVE_SUBMIT_FAILED, runtime_transport_receive_submit_result);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_VERIFY_BOUND_ENDPOINT) {
        runtime_transport_getsockname_request = (u32)runtime_transport_socket_fd;
        runtime_memzero(runtime_transport_getsockname_address, sizeof(runtime_transport_getsockname_address));
        runtime_transport_getsockname_address[0] = RUNTIME_WII_SOCKADDR_IN_SIZE;
        runtime_transport_getsockname_address[1] = AF_INET;
        runtime_transport_getsockname_submit_count += 1;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_GETSOCKNAME,
                &runtime_transport_getsockname_request,
                4,
                runtime_transport_getsockname_address,
                RUNTIME_WII_SOCKADDR_IN_SIZE,
                RUNTIME_TRANSPORT_OP_GETSOCKNAME,
                RUNTIME_TRANSPORT_PHASE_WAIT_VERIFY_BOUND_ENDPOINT
            ) < 0
        ) {
            runtime_transport_getsockname_result = runtime_transport_last_submit_result;
            runtime_record_endpoint_verification_warning(runtime_transport_last_submit_result);
            runtime_enter_listening_after_bind(0);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_AFTER_BIND_FAILURE) {
        runtime_transport_cleanup_close_request = runtime_transport_socket_fd;
        runtime_transport_cleanup_close_request_value = runtime_transport_cleanup_close_request;
        runtime_transport_socket_close_submit_count += 1;
        runtime_transport_close_call_count += 1;
        runtime_transport_last_close_descriptor = runtime_transport_socket_fd;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_CLOSE,
                &runtime_transport_cleanup_close_request,
                4,
                0,
                0,
                RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_AFTER_BIND_FAILURE,
                RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_SOCKET_AFTER_BIND_FAILURE
            ) < 0
        ) {
            runtime_transport_socket_leak_detected = 1;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FAILED_SOCKET_LEAK, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_FOR_RECOVERY) {
        runtime_transport_cleanup_close_request = runtime_transport_socket_fd;
        runtime_transport_cleanup_close_request_value = runtime_transport_cleanup_close_request;
        runtime_transport_socket_close_submit_count += 1;
        runtime_transport_close_call_count += 1;
        runtime_transport_last_close_descriptor = runtime_transport_socket_fd;
        if (
            runtime_submit_ioctl(
                runtime_transport_ip_fd,
                IOCTL_SO_CLOSE,
                &runtime_transport_cleanup_close_request,
                4,
                0,
                0,
                RUNTIME_TRANSPORT_OP_CLOSE_SOCKET_FOR_RECOVERY,
                RUNTIME_TRANSPORT_PHASE_WAIT_CLOSE_SOCKET_FOR_RECOVERY
            ) < 0
        ) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_FATAL_ERROR, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_LISTENING) {
        runtime_set_phase(
            runtime_transport_uses_receive_mode()
                ? RUNTIME_TRANSPORT_PHASE_SUBMIT_RECEIVE_ONCE
                : RUNTIME_TRANSPORT_PHASE_BOUND_NO_RECV,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        goto runtime_poll_exit;
    }
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_NATIVE_SUBMIT_BEACON) {
        s32 submit_result;
        runtime_native_set_stage(RUNTIME_NATIVE_STAGE_BEACON_SUBMIT);
        runtime_native_beacon_attempt_count += 1;
        runtime_transport_send_submit_count += 1;
        submit_result = runtime_submit_ioctlv_send(RUNTIME_TRANSPORT_PHASE_NATIVE_WAIT_BEACON);
        runtime_native_last_beacon_submit_result = runtime_transport_send_submit_result;
        if (submit_result != 0) {
            runtime_native_beacon_submission_failure_count += 1;
            runtime_transport_last_heartbeat_result = runtime_transport_send_submit_result;
            runtime_native_record_fatal_error(
                RUNTIME_TRANSPORT_PHASE_NATIVE_SUBMIT_BEACON,
                runtime_transport_send_submit_result
            );
        }
        goto runtime_poll_exit;
    }
#endif
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SUBMIT_HEARTBEAT) {
        runtime_transport_send_submit_count += 1;
        if (runtime_submit_ioctlv_send(RUNTIME_TRANSPORT_PHASE_WAIT_HEARTBEAT) != 0) {
            runtime_transport_last_heartbeat_result = runtime_transport_send_submit_result;
            runtime_record_send_error(
                RUNTIME_TRANSPORT_PHASE_SEND_SUBMIT_FAILED,
                runtime_transport_send_submit_result
            );
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_BOUND_NO_RECV) {
        if (runtime_transport_uses_receive_mode()) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_SUBMIT_RECEIVE_ONCE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        } else {
            runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SUBMIT_RECEIVE_ONCE) {
        runtime_transport_polls_before_receive = runtime_poll_counter;
        runtime_transport_receive_arm_count += 1;
        runtime_transport_receive_submit_count += 1;
        {
            s32 receive_submit = runtime_submit_ioctlv_receive(RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE);
            if (receive_submit < 0) {
                runtime_record_receive_error(
                    RUNTIME_TRANSPORT_PHASE_RECEIVE_SUBMIT_FAILED,
                    runtime_transport_receive_submit_result
                );
            } else if (receive_submit > 0) {
                runtime_record_receive_error(
                    RUNTIME_TRANSPORT_PHASE_RECEIVE_INVALID_POSITIVE,
                    runtime_transport_receive_submit_result
                );
            }
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE) {
        if (
            (!runtime_transport_is_recv_send_loop_mode() && !runtime_transport_is_cp3w_mode())
            || runtime_transport_pending_operation != RUNTIME_TRANSPORT_OP_NONE
            || (runtime_transport_is_recv_send_loop_mode()
                && (runtime_transport_send_count != runtime_transport_completed_exchange_count
                    || runtime_transport_completed_exchange_count >= runtime_transport_configured_exchange_limit))
            || (runtime_transport_is_cp3w_mode() && runtime_transport_exchange_limit_reached())
        ) {
            runtime_transport_rearm_submission_failure_count += 1;
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_INVALID_STATE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
            goto runtime_poll_exit;
        }
        runtime_transport_polls_before_receive = runtime_poll_counter;
        runtime_transport_receive_arm_count += 1;
        runtime_transport_receive_rearm_count += 1;
        runtime_transport_receive_submit_count += 1;
        {
            s32 receive_submit = runtime_submit_ioctlv_receive(RUNTIME_TRANSPORT_PHASE_WAIT_RECEIVE);
            if (receive_submit < 0) {
                runtime_transport_rearm_submission_failure_count += 1;
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_SUBMIT_FAILED, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
            } else if (receive_submit > 0) {
                runtime_transport_rearm_submission_failure_count += 1;
                runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_INVALID_STATE, RUNTIME_TRANSPORT_POLL_ACTION_ERROR);
            }
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SUBMIT_SEND_ONCE) {
        runtime_transport_polls_before_send = runtime_poll_counter;
        runtime_transport_send_submit_count += 1;
        runtime_transport_prepare_loop_reply();
        {
            s32 send_submit = runtime_submit_ioctlv_send(RUNTIME_TRANSPORT_PHASE_WAIT_SEND);
            if (send_submit < 0) {
                runtime_record_send_error(
                    RUNTIME_TRANSPORT_PHASE_SEND_SUBMIT_FAILED,
                    runtime_transport_send_submit_result
                );
            } else if (send_submit > 0) {
                runtime_record_send_error(
                    RUNTIME_TRANSPORT_PHASE_SEND_INVALID_POSITIVE,
                    runtime_transport_send_submit_result
                );
            }
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_VALIDATE_FRAME) {
        if (
            (runtime_transport_is_cp3w_frame_validation_mode() && runtime_transport_validate_cp3w_frame() == 0)
            || (runtime_transport_is_cp3w_ping_pong_mode() && runtime_transport_validate_cp3w_ping_pong_frame() == 0)
            || (runtime_transport_is_cp3w_hello_session_mode() && runtime_transport_validate_cp3w_ping_pong_frame() == 0)
            || (runtime_transport_is_cp3w_game_identity_mode()
                && runtime_transport_validate_cp3w_ping_pong_frame() == 0)
            || (runtime_transport_is_cp3w_inventory_mode()
                && runtime_transport_validate_cp3w_ping_pong_frame() == 0)
        ) {
            runtime_set_phase(
                runtime_transport_is_cp3w_ping_pong_mode()
                    || runtime_transport_is_cp3w_hello_session_mode()
                    || runtime_transport_is_cp3w_game_identity_mode()
                    || runtime_transport_is_cp3w_inventory_mode()
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_DISPATCH_REQUEST
                    : RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_VALID,
                RUNTIME_TRANSPORT_POLL_ACTION_WAIT
            );
        } else if (!runtime_transport_validate_loop_limit()) {
            runtime_record_receive_error(RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID, runtime_transport_last_ios_result);
        } else if (runtime_transport_exchange_limit_reached()) {
            if (runtime_transport_is_cp3w_ping_pong_mode()) {
                runtime_transport_note_cp3w_ping_pong_loop_complete();
            } else if (runtime_transport_is_cp3w_hello_session_mode()) {
                runtime_transport_note_cp3w_hello_session_loop_complete();
            } else if (runtime_transport_is_cp3w_game_identity_mode()) {
                runtime_transport_note_cp3w_game_identity_loop_complete();
            } else if (runtime_transport_is_cp3w_inventory_mode()) {
                runtime_transport_note_cp3w_inventory_loop_complete();
            } else {
                runtime_transport_note_cp3w_loop_complete();
            }
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_REJECTED, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_DISPATCH_REQUEST) {
        s32 dispatch_result = (runtime_transport_is_cp3w_game_identity_mode()
            || runtime_transport_is_cp3w_inventory_mode())
            ? runtime_transport_dispatch_cp3w_game_identity_request()
            : runtime_transport_is_cp3w_hello_session_mode()
            ? runtime_transport_dispatch_cp3w_hello_session_request()
            : runtime_transport_dispatch_cp3w_ping_pong_request();
        if (dispatch_result == 0) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_PING, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        } else if (
            (runtime_transport_is_cp3w_hello_session_mode() || runtime_transport_is_cp3w_game_identity_mode()
                || runtime_transport_is_cp3w_inventory_mode())
            && dispatch_result == 1
        ) {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_PING, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        } else if (dispatch_result > 0) {
            runtime_set_phase(
                dispatch_result == 2
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_HELLO_REJECTED
                    : dispatch_result == 3
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_HELLO_SUCCESS
                    : dispatch_result == 4
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_DUPLICATE_HELLO
                    : dispatch_result == 5
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_RENEGOTIATION_REJECTED
                    : dispatch_result == 6
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_NOT_NEGOTIATED
                    : dispatch_result == 10
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_BUILD_RESPONSE
                    : dispatch_result == 8 || dispatch_result == 9
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_HANDLE_ERROR
                    : dispatch_result == 14
                    ? RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE
                    : dispatch_result == 13
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_BUILD_RESPONSE
                    : dispatch_result == 11 || dispatch_result == 12
                    ? RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_HANDLE_ERROR
                    : RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_UNSUPPORTED_COMMAND,
                RUNTIME_TRANSPORT_POLL_ACTION_WAIT
            );
        } else if (!runtime_transport_validate_loop_limit()) {
            runtime_record_receive_error(RUNTIME_TRANSPORT_PHASE_LOOP_LIMIT_INVALID, runtime_transport_last_ios_result);
        } else if (runtime_transport_exchange_limit_reached()) {
            if (runtime_transport_is_cp3w_hello_session_mode()) {
                runtime_transport_note_cp3w_hello_session_loop_complete();
            } else if (runtime_transport_is_cp3w_game_identity_mode()) {
                runtime_transport_note_cp3w_game_identity_loop_complete();
            } else if (runtime_transport_is_cp3w_inventory_mode()) {
                runtime_transport_note_cp3w_inventory_loop_complete();
            } else {
                runtime_transport_note_cp3w_ping_pong_loop_complete();
            }
        } else {
            runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_REJECTED, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_VALID) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_PING) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_UNSUPPORTED_COMMAND) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_HELLO_SUCCESS) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_HELLO_REJECTED) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_DUPLICATE_HELLO) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_RENEGOTIATION_REJECTED) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_HANDLE_NOT_NEGOTIATED) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_BUILD_RESPONSE) {
        runtime_set_phase(
            RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_SUBMIT_RESPONSE,
            RUNTIME_TRANSPORT_POLL_ACTION_WAIT
        );
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_HANDLE_ERROR) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_GAME_IDENTITY_SUBMIT_RESPONSE) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_BUILD_RESPONSE) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_SUBMIT_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_HANDLE_ERROR) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_INVENTORY_SUBMIT_RESPONSE) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_FRAME_REJECTED) {
        runtime_set_phase(RUNTIME_TRANSPORT_PHASE_REARM_RECEIVE, RUNTIME_TRANSPORT_POLL_ACTION_WAIT);
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_RESPONSE) {
        runtime_transport_polls_before_send = runtime_poll_counter;
        runtime_transport_send_submit_count += 1;
        runtime_transport_cp3w_framed_responses_submitted += 1;
        {
            s32 send_submit = runtime_submit_ioctlv_send(RUNTIME_TRANSPORT_PHASE_CP3W_WAIT_RESPONSE);
            if (send_submit < 0) {
                runtime_record_send_error(
                    RUNTIME_TRANSPORT_PHASE_SEND_SUBMIT_FAILED,
                    runtime_transport_send_submit_result
                );
            } else if (send_submit > 0) {
                runtime_record_send_error(
                    RUNTIME_TRANSPORT_PHASE_SEND_INVALID_POSITIVE,
                    runtime_transport_send_submit_result
                );
            }
        }
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_CP3W_SUBMIT_DISPATCH_RESPONSE) {
        runtime_transport_polls_before_send = runtime_poll_counter;
        runtime_transport_send_submit_count += 1;
        if (runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_HELLO) {
            runtime_transport_cp3w_hello_responses_submitted += 1;
        } else if (
            runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY
            && runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK
        ) {
            runtime_transport_cp3w_game_identity_responses_submitted += 1;
        } else if (
            runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_GET_INVENTORY
            && runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK
        ) {
            runtime_transport_cp3w_inventory_responses_submitted += 1;
        } else if (
            runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY
            &&
            runtime_transport_cp3w_last_dispatch_result == RUNTIME_CP3W_ERROR_CODE_CAPABILITY_NOT_NEGOTIATED
        ) {
            runtime_transport_cp3w_game_identity_capability_errors_submitted += 1;
        } else if (
            runtime_transport_cp3w_last_command == RUNTIME_CP3W_COMMAND_GET_GAME_IDENTITY
            &&
            runtime_transport_cp3w_last_dispatch_result == RUNTIME_CP3W_ERROR_CODE_INVALID_PAYLOAD_LENGTH
        ) {
            runtime_transport_cp3w_game_identity_invalid_payload_errors_submitted += 1;
        } else if (runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_OK) {
            runtime_transport_cp3w_pong_responses_submitted += 1;
        } else if (runtime_transport_cp3w_last_dispatch_result == RUNTIME_CP3W_ERROR_CODE_NOT_NEGOTIATED) {
            runtime_transport_cp3w_not_negotiated_responses_submitted += 1;
        } else if (runtime_transport_cp3w_last_response_status == RUNTIME_CP3W_RESPONSE_STATUS_ERROR) {
            runtime_transport_cp3w_unsupported_responses_submitted += 1;
        }
        {
            s32 send_submit = runtime_submit_ioctlv_send(RUNTIME_TRANSPORT_PHASE_CP3W_WAIT_DISPATCH_RESPONSE);
            if (send_submit < 0) {
                runtime_record_send_error(
                    RUNTIME_TRANSPORT_PHASE_SEND_SUBMIT_FAILED,
                    runtime_transport_send_submit_result
                );
            } else if (send_submit > 0) {
                runtime_record_send_error(
                    RUNTIME_TRANSPORT_PHASE_SEND_INVALID_POSITIVE,
                    runtime_transport_send_submit_result
                );
            }
        }
        goto runtime_poll_exit;
    }
    if (
        runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_BIND_FAILED_CLEANED
        || runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_FAILED_SOCKET_LEAK
    ) {
        runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SO_STARTED) {
        runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_HOST_ID_READY) {
        runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
        goto runtime_poll_exit;
    }
    if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SOCKET_READY) {
        runtime_transport_last_poll_action = RUNTIME_TRANSPORT_POLL_ACTION_IDLE;
        goto runtime_poll_exit;
    }

runtime_poll_exit:
    runtime_sync_network_diagnostics();
#if PRIME3_IOS_UDP_DIAGNOSTIC_MODE == 23
    runtime_native_overlay_draw();
#endif
    runtime_last_transport_phase_after_step = runtime_transport_phase;
    if (state_machine_entered != 0) {
        runtime_diag_increment(&runtime_state_machine_exit_count);
    }
    return;
}
