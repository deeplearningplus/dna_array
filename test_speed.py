import time
import numpy as np
import mmap
from dna_array_memmap import *

class PackedArrayMemmapNaive:
    def __init__(self, filename, size):
        """
        Initialize a memory-mapped interface to read 2-bit packed values.
        Args:
            filename (str): Path to the packed binary file.
            size (int): Number of 2-bit elements in the file.
        Raises:
            ValueError: If file size doesn't match the expected number of elements.
        """
        self.filename = filename
        self.size = size
        self.byte_size = (size + 3) // 4  # Each byte contains 4 elements (2 bits each)
        # Open the file in binary read mode and memory-map it
        self.file = open(filename, "rb")
        self.mmap = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        # Check file size
        if self.mmap.size() < self.byte_size:
            self.mmap.close()
            self.file.close()
            raise ValueError("File size is smaller than expected for the given number of elements.")

    def __getitem__(self, idx):
        """
        Access one or more elements from the packed array.
        Args:
            idx (int or slice): Index or slice of elements to access.
        Returns:
            np.ndarray: Array of unpacked 2-bit values.
        """
        if isinstance(idx, slice):
            start, stop, step = idx.indices(self.size)
            indices = range(start, stop, step)
        else:
            indices = [idx]
        # Initialize an output array
        result = np.zeros(len(indices), dtype=np.uint8)
        for i, index in enumerate(indices):
            if index < 0 or index >= self.size:
                raise IndexError("Index out of bounds.")
            byte_idx = index // 4  # Which byte the element is in
            bit_offset = (index % 4) * 2  # Position in the byte (0, 2, 4, 6)
            # Extract the 2-bit value
            byte_value = self.mmap[byte_idx]
            result[i] = (byte_value >> (6 - bit_offset)) & 0x03
        return result[0] if isinstance(idx, int) else result

    def __len__(self):
        """
        Return the total number of elements.
        """
        return self.size
    def close(self):
        """
        Close the memory-mapped file and associated resources.
        """
        self.mmap.close()
        self.file.close()




# For speed comparison only as it does not correctly parse byte data into integer.
a = np.memmap("output_large.bin", dtype=np.uint8, mode="r")
tic = time.time()
idxs = np.random.randint(0, 32_000_000 - 10_000, 10000)
for idx in idxs:
  b = a[idx: idx + 10000]
toc = time.time()
print(f"np.memmap - Time elapse: {toc - tic} secs.")




a = PackedArrayMemmap("output_large.bin", 32_000_000)
tic = time.time()
idxs = np.random.randint(0, 32_000_000 - 10_000, 10000)
for idx in idxs:
  b = a[idx: idx + 10000]
toc = time.time()
print(f"PackedArrayMemmap - Time elapse: {toc - tic} secs.")



a = PackedArrayMemmapPreload("output_large.bin", 32_000_000)
tic = time.time()
idxs = np.random.randint(0, 32_000_000 - 10_000, 10000)
for idx in idxs:
  b = a[idx: idx + 10000]
toc = time.time()
print(f"PackedArrayMemmapPreload - Time elapse: {toc - tic} secs.")


a = PackedArrayMemmapBatch("output_large.bin", 32_000_000)
tic = time.time()
idxs = np.random.randint(0, 32_000_000 - 10_000, 10000)
for idx in idxs:
  b = a[idx: idx + 10000]
toc = time.time()
print(f"PackedArrayMemmapBatch - Time elapse: {toc - tic} secs.")




a = PackedArrayMemmapNaive("output_large.bin", 32_000_000)
tic = time.time()
idxs = np.random.randint(0, 32_000_000 - 10_000, 10000)
for idx in idxs:
  b = a[idx: idx + 10000]
toc = time.time()
print(f"PackedArrayMemmapNaive - Time elapse: {toc - tic} secs.")


#np.memmap - Time elapse: 0.02609539031982422 secs.
#PackedArrayMemmap - Time elapse: 0.25661396980285645 secs.
#PackedArrayMemmapPreload - Time elapse: 0.003321409225463867 secs.
#PackedArrayMemmapBatch - Time elapse: 0.1782209873199463 secs.
#PackedArrayMemmapNaive - Time elapse: 25.133869409561157 secs.

