#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
from typing import Callable, Dict, List, Optional, Tuple, Any

import can
from loguru import logger

# ----------------------------------------
# XCP constants (subset)
# ----------------------------------------

# PIDs
PID_RES = 0xFF
PID_ERR = 0xFE
PID_EV  = 0xFD

# Standard commands (Table 24)
CMD_CONNECT                = 0xFF
CMD_DISCONNECT             = 0xFE
CMD_GET_STATUS             = 0xFD
CMD_SYNCH                  = 0xFC
CMD_GET_COMM_MODE_INFO     = 0xFB
CMD_GET_ID                 = 0xFA
CMD_SET_REQUEST            = 0xF9
CMD_GET_SEED               = 0xF8
CMD_UNLOCK                 = 0xF7
CMD_SET_MTA                = 0xF6
CMD_UPLOAD                 = 0xF5
CMD_SHORT_UPLOAD           = 0xF4
CMD_BUILD_CHECKSUM         = 0xF3
CMD_TRANSPORT_LAYER_CMD    = 0xF2
CMD_USER_CMD               = 0xF1

# Calibration (Table 25)
CMD_DOWNLOAD               = 0xF0
CMD_DOWNLOAD_NEXT          = 0xEF
CMD_DOWNLOAD_MAX           = 0xEE
CMD_SHORT_DOWNLOAD         = 0xED
CMD_MODIFY_BITS            = 0xEC

# Page switching (Table 26)
CMD_SET_CAL_PAGE           = 0xEB
CMD_GET_CAL_PAGE           = 0xEA
CMD_GET_PAG_PROCESSOR_INFO = 0xE9
CMD_GET_SEGMENT_INFO       = 0xE8
CMD_GET_PAGE_INFO          = 0xE7
CMD_SET_SEGMENT_MODE       = 0xE6
CMD_GET_SEGMENT_MODE       = 0xE5
CMD_COPY_CAL_PAGE          = 0xE4

# DAQ/STIM basic (Table 27)
CMD_SET_DAQ_PTR            = 0xE2
CMD_WRITE_DAQ              = 0xE1
CMD_SET_DAQ_LIST_MODE      = 0xE0
CMD_GET_DAQ_LIST_MODE      = 0xDF
CMD_START_STOP_SYNCH       = 0xDE
CMD_START_STOP_DAQ_LIST    = 0xDD
CMD_GET_DAQ_CLOCK          = 0xDC
CMD_READ_DAQ               = 0xDB
CMD_GET_DAQ_PROCESSOR_INFO = 0xDA
CMD_GET_DAQ_RESOLUTION_INFO= 0xD9
CMD_GET_DAQ_EVENT_INFO     = 0xD7
CMD_WRITE_DAQ_MULTIPLE     = 0xC7
CMD_DTO_CTR_PROPERTIES     = 0xC5

# DAQ/STIM static (Table 28)
CMD_CLEAR_DAQ_LIST         = 0xE3
CMD_GET_DAQ_LIST_INFO      = 0xD8

# DAQ/STIM dynamic (Table 29)
CMD_FREE_DAQ               = 0xD6
CMD_ALLOC_DAQ              = 0xD5
CMD_ALLOC_ODT              = 0xD4
CMD_ALLOC_ODT_ENTRY        = 0xD3

# Programming (Table 30)
CMD_PROGRAM_START          = 0xD2
CMD_PROGRAM_CLEAR          = 0xD1
CMD_PROGRAM                = 0xD0
CMD_PROGRAM_RESET          = 0xCF
CMD_GET_PGM_PROCESSOR_INFO = 0xCE
CMD_GET_SECTOR_INFO        = 0xCD
CMD_PROGRAM_PREPARE        = 0xCC
CMD_PROGRAM_FORMAT         = 0xCB
CMD_PROGRAM_NEXT           = 0xCA
CMD_PROGRAM_MAX            = 0xC9
CMD_PROGRAM_VERIFY         = 0xC8

