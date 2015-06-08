# Memory-Mapped Ring Buffer

A memory-mapped ring buffer implementation in Python.

This module provides a `MemMapRingBuffer` class which is essentially a
memory-mapped variant of `collections.deque(maxlen)`. This combination
of functionality comes in handy when one needs to buffer data that
must persist across machine restarts.

*NOTE:* This library is in alpha and thus all APIs and contracts are
subject to change. Buyer beware, at least until v0.0.1 is released.

## Installation

A 0.0.1 release of `mmringbuffer` hasn't been released, so the library
isn't available yet in the Python Package Index. For the time-being,
you can play with it by cloning this repository and installing it
locally.

    $ git clone git@github.com:whiskerlabs/mmringbuffer.git
    ...
    $ cd mmringbuffer
    $ pip install .

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
