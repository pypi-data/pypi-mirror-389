XCP CAN Master

A Python implementation of an XCP (Universal Measurement and Calibration Protocol) master over CAN/CAN FD using the python-can library.

Features

• Request/Response Engine: Handles CRO (Command Receive Object) to DTO (Data Transmit Object) RES/ERR communication

• Connection Management: CONNECT and GET_COMM_MODE_INFO commands to learn MAX_CTO/MAX_DTO parameters

• Calibration Operations: 

  • Write operations using SHORT_DOWNLOAD/DOWNLOAD + SET_MTA

  • Read operations using SHORT_UPLOAD/UPLOAD

• DAQ (Data Acquisition) Support:

  • DAQ list allocation and configuration

  • ODT (Object Descriptor Table) entry setup

  • DAQ list start/stop control

• Flexible Data Parsing: User-configurable DAQ registry for byte-aligned entry parsing

• Thread-Safe: Built-in locking for concurrent operations

• CAN FD Support: Automatic detection and switching to CAN FD when needed

Installation

1. Install required dependencies:
pip install python-can loguru



Basic Usage

import can
from xcp_can_master import XcpCanMaster

# Configure CAN bus
timing_fd = can.BitTimingFd(
    f_clock=80000000, 
    nom_brp=1, nom_tseg1=127, nom_tseg2=32, nom_sjw=32,
    data_brp=1, data_tseg1=27, data_tseg2=12, data_sjw=12
)

bus = can.interface.Bus(interface='vector', channel='0', fd=True, timing=timing_fd)

# Initialize XCP master
CRO_ID = 0x1BFFE600
DTO_ID = 0x1BFFE601

xcp = XcpCanMaster(
    bus, 
    cro_id=CRO_ID, 
    dto_id=DTO_ID, 
    extended=True, 
    is_fd=True, 
    default_timeout=1.0
)

try:
    # Connect to ECU
    xcp.connect(mode=0x00)
    xcp.get_comm_mode_info()
    
    # Read/write operations
    data = (123456).to_bytes(4, "little")
    xcp.write(0x00, 0x7001c000, data)
    
    rd = xcp.read(0x00, 0x7001c000, 4)
    print(f"Readback: {int.from_bytes(rd, 'little')}")
    
finally:
    xcp.stop()


API Reference

Core Methods

• connect(mode: int = 0x00, timeout: Optional[float] = None): Establish XCP connection

• disconnect(timeout: Optional[float] = None): Disconnect from ECU

• get_comm_mode_info(timeout: Optional[float] = None): Get communication parameters

• build_checksum(size: int, timeout: Optional[float] = None): Calculate checksum

Memory Access

• read(addr_ext: int, address: int, size: int, timeout: Optional[float] = None): Read memory

• write(addr_ext: int, address: int, data: bytes, timeout: Optional[float] = None): Write memory

• short_upload(), upload(), short_download(), download(): Low-level memory operations

DAQ Configuration

• free_daq(), alloc_daq(), alloc_odt(), alloc_odt_entry(): DAQ resource management

• set_daq_ptr(), write_daq(): Configure DAQ entries

• set_daq_list_mode(): Configure DAQ list behavior

• start_stop_daq_list(): Start/stop DAQ acquisition

• register_daq_entry(): Register DAQ entries for parsing

• on_daq(): Set callback for DAQ data

DAQ Example

# Setup DAQ measurement
xcp.free_daq()
xcp.alloc_daq(1)
xcp.alloc_odt(daq_list=0, odt_num=1)
xcp.alloc_odt_entry(daq_list=0, odt=0, entries=2)

# Configure measurement points
xcp.set_daq_ptr(daq_list=0, odt=0, entry=0)
xcp.write_daq(bit_offset=0, size=4, addr_ext=0x00, address=0x7001c000)

xcp.set_daq_ptr(daq_list=0, odt=0, entry=1)
xcp.write_daq(bit_offset=0, size=4, addr_ext=0x00, address=0x20000014)

# Register for parsing
xcp.register_daq_entry(odt_pid=0, entry_name="sigA", size=4, addr_ext=0x00, address=0x20000010)
xcp.register_daq_entry(odt_pid=0, entry_name="sigB", size=4, addr_ext=0x00, address=0x20000014)

# Set DAQ callback
def on_daq(odt_pid: int, values: Dict[str, int], raw: bytes):
    print(f"DAQ odt={odt_pid} values={values}")

xcp.on_daq(on_daq)

# Start acquisition
xcp.set_daq_list_mode(daq_list=0, event=0, prescaler=1, priority=0, mode=0x01)
xcp.start_stop_daq_list(daq_list=0, start=True)


Error Handling

The library raises RuntimeError with detailed XCP error information when commands fail. Error codes are mapped according to the XCP standard:
XCP_ERROR_INFO = {
    0x00: {"name": "ERR_CMD_SYNCH", "desc": "Command processor synchronization."},
    0x10: {"name": "ERR_CMD_BUSY", "desc": "Command was not executed."},
    # ... more error codes
}


Configuration

Constructor Parameters

• bus: Configured python-can Bus instance

• cro_id: Arbitration ID for sending CRO frames to ECU

• dto_id: Arbitration ID for receiving DTO frames from ECU  

• extended: True for 29-bit CAN IDs (default: True)

• is_fd: True to use CAN FD (default: False)

• default_timeout: Default timeout for commands in seconds (default: 0.5)

• byteorder: Byte order for multi-byte values - "little" or "big" (default: "little")

Supported XCP Commands

The library implements a comprehensive subset of XCP commands including:

• Standard commands (CONNECT, DISCONNECT, GET_STATUS, etc.)

• Calibration commands (DOWNLOAD, UPLOAD, MODIFY_BITS, etc.)

• DAQ/STIM commands (SET_DAQ_PTR, WRITE_DAQ, START_STOP_DAQ_LIST, etc.)

• Page switching commands (SET_CAL_PAGE, GET_CAL_PAGE, etc.)

Requirements

• Python 3.7+

• python-can 4.0+

• loguru (for logging)

• Appropriate CAN interface drivers

License

This code is provided as-is for educational and development purposes. Adapt to your specific hardware and protocol requirements.