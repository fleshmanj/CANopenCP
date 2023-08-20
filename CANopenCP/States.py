from enum import Enum

class CANopenSDOStates(Enum):

    CO_SDO_ST_IDLE = 0x00
    CO_SDO_ST_ABORT = 0x01
    CO_SDO_ST_DOWNLOAD_LOCAL_TRANSFER = 0x10
    CO_SDO_ST_DOWNLOAD_INITIATE_REQ = 0x11
    CO_SDO_ST_DOWNLOAD_INITIATE_RSP = 0x12
    CO_SDO_ST_DOWNLOAD_SEGMENT_REQ = 0x13
    CO_SDO_ST_DOWNLOAD_SEGMENT_RSP = 0x14
    CO_SDO_ST_UPLOAD_LOCAL_TRANSFER = 0x20
    CO_SDO_ST_UPLOAD_INITIATE_REQ = 0x21
    CO_SDO_ST_UPLOAD_INITIATE_RSP = 0x22
    CO_SDO_ST_UPLOAD_SEGMENT_REQ = 0x23
    CO_SDO_ST_UPLOAD_SEGMENT_RSP = 0x24
    CO_SDO_ST_DOWNLOAD_BLK_INITIATE_REQ = 0x51
    CO_SDO_ST_DOWNLOAD_BLK_INITIATE_RSP = 0x52
    CO_SDO_ST_DOWNLOAD_BLK_SUBBLOCK_REQ = 0x53
    CO_SDO_ST_DOWNLOAD_BLK_SUBBLOCK_RSP = 0x54
    CO_SDO_ST_DOWNLOAD_BLK_END_REQ = 0x55
    CO_SDO_ST_DOWNLOAD_BLK_END_RSP = 0x56
    CO_SDO_ST_UPLOAD_BLK_INITIATE_REQ = 0x61
    CO_SDO_ST_UPLOAD_BLK_INITIATE_RSP = 0x62
    CO_SDO_ST_UPLOAD_BLK_SUBBLOCK_SREQ = 0x64
    CO_SDO_ST_UPLOAD_BLK_SUBBLOCK_CRSP = 0x65
    CO_SDO_ST_UPLOAD_BLK_END_SREQ = 0x66
    CO_SDO_ST_UPLOAD_BLK_END_CRSP = 0x67
    # ... Add other SDO-specific states as necessary ...