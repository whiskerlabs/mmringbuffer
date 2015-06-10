# Constant indices within mmap buffers.
_POS_VALUE_SIZE = 8
_READ_POS_IDX   = 0
_WRITE_POS_IDX  = _POS_VALUE_SIZE
_HEADER_LEN     = _POS_VALUE_SIZE * 2

# struct.[un]pack format string for length fields
_LEN_RECORD_FORMAT = "q"
