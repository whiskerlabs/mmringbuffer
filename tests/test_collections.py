from mmringbuffer import MemMapRingBuffer
import pytest
import tempfile

def test_capacity():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 1024, 7)
  assert mmbuf.capacity == 1024

def test_initialize_new_file_as_empty():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 1024, 7)
  assert mmbuf.empty()

def test_empty_after_clear():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 16, 7)
  mmbuf.put("vanilla")
  mmbuf.clear()
  assert mmbuf.empty()

def test_get_on_empty_buffer_raises_indexerror():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 1024, 7)
  assert mmbuf.empty()
  with pytest.raises(IndexError):
    mmbuf.get()

def test_get_a_stored_value():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 1024, 7)
  mmbuf.put("vanilla")
  assert mmbuf.get() == "vanilla"

def test_full():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 16, 7)
  mmbuf.put("vanilla")
  mmbuf.put("hotchip")
  assert mmbuf.full()

def test_incr_add_remove_wrap():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 16, 7)
  for s in ["vanilla", "tandoor", "sunsets"]:
    mmbuf.put(s)
    assert mmbuf.get() == s
  assert not mmbuf.full()
  assert mmbuf.empty()

def test_wrap_overwrite():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 8, 2)
  words = ["ab", "cd", "ef", "gh", "ij", "kl", "mn", "op"]
  for s in words[:4]:
    mmbuf.put(s)

  assert mmbuf.full()

  for s in words[:4]:
    assert mmbuf.get() == s

  assert mmbuf.empty()

  for s in words:
    mmbuf.put(s)
  for s in words[4:8]:
    assert mmbuf.get() == s

def test_read_load_data_from_file():
  file_path = tempfile.mkstemp()[1]
  mmbuf1 = MemMapRingBuffer(file_path, 1024, 7)
  for s in ["vanilla", "tandoor", "sunsets"]:
    mmbuf1.put(s)

  mmbuf2 = MemMapRingBuffer(file_path, 1024, 7)
  for s in ["vanilla", "tandoor", "sunsets"]:
    assert mmbuf2.get() == s
