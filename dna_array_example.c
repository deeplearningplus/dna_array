#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

void save_large_array_to_file(const char *filename, const uint8_t *arr, size_t size) {
    FILE *file = fopen(filename, "wb");
    if (!file) {
        perror("Failed to open file");
        return;
    }

    uint8_t buffer = 0;  // Buffer for packed bits
    int bit_position = 0; // Tracks current bit position in the buffer

    for (size_t i = 0; i < size; ++i) {
        // Pack 2 bits of the current element into the buffer
        buffer |= (arr[i] & 0x03) << (6 - bit_position);
        bit_position += 2;

        // Write buffer when full
        if (bit_position == 8) {
            fwrite(&buffer, 1, 1, file);
            buffer = 0;
            bit_position = 0;
        }
    }

    // Write remaining bits
    if (bit_position > 0) {
        fwrite(&buffer, 1, 1, file);
    }

    fclose(file);
}

void read_large_array_from_file(const char *filename, uint8_t *arr, size_t size) {
    FILE *file = fopen(filename, "rb");
    if (!file) {
        perror("Failed to open file");
        return;
    }

    uint8_t buffer = 0;  // Buffer for packed bits
    int bit_position = 0; // Tracks current bit position in the buffer

    for (size_t i = 0; i < size; ++i) {
        // Read a new byte when needed
        if (bit_position == 0) {
            fread(&buffer, 1, 1, file);
        }

        // Extract the next 2 bits
        arr[i] = (buffer >> (6 - bit_position)) & 0x03;
        bit_position += 2;

        // Reset bit position when byte is consumed
        if (bit_position == 8) {
            bit_position = 0;
        }
    }

    fclose(file);
}

int main() {
    size_t size = 32000000; // 32e6 elements
    uint8_t *arr = malloc(size * sizeof(uint8_t));

    // Fill the array with random values (0, 1, 2, 3)
    for (size_t i = 0; i < size; ++i) {
        arr[i] = rand() % 4; // Values: 0, 1, 2, 3
    }
	// Print the first 10 elements
	for (size_t i = 0; i < 10; i++)
		printf("%d ", arr[i]);
	printf("\n");


    // Save the array to a file
    save_large_array_to_file("output_large.bin", arr, size);

    // Read the array back
    uint8_t *recovered_arr = malloc(size * sizeof(uint8_t));
    read_large_array_from_file("output_large.bin", recovered_arr, size);

    // Verify the content
    int mismatch = 0;
    for (size_t i = 0; i < size; ++i) {
        if (arr[i] != recovered_arr[i]) {
            mismatch = 1;
            printf("Mismatch at index %zu: %d != %d\n", i, arr[i], recovered_arr[i]);
            break;
        }
    }

    // Print the first 10 elements
	for (size_t i = 0; i < 10; i++)
		printf("%d ", recovered_arr[i]);
	printf("\n");


    if (!mismatch) {
        printf("Arrays match perfectly!\n");
    }

    free(arr);
    free(recovered_arr);
    return 0;
}

