#include <stdio.h>
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
