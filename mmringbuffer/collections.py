from .constants import _HEADER_LEN, _READ_POS_IDX, _WRITE_POS_IDX, _LEN_RECORD_FORMAT
import mmap
import os
import struct

class MemMapRingBuffer(object):
  """A memory-mapped ring buffer.

  A single slot in the ring buffer is always left unallocated in order
  to ensure that the read and write positions are only ever equal when
  the buffer is empty [1].

  The underlying mmap buffer is prefixed with a header containing the
  two integers representing the current read and write positions
  within the buffer. These positions are updated with each read and
  write in order to make buffer state fully reflected in the on-disk
  format.

  Because of these two conditions, the actual size of the underlying
  memory-mapped buffer, in terms of the arguments to `__init__`, is
  equal to

      4 + 4 + (item_size * (capacity + 1))

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
      _LEN_RECORD_FORMAT,
      self.mmap_buffer.read(4)
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
      _LEN_RECORD_FORMAT,
      self.mmap_buffer.read(4)
    )[0]
    if recorded_write_position == 0:
      return _HEADER_LEN
    else:
      return recorded_write_position


  def _record_rw_positions(self):
    """Record the current read and write positions to the buffer
    header.
    """
    packed_read_position = struct.pack(_LEN_RECORD_FORMAT, self.read_position)
    packed_write_position = struct.pack(_LEN_RECORD_FORMAT, self.write_position)
    self.mmap_buffer.seek(_READ_POS_IDX)
    self.mmap_buffer.write(packed_read_position)
    self.mmap_buffer.seek(_WRITE_POS_IDX)
    self.mmap_buffer.write(packed_write_position)


  def __init__(self, file_path, capacity, item_size):
    """
    Parameters
    ----------
    file_path : path to a file to be memory-mapped for use in the buffer
    capacity : maximum number of logical items to be stored in the buffer
    item_size : size, in bytes, of each individual item to be stored in the buffer
    """
    assert capacity > item_size

    self.capacity = capacity
    self.buffer_size = _HEADER_LEN + capacity + item_size
    self.item_size = item_size

    # Open the file and pad its tail with zeros if it's not large
    # enough to contain the buffer.
    buffer_file = open(file_path, "a+b")
    file_current_size = os.stat(file_path).st_size
    if file_current_size < self.buffer_size:
      buffer_file.seek(file_current_size)
      buffer_file.write("\0" * (self.buffer_size - file_current_size))
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


  def full(self):
    """Return `True` if the buffer is full, `False` otherwise."""
    # The buffer is full if the read position is directly ahead of the
    # write position.
    return (
      self.write_position + 2*self.item_size > self.buffer_size and self.read_position == _HEADER_LEN
    ) or (
      self.write_position + self.item_size > self.buffer_size and self.read_position == _HEADER_LEN + self.item_size
    ) or (
      self.write_position + self.item_size == self.read_position
    )


  def size(self):
    """Returns the number of allocated slots in the buffer."""
    if self.empty():
      return 0
    elif self.write_position > self.read_position:
      return (self.write_position - self.read_position) / self.item_size
    else:
      return ((self.capacity + self.item_size) - (self.read_position - self.write_position)) / self.item_size


  def put(self, item):
    """Put the bytes of the string `item` in the buffer."""
    assert type(item) is str
    assert len(item) == self.item_size

    was_full = self.full()

    # If there isn't enough remaining space at the tail of the buffer
    # to fit another item, then wrap around.
    if self.write_position + self.item_size > self.buffer_size:
      self.write_position = _HEADER_LEN

    self.mmap_buffer.seek(self.write_position)
    self.mmap_buffer.write(item)

    # Update the write position.
    if self.mmap_buffer.tell() == self.buffer_size:
      self.write_position = _HEADER_LEN
    else:
      self.write_position = self.mmap_buffer.tell()

    # If the buffer was full prior to insertion, then the read
    # position must be moved to the next item.
    if was_full:
      if self.write_position + self.item_size > self.buffer_size:
        self.read_position = _HEADER_LEN + self.item_size
      else:
        self.read_position = self.write_position + self.item_size

    self._record_rw_positions()
    self.mmap_buffer.flush()


  def get(self):
    """Remove and return an item from the buffer. Throws `IndexError`
    if buffer is empty.
    """
    if self.read_position + self.item_size > self.buffer_size:
      self.read_position = _HEADER_LEN

    if self.empty():
      raise IndexError("MemMapRingBuffer.get(): buffer is empty")

    self.mmap_buffer.seek(self.read_position)
    result = self.mmap_buffer.read(self.item_size)

    # Update the read position.
    if self.mmap_buffer.tell() == self.buffer_size:
      self.read_position = _HEADER_LEN
    else:
      self.read_position = self.mmap_buffer.tell()

    self._record_rw_positions()
    self.mmap_buffer.flush()
    return result


  def clear(self):
    """Remove all elements from the buffer."""
    self.mmap_buffer.seek(0)
    self.mmap_buffer.write("\0" * self.buffer_size)
    self.mmap_buffer.flush()
    self.read_position = _HEADER_LEN
    self.write_position = _HEADER_LEN
    self._record_rw_positions()
