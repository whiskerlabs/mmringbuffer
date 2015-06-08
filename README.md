# Memory-Mapped Ring Buffer

A memory-mapped ring buffer implementation in Python.

This module provides a `MemMapRingBuffer` class which is essentially a
memory-mapped variant of `collections.deque(maxlen)`. This combination
of functionality comes in handy when one needs to buffer data that
must persist across machine restarts.

## Installation

    $ pip install mmringbuffer

## Usage

    # Create a 1MB ring buffer backed by a file under /var/spool to
    # store seven-byte-long strings.
    file_path = "/var/spool/mmrbexample"
    mmbuf = MemMapRingBuffer(file_path, 1024 * 1024, 7)
    mmbuf.put("vanilla")
    mmbuf.put("dogsled")
    assert mmbuf.get() == "vanilla"
