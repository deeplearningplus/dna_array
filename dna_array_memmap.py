import numpy as np

## 0. Unpacking the packed 2-bit data step by step into usable integers
## Speed: slow
class PackedArrayMemmap:
    def __init__(self, filename, num_elements):
        self.filename = filename
        self.num_elements = num_elements
        self.bytes_per_element = 2  # Each element is 2 bits
        self.bytes_in_file = (num_elements + 3) // 4  # Total bytes in packed file
        self.memmap = np.memmap(filename, dtype=np.uint8, mode='r', shape=(self.bytes_in_file,))
        self.cache = None  # Cache to store recently unpacked data
        self.cache_range = None  # (start, stop) range of cached indices

    def __len__(self):
        return self.num_elements

    def _unpack_bytes(self, raw_bytes):
        """
        Unpack bytes into a NumPy array of 2-bit integers using vectorized operations.
        """
        expanded = np.zeros(len(raw_bytes) * 4, dtype=np.uint8)
        expanded[0::4] = (raw_bytes >> 6) & 0x03  # First 2 bits
        expanded[1::4] = (raw_bytes >> 4) & 0x03  # Second 2 bits
        expanded[2::4] = (raw_bytes >> 2) & 0x03  # Third 2 bits
        expanded[3::4] = raw_bytes & 0x03         # Fourth 2 bits
        return expanded

    def _fetch_and_unpack(self, start, stop):
        """
        Fetch the relevant bytes from the memmap and unpack them into 2-bit integers.
        """
        # Compute byte range to read
        first_byte = start // 4
        last_byte = (stop + 3) // 4  # Include the byte containing the last bit

        # Read the raw bytes
        raw_bytes = self.memmap[first_byte:last_byte]

        # Unpack the bytes into 2-bit integers
        unpacked = self._unpack_bytes(raw_bytes)

        # Return the requested slice
        return unpacked[(start % 4):(stop - start + start % 4)]

    def __getitem__(self, key):
        if isinstance(key, int):  # Single index access
            if key < 0:  # Handle negative indexing
                key += self.num_elements
            if key < 0 or key >= self.num_elements:
                raise IndexError("Index out of range")

            # Use caching for single index access
            if self.cache_range and self.cache_range[0] <= key < self.cache_range[1]:
                return self.cache[key - self.cache_range[0]]

            # Fetch the relevant byte and extract the 2-bit value
            byte_index = key // 4
            bit_offset = (key % 4) * 2
            byte_value = self.memmap[byte_index]
            return (byte_value >> (6 - bit_offset)) & 0x03

        elif isinstance(key, slice):  # Slicing access
            start, stop, step = key.indices(self.num_elements)

            if step != 1:
                # For non-contiguous slicing, fallback to Python-level slicing
                return np.array([self[i] for i in range(start, stop, step)], dtype=np.uint8)

            # Check if the slice is fully cached
            if self.cache_range and self.cache_range[0] <= start < self.cache_range[1] and self.cache_range[1] >= stop:
                return self.cache[start - self.cache_range[0]:stop - self.cache_range[0]]

            # Fetch and unpack the data for the requested range
            result = self._fetch_and_unpack(start, stop)

            # Update the cache
            self.cache = result
            self.cache_range = (start, stop)

            return result

        else:
            raise TypeError("Invalid index type")

