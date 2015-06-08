import mmap
import os

class MemMapRingBuffer(object):
  """A memory-mapped ring buffer."""

  def __init__(self, file_path, capacity, item_size):
    assert capacity > item_size

    self.capacity = capacity
    self.buffer_size = capacity + item_size
    self.item_size = item_size

    # Initialize a memory-mapped file in which to store data to be
    # posted to sMAP in the event that network connectivity is lost.
    buffer_file = open(file_path, "a+b")
    file_current_size = os.stat(file_path).st_size
    if file_current_size < self.buffer_size:
      buffer_file.seek(file_current_size)
      buffer_file.write("\0" * (self.buffer_size - file_current_size))
      buffer_file.flush()
    self.mmap_buffer = mmap.mmap(buffer_file.fileno(), self.buffer_size)
    self.read_position = 0
    self.write_position = 0

    # TODO: Support non-empty buffers on init

  def empty(self):
    """Return `True` if the buffer is empty, `False` otherwise."""
    return self.read_position == self.write_position

  def full(self):
    """Return `True` if the buffer is full, `False` otherwise."""
    # The buffer is full if the read position is directly ahead of the
    # write position.
    return (
      self.write_position + 2*self.item_size > self.buffer_size and self.read_position == 0
    ) or (
      self.write_position + self.item_size > self.buffer_size and self.read_position == self.item_size
    ) or (
      self.write_position + self.item_size == self.read_position
    )

  def put(self, item):
    """Put the bytes of the string `item` in the buffer."""
    assert type(item) is str
    assert len(item) == self.item_size

    was_full = self.full()

    # If there isn't enough remaining space at the tail of the buffer
    # to fit another item, then wrap around.
    if self.write_position + self.item_size > self.buffer_size:
      self.write_position = 0

    self.mmap_buffer.seek(self.write_position)
    self.mmap_buffer.write(item)
    self.mmap_buffer.flush()
    self.write_position = self.mmap_buffer.tell() % self.buffer_size

    # If the buffer was full prior to insertion, then the read
    # position must be moved to the next item.
    if was_full:
      if self.write_position + self.item_size > self.buffer_size:
        self.read_position = self.item_size
      else:
        self.read_position = self.write_position + self.item_size

  def get(self):
    """Remove and return an item from the buffer. Throws `IndexError`
    if buffer is empty.
    """
    if self.read_position + self.item_size > self.buffer_size:
      self.read_position = 0

    if self.empty():
      raise IndexError("MemMapRingBuffer.get(): buffer is empty")

    self.mmap_buffer.seek(self.read_position)
    result = self.mmap_buffer.read(self.item_size)
    self.read_position = self.mmap_buffer.tell() % self.buffer_size
    return result

  def clear(self):
    """Remove all elements from the buffer."""
    self.mmap_buffer.seek(0)
    self.mmap_buffer.write("\0" * self.buffer_size)
    self.mmap_buffer.flush()
    self.read_position = 0
    self.write_position = 0
