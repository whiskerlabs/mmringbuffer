# Memory-Mapped Ring Buffer

A memory-mapped ring buffer implementation in Python.

This module provides a `MemMapRingBuffer` class which is essentially a
memory-mapped variant of `collections.deque(maxlen)`. This combination
of functionality comes in handy when one needs to buffer data that
must persist across machine restarts.

Latest stable version:
[mmringbuffer v0.0.1](https://pypi.python.org/pypi/mmringbuffer/0.0.1),
released
[June 10, 2015](https://github.com/whiskerlabs/mmringbuffer/releases/tag/0.0.1)

## Buffer layout

The underlying mmap buffer is prefixed with a header containing two
64-bit integers representing the current read and write positions
within the buffer. These positions are updated with each read and
write in order to make buffer state fully reflected in the on-disk
format.

A single logical slot in the ring buffer is always left unallocated in
order to ensure that the read and write positions are only ever equal
when the buffer is empty [1].

Because of these two conditions, the actual size of the underlying
memory-mapped buffer, in terms of the arguments to `__init__`, is
equal to

    8 + 8 + (item_size * (capacity + 1))

[1] http://en.wikipedia.org/wiki/Circular_buffer#Always_keep_one_slot_open

## Installation

Install with `pip`:

    $ pip install mmringbuffer

Install from source:

    $ git clone git@github.com:whiskerlabs/mmringbuffer.git
    $ cd mmringbuffer
    $ python setup.py install

## Usage

    # Create a 1MB ring buffer backed by a file under /var/spool to
    # store seven-byte-long strings.
    file_path = "/var/spool/mmrbexample"
    mmbuf = MemMapRingBuffer(file_path, 1024 * 1024, 7)
    mmbuf.put("vanilla")
    mmbuf.put("dogsled")
    assert mmbuf.get() == "vanilla"

## Support

For questions or bug reports, please
[file an issue on Github](https://github.com/whiskerlabs/mmringbuffer/issues).

For any other inquiries, send mail to `software at whiskerlabs.com`.

## License

Copyright 2015 Whisker Labs

Licensed under the MIT License. See LICENSE for details.