## 1. Unpack Entire Data Once (Preloading)
## If memory permits, unpack the entire data once and keep it in memory as a np.ndarray. 
## This eliminates the need to unpack data repeatedly during each access:
## Speed: fast
class PackedArrayMemmapPreload:
    def __init__(self, filename, num_elements):
        self.filename = filename
        self.num_elements = num_elements
        self.bytes_in_file = (num_elements + 3) // 4  # Calculate number of bytes
        self.memmap = np.memmap(filename, dtype=np.uint8, mode='r', shape=(self.bytes_in_file,))
        self.unpacked_array = self._unpack_all()  # Unpack entire file into memory

    def __len__(self):
        return self.num_elements

    def _unpack_all(self):
        """
        Unpack all bytes into a NumPy array of 2-bit integers.
        """
        raw_bytes = self.memmap[:]
        return self._unpack_bytes(raw_bytes)

    def _unpack_bytes(self, raw_bytes):
        """
        Unpack bytes into a NumPy array of 2-bit integers using vectorized operations.
        """
        expanded = np.zeros(len(raw_bytes) * 4, dtype=np.uint8)
        expanded[0::4] = (raw_bytes >> 6) & 0x03  # First 2 bits
        expanded[1::4] = (raw_bytes >> 4) & 0x03  # Second 2 bits
        expanded[2::4] = (raw_bytes >> 2) & 0x03  # Third 2 bits
        expanded[3::4] = raw_bytes & 0x03         # Fourth 2 bits
        return expanded[:self.num_elements]  # Trim to the number of elements

    def __getitem__(self, key):
        return self.unpacked_array[key]


## 2. Batch Unpacking for Access
## If preloading the entire dataset is infeasible, unpack data in batches and cache it. 
## This avoids repeated byte-by-byte unpacking for overlapping ranges.
## Speed: intermediate
class PackedArrayMemmapBatch:
    def __init__(self, filename, num_elements, batch_size=10):
        self.filename = filename
        self.num_elements = num_elements
        self.batch_size = batch_size
        self.bytes_in_file = (num_elements + 3) // 4
        self.memmap = np.memmap(filename, dtype=np.uint8, mode='r', shape=(self.bytes_in_file,))
        self.cache = None
        self.cache_range = None

    def __len__(self):
        return self.num_elements

    def _unpack_bytes(self, raw_bytes):
        expanded = np.zeros(len(raw_bytes) * 4, dtype=np.uint8)
        expanded[0::4] = (raw_bytes >> 6) & 0x03
        expanded[1::4] = (raw_bytes >> 4) & 0x03
        expanded[2::4] = (raw_bytes >> 2) & 0x03
        expanded[3::4] = raw_bytes & 0x03
        return expanded

    def _fetch_and_unpack_batch(self, start):
        """
        Fetch and unpack a batch starting from `start`.
        """
        batch_start = (start // self.batch_size) * self.batch_size
        batch_end = min(batch_start + self.batch_size, self.num_elements)
        byte_start = batch_start // 4
        byte_end = (batch_end + 3) // 4
        raw_bytes = self.memmap[byte_start:byte_end]
        unpacked = self._unpack_bytes(raw_bytes)
        unpacked = unpacked[: batch_end - batch_start]
        self.cache = unpacked
        self.cache_range = (batch_start, batch_end)

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0:
                key += self.num_elements
            if not (self.cache_range and self.cache_range[0] <= key < self.cache_range[1]):
                self._fetch_and_unpack_batch(key)
            return self.cache[key - self.cache_range[0]]

        elif isinstance(key, slice):
            start, stop, step = key.indices(self.num_elements)
            if step != 1:
                return np.array([self[i] for i in range(start, stop, step)])
            if not (self.cache_range and self.cache_range[0] <= start < self.cache_range[1] and self.cache_range[1] >= stop):
                self._fetch_and_unpack_batch(start)
            return self.cache[start - self.cache_range[0]:stop - self.cache_range[0]]

        else:
            raise TypeError("Invalid index type")


if __name__ == '__main__':
    import time
    #a = PackedArrayMemmap("output_large.bin", 32_000_000)
    a = PackedArrayMemmapPreload("output_large.bin", 32_000_000)
    #a = PackedArrayMemmapBatch("output_large.bin", 32_000_000)
    tic = time.time()
    idxs = np.random.randint(0, 32_000_000 - 10_000, 10000)
    for idx in idxs:
        b = a[idx: idx + 10000]
    toc = time.time()
    print(f"Time elapse: {toc - tic} secs.")