# Time synchronization (Table 31)
CMD_TIME_CORRELATION_PROPERTIES = 0xC6

# Command spaces (Table 32) multiplexed under 0xC0
CMD_SPACE_0xC0             = 0xC0
C0_SUB_GET_VERSION         = 0x00
C0_SUB_SET_DAQ_PACKED_MODE = 0x01
C0_SUB_GET_DAQ_PACKED_MODE = 0x02
C0_SUB_SW_DBG_OVER_XCP     = 0xFC
C0_SUB_MCD_1_POD_BS        = 0xFD

# Error codes (updated per table)
XCP_ERROR_INFO = {
    0x00: {"name": "ERR_CMD_SYNCH", "desc": "Command processor synchronization.", "severity": "S0"},
    0x10: {"name": "ERR_CMD_BUSY", "desc": "Command was not executed.", "severity": "S2"},
    0x11: {"name": "ERR_DAQ_ACTIVE", "desc": "DAQ is running.", "severity": "S2"},
    0x12: {"name": "ERR_PGM_ACTIVE", "desc": "PGM is running.", "severity": "S2"},
    0x20: {"name": "ERR_CMD_UNKNOWN", "desc": "Unknown command or optional not implemented.", "severity": "S2"},
    0x21: {"name": "ERR_CMD_SYNTAX", "desc": "Invalid command syntax.", "severity": "S2"},
    0x22: {"name": "ERR_OUT_OF_RANGE", "desc": "Parameter(s) out of range.", "severity": "S2"},
    0x23: {"name": "ERR_WRITE_PROTECTED", "desc": "Write protected.", "severity": "S2"},
    0x24: {"name": "ERR_ACCESS_DENIED", "desc": "Location not accessible.", "severity": "S2"},
    0x25: {"name": "ERR_ACCESS_LOCKED", "desc": "Seed & Key required.", "severity": "S2"},
    0x26: {"name": "ERR_PAGE_NOT_VALID", "desc": "Page not available.", "severity": "S2"},
    0x27: {"name": "ERR_MODE_NOT_VALID", "desc": "Mode not available.", "severity": "S2"},
    0x28: {"name": "ERR_SEGMENT_NOT_VALID", "desc": "Segment not valid.", "severity": "S2"},
    0x29: {"name": "ERR_SEQUENCE", "desc": "Sequence error.", "severity": "S2"},
    0x2A: {"name": "ERR_DAQ_CONFIG", "desc": "DAQ config not valid.", "severity": "S2"},
    0x30: {"name": "ERR_MEMORY_OVERFLOW", "desc": "Memory overflow.", "severity": "S2"},
    0x31: {"name": "ERR_GENERIC", "desc": "Generic error.", "severity": "S2"},
    0x32: {"name": "ERR_VERIFY", "desc": "Verify routine detected an error.", "severity": "S3"},
    0x33: {"name": "ERR_RESOURCE_TEMPORARY_NOT_ACCESSIBLE", "desc": "Resource temporarily not accessible.", "severity": "S2"},
    0x34: {"name": "ERR_SUBCMD_UNKNOWN", "desc": "Unknown sub command.", "severity": "S2"},
    0x35: {"name": "ERR_TIMECORR_STATE_CHANGE", "desc": "Sync status changed.", "severity": "S2"},
    0xFC: {"name": "ERR_DBG", "desc": "SW-DBG-over-XCP errors.", "severity": None},
}




