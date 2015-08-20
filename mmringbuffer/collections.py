from .constants import (
  _HEADER_LEN, _ITEM_SIZE_FORMAT, _ITEM_SIZE_LEN, _POS_VALUE_FORMAT,
  _POS_VALUE_LEN, _READ_POS_IDX, _WRITE_POS_IDX
)
import mmap
import os
import struct

class MemMapRingBuffer(object):
  """A memory-mapped ring buffer.

  The underlying mmap buffer is prefixed with a header containing two
  64-bit integers representing the current read and write positions
  within the buffer. These positions are updated with each read and
  write in order to make buffer state fully reflected in the on-disk
  format.

  A single logical slot in the ring buffer is always left unallocated
  in order to ensure that the read and write positions are only ever
  equal when the buffer is empty [1].

  Because of these two conditions, the actual size of the underlying
  memory-mapped buffer, in terms of the arguments to `__init__`, is
  equal to

      8 + 8 + capacity + 1

  [1] http://en.wikipedia.org/wiki/Circular_buffer#Always_keep_one_slot_open
  """

  def _get_stored_read_position(self):
    """Return the read position that is recorded in the header of the
    underlying buffer. If the recorded read position is invalid, the
    initial read position is returned.

    Under normal operation, this will equal
    `self.read_position`. However when initializing a
    `MemMapRingBuffer` from a buffer file, the former read and write
    positions must be determined from the storage medium.
    """
    self.mmap_buffer.seek(_READ_POS_IDX)
    recorded_read_position = struct.unpack(
      _POS_VALUE_FORMAT,
      self.mmap_buffer.read(_POS_VALUE_LEN)
    )[0]
    if recorded_read_position == 0:
      return _HEADER_LEN
    else:
      return recorded_read_position


  def _get_stored_write_position(self):
    """Return the write position that is recorded in the header of the
    underlying buffer. If the recorded write position is invalid, the
    initial write position is returned.

    Under normal operation, this will equal
    `self.read_position`. However when initializing a
    `MemMapRingBuffer` from a buffer file, the former read and write
    positions must be determined from the storage medium.
    """
    self.mmap_buffer.seek(_WRITE_POS_IDX)
    recorded_write_position = struct.unpack(
      _POS_VALUE_FORMAT,
      self.mmap_buffer.read(_POS_VALUE_LEN)
    )[0]
    if recorded_write_position == 0:
      return _HEADER_LEN
    else:
      return recorded_write_position


  def _record_rw_positions(self):
    """Record the current read and write positions to the buffer
    header.
    """
    packed_read_position = struct.pack(_POS_VALUE_FORMAT, self.read_position)
    packed_write_position = struct.pack(_POS_VALUE_FORMAT, self.write_position)
    self.mmap_buffer.seek(_READ_POS_IDX)
    self.mmap_buffer.write(packed_read_position)
    self.mmap_buffer.seek(_WRITE_POS_IDX)
    self.mmap_buffer.write(packed_write_position)


  def __init__(self, file_path, capacity):
    """
    Parameters
    ----------
    file_path : path to a file to be memory-mapped for use in the buffer
    capacity : total size, in bytes, of the data set stored in the buffer
    """
    self.capacity = capacity
    self.buffer_size = _HEADER_LEN + capacity + 1

    # Open the file and ensure that its length is equal to `self.buffer_size`.
    buffer_file = open(file_path, "a+b")
    buffer_file.truncate(self.buffer_size)

    # This is probably unnecessary, but according to documentation [1],
    # `file.truncate`'s behavior is platform-dependent.
    #
    # [1] https://docs.python.org/2/library/stdtypes.html#file.truncate
    current_file_size = os.stat(file_path).st_size
    if current_file_size != self.buffer_size:
      buffer_file.seek(file_current_size)
      buffer_file.write("\0" * (self.buffer_size - current_file_size))
      buffer_file.flush()

    # Now mmap the file and check if it contains data. If so,
    # initialize the read and write positions.
    #
    # TODO: What if the file contains random data..? Perhaps add a
    # magic character to the header.
    self.mmap_buffer = mmap.mmap(buffer_file.fileno(), self.buffer_size)
    self.read_position = self._get_stored_read_position()
    self.write_position = self._get_stored_write_position()
    self._record_rw_positions()


  def empty(self):
    """Return `True` if the buffer is empty, `False` otherwise."""
    return self.read_position == self.write_position


  def _advance_read_position(self):
    """Advances the reader position by one item."""
    self.mmap_buffer.seek(self.read_position)
    read_position_delta = struct.unpack(
      _ITEM_SIZE_FORMAT,
      self.mmap_buffer.read(_ITEM_SIZE_LEN)
    )[0]
    self.read_position += (_ITEM_SIZE_LEN + read_position_delta)


  def _reader_needs_advancing(self, n):
    """Given the precondition that there is at least `n` bytes between
    the write position and the end of the buffer, returns `True` if
    there is enough space between the write and read positions to
    allocate `n` bytes.
    """
    return self.read_position > self.write_position and (
      self.read_position - self.write_position < _ITEM_SIZE_LEN + n)


  def put(self, item):
    """Put the bytes of the string `item` in the buffer."""
    assert type(item) is str, "items put into ring buffer must be strings"
    item_len = len(item)
    assert _ITEM_SIZE_LEN + item_len <= self.capacity, "item size exceeds buffer capacity"

    # If there isn't enough space from the write position to the end
    # of the buffer, then wrap around.
    prev_write_position = self.write_position
    was_empty = self.empty()
    if self.write_position + _ITEM_SIZE_LEN + item_len + 1 > self.buffer_size:
      self.write_position = _HEADER_LEN
      if was_empty:
        # Buffer was empty, so reset read position to reflect emptiness.
        self.read_position = _HEADER_LEN
      elif self.read_position > prev_write_position:
        # In wrapping around, the write position lapped the read
        # position, so the latter must be advanced one past
        # _HEADER_LEN.
        self.read_position = _HEADER_LEN
        self._advance_read_position()

    # If the buffer wasn't empty and there isn't enough space between
    # the write and read positions to fit the item, then advance the
    # read position until it fits.
    while not was_empty and self._reader_needs_advancing(item_len):
      self._advance_read_position()

    # Now that enough writer headroom has been ensured, it is safe to
    # write the item.
    self.mmap_buffer.seek(self.write_position)
    self.mmap_buffer.write(struct.pack(_ITEM_SIZE_FORMAT, item_len))
    self.mmap_buffer.write(item)

    # Update the write position.
    if self.mmap_buffer.tell() == self.buffer_size:
      self.write_position = _HEADER_LEN
    else:
      self.write_position = self.mmap_buffer.tell()

    self._record_rw_positions()


  def get(self):
    """Remove and return the next item from the buffer.

    Note that because read and write positions are stored in the
    header of the memory-mapped buffer, calling `get` represents a
    mutation to the buffer's metadata. Thus, it is often advisable to
    invoke `MemMapRingBuffer.flush()` manually after reading data from
    the buffer.
    """
    if self.empty():
      raise IndexError("buffer is empty")

    self.mmap_buffer.seek(self.read_position)
    item_len = struct.unpack(
      _ITEM_SIZE_FORMAT,
      self.mmap_buffer.read(_ITEM_SIZE_LEN)
    )[0]
    result = self.mmap_buffer.read(item_len)

    # Update the read position.
    if self.mmap_buffer.tell() == self.buffer_size:
      self.read_position = _HEADER_LEN
    else:
      self.read_position = self.mmap_buffer.tell()

    self._record_rw_positions()
    return result


  def flush(self):
    """Flush changes made to the in-memory buffer back to disk."""
    self.mmap_buffer.flush()


  def clear(self):
    """Remove all elements from the buffer."""
    self.mmap_buffer.seek(0)
    self.mmap_buffer.write("\0" * self.buffer_size)
    self.read_position = _HEADER_LEN
    self.write_position = _HEADER_LEN
    self._record_rw_positions()
