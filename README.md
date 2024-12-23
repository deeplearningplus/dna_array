## Disk-efficient storage for DNA sequences

This library provides a simple and efficient way to save and read DNA sequences, reducing disk usage significantly. DNA sequences can be represented using four integers: `A`=0, `C`=1, `G`=2, and `T`=3. By leveraging this representation, we use np.uint8 arrays in Python to encode DNA sequences efficiently.

For example, an array with 32e6 elements (`np.random.randint(0, 4, size=int(32e6), dtype=np.uint8)`) would normally require **32 MB** to store on disk. Using this library, the file size can be reduced to just **8 MB**.

### Features

* Efficient disk storage for DNA sequences.
* Support for Python and C interfaces.
* Easy integration with Python through a shared library.

### Python example
The following Python example demonstrates how to generate, save, and compress a DNA sequence array:
```python
array = np.random.randint(0, 4, size=int(32e6), dtype=np.uint8)

with open("array_python.bin", "wb") as fout:
    fout.write(array.tobytes())

# This will generate a file array_python.bin (32Mb in size)

```


### C example
```bash
gcc dna_array_example.c -o dna_array_example -O3 -Wall

./dna_array_example

# This will generate a file output_large.bin (8Mb in size)
```

See `read_large_array_from_file` in `dna_array_example.c` on how to read the `output_large.bin`.


### Compile as shared library
```bash
gcc -shared -o dna_array.so -fPIC dna_array.c -O3 -Wall
```

### Python interface to dna_array.c
For Python integration with the C library, refer to the included file: `dna_array.py`.




