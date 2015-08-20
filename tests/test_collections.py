from mmringbuffer import MemMapRingBuffer
import pytest
import tempfile

def test_capacity():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 1024)
  assert mmbuf.capacity == 1024

def test_initialize_new_file_as_empty():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 1024)
  assert mmbuf.empty()

def test_empty_after_clear():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 16)
  mmbuf.put("vanilla")
  mmbuf.clear()
  assert mmbuf.empty()

def test_get_on_empty_buffer_raises_indexerror():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 1024)
  assert mmbuf.empty()
  with pytest.raises(IndexError):
    mmbuf.get()

def test_get_a_stored_value():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 1024)
  mmbuf.put("vanilla")
  assert mmbuf.get() == "vanilla"

def test_add_remove():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 16)
  for s in ["vanilla", "tandoor", "sunsets"]:
    mmbuf.put(s)
    assert mmbuf.get() == s
  assert mmbuf.empty()

def test_variable_item_size_add_remove():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 16)
  for s in ["vanilla", "dice", "car"]:
    mmbuf.put(s)
    assert mmbuf.get() == s
  assert mmbuf.empty()

def test_wrap_overwrite():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 12)
  words = ["ab", "cd", "ef", "gh"]
  for s in words[:2]:
    mmbuf.put(s)

  for s in words[:2]:
    assert mmbuf.get() == s

  assert mmbuf.empty()

  for s in words:
    mmbuf.put(s)
  for s in words[2:4]:
    assert mmbuf.get() == s

def test_variable_item_size_wrap_overwrite():
  mmbuf = MemMapRingBuffer(tempfile.mkstemp()[1], 14)
  words = ["a", "bcdef", "ghij", "kl"]
  for s in words[:2]:
    mmbuf.put(s)

  for s in words[:2]:
    assert mmbuf.get() == s

  assert mmbuf.empty()

  for s in words:
    mmbuf.put(s)
  for s in words[2:4]:
    assert mmbuf.get() == s

def test_read_load_data_from_file():
  file_path = tempfile.mkstemp()[1]
  mmbuf1 = MemMapRingBuffer(file_path, 1024)
  for s in ["vanilla", "tandoor", "sunsets"]:
    mmbuf1.put(s)

  mmbuf2 = MemMapRingBuffer(file_path, 1024)
  for s in ["vanilla", "tandoor", "sunsets"]:
    assert mmbuf2.get() == s
