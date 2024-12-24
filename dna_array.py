import ctypes
import numpy as np
import mmap

# Load the shared library
dna_array_lib = ctypes.CDLL('./dna_array.so')  # Use .dll on Windows

# Define the function signature
dna_array_lib.read_large_array_from_file.argtypes = [
    ctypes.c_char_p,       # const char *filename
    ctypes.POINTER(ctypes.c_uint8),  # uint8_t *arr
    ctypes.c_size_t        # size_t size
]

dna_array_lib.read_large_array_from_file.restype = None
dna_array_lib.save_large_array_to_file.restype = None

def save_large_array(filename, arr):
    """
    Python interface for the C function `save_large_array_to_file`.

    Args:
        filename (str): The path to save the binary file.
        arr (numpy.ndarray): A NumPy array of uint8 elements (values 0-3).

    Raises:
        ValueError: If array contains values outside the range [0, 3].
    """
    if arr.dtype != np.uint8:
        raise ValueError("Array must be of type uint8.")
    if not np.all((arr >= 0) & (arr <= 3)):
        raise ValueError("Array values must be in the range [0, 3].")

    # Call the C function to save the array
    dna_array_lib.save_large_array_to_file(
        filename.encode('utf-8'),  # Convert filename to bytes
        arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),  # Pass array pointer
        arr.size
    )

def read_large_array(filename, size):
    """
    Python interface for the C function `read_large_array_from_file`.

    Args:
        filename (str): The path to the binary file containing packed data.
        size (int): The number of 2-bit elements to unpack.

    Returns:
        numpy.ndarray: A NumPy array containing the unpacked data.
    """
    # Allocate space for the array
    arr = np.zeros(size, dtype=np.uint8)

    # Call the C function
    dna_array_lib.read_large_array_from_file(
        filename.encode('utf-8'),  # Convert filename to bytes
        arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),  # Pass the array as pointer
        size
    )

    return arr

# Example usage
if __name__ == "__main__":

    # Number of 2-bit elements to read
    array_size = 32000000

    # Create a sample array of uint8 values (0, 1, 2, 3)
    array = np.random.randint(0, 4, size=array_size, dtype=np.uint8)

    # File to save the packed binary data
    output_file = "output_large.bin"

    # Save the array
    save_large_array(output_file, array)
    print(f"Array saved to {output_file}.")


    # Read the array
    unpacked_array = read_large_array(output_file, array_size)

    # Print a slice of the array for verification
    print("First 10 elements:", unpacked_array[:10])

    print(f"All identical: {(array == unpacked_array).all()}")