class XcpCanMaster:
    """
    Minimal XCP master over CAN/CAN FD using python-can.

    Features:
    - Request/Response engine (CRO -> DTO RES/ERR)
    - CONNECT/GET_COMM_MODE_INFO to learn MAX_CTO/MAX_DTO
    - Calibration: write (SHORT_DOWNLOAD/DOWNLOAD + SET_MTA), read (SHORT_UPLOAD/UPLOAD)
    - DAQ: FREE/ALLOC, SET_DAQ_PTR/WRITE_DAQ, SET_DAQ_LIST_MODE, START/STOP
    - DAQ parsing using a user registry (byte-aligned entries)
    """

    def __init__(
        self,
        bus: can.BusABC,
        cro_id: int,
        dto_id: int,
        extended: bool = True,
        is_fd: bool = False,
        default_timeout: float = 0.5,
        byteorder:str = "little"
    ):
        """
        - bus: a configured python-can Bus
        - cro_id: arbitration ID to send CRO frames to ECU
        - dto_id: arbitration ID to receive DTO frames from ECU
        - extended: True if IDs are 29-bit
        - is_fd: True to use CAN FD for CTO/DTO (auto-updated after GET_COMM_MODE_INFO if larger MAX_CTO/MAX_DTO)
        - default_timeout: seconds to wait for RES/ERR
        """
        self.byteorder = byteorder
        self.bus = bus
        self.cro_id = cro_id
        self.dto_id = dto_id
        self.extended = extended
        self.is_fd = is_fd
        self.default_timeout = default_timeout

        # Learned from ECU
        self.max_cto: int = 8 if not is_fd else 64
        self.max_dto: int = 8 if not is_fd else 64
        self.protocol_version: Optional[int] = None
        self.transport_version: Optional[int] = None
        self.max_bs = 0
        self.min_st = 0
        self.queue_size = 0
        self.driver_version = ""

        # Request/response coordination
        self._lock = threading.Lock()
        self._resp_cond = threading.Condition(self._lock)
        self._pending: Optional[Dict[str, Any]] = None  # holds last response dict

        # DAQ registry and callback
        # map: odt_pid -> list of entries: [{"name":str, "size":int, "addr_ext":int, "addr":int}]
        self.daq_map: Dict[int, List[Dict[str, Any]]] = {}
        self.daq_callback: Optional[Callable[[int, Dict[str, int], bytes], None]] = None

        # Listener thread for DTO
        self._running = False
        self._rx_thread = threading.Thread(target=self._rx_loop, name="xcp-dto-listener", daemon=True)
        self.start()

    def u16(self, v: int) -> bytes:
        return v.to_bytes(2, self.byteorder)

    def u32(self, v: int) -> bytes:
        return v.to_bytes(4, self.byteorder)


    # ------------- Transport primitives -------------

    def start(self):
        self._running = True
        if not self._rx_thread.is_alive():
            self._rx_thread = threading.Thread(target=self._rx_loop, name="xcp-dto-listener", daemon=True)
            self._rx_thread.start()

    def stop(self):
        self._running = False
        # Wake up any waiters
        with self._lock:
            self._resp_cond.notify_all()

    def _send_cro(self, payload: bytes):
        # CTO must not exceed MAX_CTO (once known)
        if len(payload) > self.max_cto:
            logger.warning(f"CTO len {len(payload)} exceeds MAX_CTO {self.max_cto}; sending anyway")
        msg = can.Message(
            arbitration_id=self.cro_id,
            is_extended_id=self.extended,
            is_fd=self.is_fd,
            data=payload,
        )
        self.bus.send(msg)

    def _recv_blocking(self, timeout: float) -> Optional[can.Message]:
        return self.bus.recv(timeout=timeout)

    def _rx_loop(self):
        # Listen for DTO frames and handle them
        while self._running:
            try:
                msg = self._recv_blocking(timeout=0.1)
                if msg is None:
                    continue
                if msg.arbitration_id != self.dto_id:
                    continue
                data = bytes(msg.data)
                if not data:
                    continue
                pid = data[0]
                pl = data[1:]

                if pid == PID_RES or pid == PID_ERR or pid == PID_EV:
                    # Handle response/event
                    resp = {"pid": pid, "payload": pl}
                    with self._lock:
                        self._pending = resp
                        self._resp_cond.notify_all()
                else:
                    # DAQ/ODT packet
                    self._handle_daq(pid, pl)
            except Exception as e:
                logger.exception(f"DTO listener error: {e}")
                time.sleep(0.05)

    def _request(self, cmd: int, args: bytes = b"", timeout: Optional[float] = None) -> bytes:
        """
        Send a CRO and wait for RES or ERR. Returns payload after PID (i.e., DTO bytes after 0xFF).
        Raises RuntimeError on ERR/timeout.
        """
        if timeout is None:
            timeout = self.default_timeout

        payload = bytes([cmd]) + args

        # Serialize requests
        with self._lock:
            self._pending = None
        self._send_cro(payload)

        # Wait for DTO
        deadline = time.time() + timeout
        with self._lock:
            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise RuntimeError(f"Timeout waiting for RES to CMD 0x{cmd:02X}")
                if self._pending is None:
                    self._resp_cond.wait(timeout=remaining)
                    if self._pending is None:
                        continue
                resp = self._pending
                self._pending = None
                pid = resp["pid"]
                pl = resp["payload"]
                if pid == PID_RES:
                    return pl
                if pid == PID_ERR:
                    err = pl[0] if pl else 0xFF
                    info = XCP_ERROR_INFO.get(err, {"name": "UNKNOWN", "desc": "", "severity": ""})
                    raise RuntimeError(f"XCP ERR 0x{err:02X} {info['name']} (CMD 0x{cmd:02X})")
                if pid == PID_EV:
                    # Event: deliver to optional callback or ignore, then still wait for RES
                    logger.debug(f"XCP EV: {pl.hex(' ')}")
                    continue

    # ------------- Core commands -------------

    def connect(self, mode: int = 0x00, timeout: Optional[float] = None):
        """
        CONNECT. Returns dict with basic info if available (flex decode).
        """
        pl = self._request(CMD_CONNECT, bytes([mode]), timeout)
        info = {}
        # Flexible decode: resource, comm_mode, sizes, versions (if present)
        # Not all slaves provide all fields; be lenient.
        if len(pl) >= 1:
            info["resource"] = pl[0]
        if len(pl) >= 2:
            info["comm_mode"] = pl[1]
        # Sizes might be U16 or U8 depending on stack; try U16 if enough bytes.
        off = 2
        if len(pl) - off >= 4:
            self.max_cto = pl[off] 
            off += 1
            info["max_cto"] = self.max_cto
            self.max_dto = int.from_bytes(pl[off:off+2], self.byteorder)
            off += 2
            info["max_cto"] = self.max_cto
            info["max_dto"] = self.max_dto
        if len(pl) - off >= 1:
            self.protocol_version = pl[off]; off += 1
            info["protocol_version"] = self.protocol_version
        if len(pl) - off >= 1:
            self.transport_version = pl[off]; off += 1
            info["transport_version"] = self.transport_version

        # Switch to FD if sizes exceed 8
        if self.max_cto > 8 or self.max_dto > 8:
            self.is_fd = True
        logger.info(f"Connected: {info}")
        return info

    def disconnect(self, timeout: Optional[float] = None):
        self._request(CMD_DISCONNECT, b"", timeout)

    def get_comm_mode_info(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        pl = self._request(CMD_GET_COMM_MODE_INFO, b"", timeout)
        info = {}
        off = 1

        if len(pl) - off >= 1:
            info["comm_mode_optional"] = pl[off]; off += 2
        if len(pl) - off >= 1:
            self.max_bs = pl[off]; off += 1
            info["max_bs"] = self.max_bs
        if len(pl) - off >= 1:
            self.min_st = pl[off]; off += 1
            info["min_st"] = self.min_st
        if len(pl) - off >= 1:
            self.queue_size = pl[off]; off += 1
            info["queue_size"] = self.queue_size
        if len(pl) - off >= 1:
            self.driver_version = pl[off]; off += 1
            info["driver_version"] = self.driver_version
        if self.max_cto > 8 or self.max_dto > 8:
            self.is_fd = True
        return info

    # Add the build checksum command
    def build_checksum(self, size: int, timeout: Optional[float] = None) -> Tuple[int, int]:
        """
        BUILD_CHECKSUM. Returns a tuple with the checksum and the type.
        """
        args = self.u32(size)
        pl = self._request(CMD_BUILD_CHECKSUM, args, timeout)
        if len(pl) < 5:
            raise RuntimeError("Invalid response length for BUILD_CHECKSUM")
        checksum = int.from_bytes(pl[:4], self.byteorder)
        checksum_type = pl[4]
        return checksum, checksum_type

    # Existing code...

    # ------------- Memory access (Calibration) -------------

    def set_mta(self, addr_ext: int, address: int, timeout: Optional[float] = None):
        args = bytes([0, addr_ext]) + self.u32(address)
        self._request(CMD_SET_MTA, args, timeout)

    def short_upload(self, size: int, addr_ext: int, address: int, timeout: Optional[float] = None) -> bytes:
        args = bytes([size, 0, addr_ext]) + self.u32(address)
        pl = self._request(CMD_SHORT_UPLOAD, args, timeout)
        return pl[:size]

    def upload(self, size: int, timeout: Optional[float] = None) -> bytes:
        args = bytes([size])
        pl = self._request(CMD_UPLOAD, args, timeout)
        return pl[:size]

    def short_download(self, addr_ext: int, address: int, data: bytes, timeout: Optional[float] = None):
        # SHORT_DOWNLOAD header: cmd(1) + size(1) + addr_ext(1) + addr(4) + data[N] <= MAX_CTO
        header = 1 + 1 + 1 + 4
        max_data = max(0, self.max_cto - header)
        if len(data) > max_data:
            raise ValueError(f"Data too large for SHORT_DOWNLOAD: {len(data)} > {max_data} (MAX_CTO={self.max_cto})")
        args = bytes([len(data), 0, addr_ext]) + self.u32(address) + data
        self._request(CMD_SHORT_DOWNLOAD, args, timeout)

    def download(self, data: bytes, timeout: Optional[float] = None):
        # Requires MTA set. DOWNLOAD payload: cmd(1) + size(1) + data[N], N <= MAX_CTO-2
        max_chunk = max(0, self.max_cto - 2)
        off = 0
        while off < len(data):
            chunk = data[off:off + max_chunk]
            args = bytes([len(chunk)]) + chunk
            self._request(CMD_DOWNLOAD, args, timeout)
            off += len(chunk)

    def write(self, addr_ext: int, address: int, data: bytes, timeout: Optional[float] = None):
        """
        High-level calibration write helper. Uses SHORT_DOWNLOAD when it fits, else SET_MTA + DOWNLOAD chunks.
        """
        header = 1 + 1 + 1 + 4
        max_data_short = max(0, self.max_cto - header)
        if len(data) <= max_data_short:
            self.short_download(addr_ext, address, data, timeout)
        else:
            self.set_mta(addr_ext, address, timeout)
            self.download(data, timeout)

    # Optional: page switching
    def set_cal_page(self, mode: int, segment: int, page: int, timeout: Optional[float] = None):
        args = bytes([mode, segment, page])
        self._request(CMD_SET_CAL_PAGE, args, timeout)

    # ------------- DAQ setup -------------

    def free_daq(self, timeout: Optional[float] = None):
        self._request(CMD_FREE_DAQ, b"", timeout)

    def alloc_daq(self, daq_count: int, timeout: Optional[float] = None):
        args = self.u16(daq_count)
        self._request(CMD_ALLOC_DAQ, args, timeout)

    def alloc_odt(self, daq_list: int, odt_num: int, timeout: Optional[float] = None):
        args = self.u16(daq_list) + bytes([odt_num])
        self._request(CMD_ALLOC_ODT, args, timeout)

    def alloc_odt_entry(self, daq_list: int, odt: int, entries: int, timeout: Optional[float] = None):
        args = self.u16(daq_list) + bytes([odt, entries])
        self._request(CMD_ALLOC_ODT_ENTRY, args, timeout)

    def clear_daq_list(self, daq_list: int, timeout: Optional[float] = None):
        args = self.u16(daq_list)
        self._request(CMD_CLEAR_DAQ_LIST, args, timeout)

    def set_daq_ptr(self, daq_list: int, odt: int, entry: int, timeout: Optional[float] = None):
        args = self.u16(daq_list) + bytes([odt, entry])
        self._request(CMD_SET_DAQ_PTR, args, timeout)

    def write_daq(self, bit_offset: int, size: int, addr_ext: int, address: int, timeout: Optional[float] = None):
        args = bytes([bit_offset & 0xFF, size & 0xFF, addr_ext & 0xFF]) + self.u32(address)
        self._request(CMD_WRITE_DAQ, args, timeout)

    def set_daq_list_mode(self, daq_list: int, event: int, prescaler: int = 1, priority: int = 0, mode: int = 0x01, timeout: Optional[float] = None):
        """
        mode is bit-coded per XCP: e.g., direction, timestamping, etc.
        For simple measurement: mode=0x01 (selected)
        """
        args = bytes([mode]) + self.u16(daq_list) + self.u16(event) + bytes([prescaler, priority])
        self._request(CMD_SET_DAQ_LIST_MODE, args, timeout)

    def start_stop_daq_list(self, daq_list: int, start: bool = True, timeout: Optional[float] = None):
        mode = 0x01 if start else 0x02  # 0x01=start selected, 0x02=stop selected
        args = bytes([mode]) + self.u16(daq_list)
        self._request(CMD_START_STOP_DAQ_LIST, args, timeout)

    def start_stop_synch(self, start: bool = True, timeout: Optional[float] = None):
        mode = 0x01 if start else 0x02
        args = bytes([mode])
        self._request(CMD_START_STOP_SYNCH, args, timeout)

    # ------------- DAQ parsing -------------

    def register_daq_entry(self, odt_pid: int, entry_name: str, size: int, addr_ext: int, address: int):
        """
        Register an entry for an ODT PID to allow parsing incoming DAQ DTOs.
        Assumes bit_offset == 0 (byte aligned).
        """
        self.daq_map.setdefault(odt_pid, []).append({
            "name": entry_name,
            "size": size,
            "addr_ext": addr_ext,
            "addr": address,
        })

    def on_daq(self, cb: Callable[[int, Dict[str, int], bytes], None]):
        """
        Set a callback for DAQ DTOs:
          cb(odt_pid, values_dict, raw_payload_bytes)
        """
        self.daq_callback = cb

    def _handle_daq(self, odt_pid: int, payload: bytes):
        # Parse based on registry
        entries = self.daq_map.get(odt_pid)
        if not entries:
            # If not registered, still notify raw
            if self.daq_callback:
                self.daq_callback(odt_pid, {}, payload)
            return

        values: Dict[str, int] = {}
        off = 0
        for e in entries:
            sz = e["size"]
            if off + sz > len(payload):
                break
            raw = payload[off:off+sz]
            # Little-endian unsigned
            val = int.from_bytes(raw, self.byteorder)
            values[e["name"]] = val
            off += sz

        if self.daq_callback:
            self.daq_callback(odt_pid, values, payload)

    # ------------- Convenience high-level APIs -------------

    def read(self, addr_ext: int, address: int, size: int, timeout: Optional[float] = None) -> bytes:
        """
        High-level read helper. Uses SHORT_UPLOAD when possible, else SET_MTA + UPLOAD.
        """
        header = 1 + 1 + 1 + 4  # cmd + size + addr_ext + addr
        max_size_short = max(0, self.max_cto - header)
        if size <= max_size_short:
            return self.short_upload(size, addr_ext, address, timeout)
        self.set_mta(addr_ext, address, timeout)
        return self.upload(size, timeout)

