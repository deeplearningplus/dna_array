#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h> // Required for access()
#include <zlib.h>  // For handling compressed files

#define MAX_LINE_LENGTH 1024
#define BASES_PER_BYTE 4

// Encoding table: maps ASCII base to 2-bit integer
uint8_t base_to_code(char base) {
    switch (base) {
        case 'A': return 0;
        case 'C': return 1;
        case 'G': return 2;
        case 'T': return 3;
        default: return 255;  // Invalid base (e.g., 'N')
    }
}

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

// Process a FASTQ file
size_t process_fastq(const char *input_file, const char *output_file, size_t num_reads, size_t kmer_length) {
    if (access(output_file, F_OK) == 0) {
        printf("Output file `%s` exists, skip it.\n", output_file);
	return 0;
    }
    gzFile file = gzopen(input_file, "r");
    if (!file) {
        perror("Failed to open FASTQ file");
        exit(EXIT_FAILURE);
    }

    char id[MAX_LINE_LENGTH], seq[MAX_LINE_LENGTH], plus[MAX_LINE_LENGTH], qual[MAX_LINE_LENGTH];
    uint8_t *encoded_reads = malloc(kmer_length * num_reads);  // preallocated space for encoded reads
    size_t total_reads = 0;
    size_t total_bases = 0;

    while (gzgets(file, id, sizeof(id))) {
        gzgets(file, seq, sizeof(seq));  // Sequence line
        gzgets(file, plus, sizeof(plus));  // '+' line
        gzgets(file, qual, sizeof(qual));  // Quality line

        // Remove newline characters
        seq[strcspn(seq, "\r\n")] = '\0';

        // Filter out reads with 'N' or length < 32
        size_t len = strlen(seq);
        if (len < 32 || strchr(seq, 'N')) {
            continue;
        }

        // Encode the first 32 bases
        for (size_t i = 0; i < kmer_length; ++i) {
            uint8_t code = base_to_code(seq[i]);
            if (code == 255) {
                fprintf(stderr, "Invalid base in sequence: %s\n", seq);
                exit(EXIT_FAILURE);
            }
            encoded_reads[total_bases++] = code;

            // Resize the array if needed
            /*if (total_reads % (1 * 1024 * 1024) == 0) {
                encoded_reads = realloc(encoded_reads, total_reads + (1 * 1024 * 1024));
                if (!encoded_reads) {
                    perror("Failed to allocate memory for encoded reads");
                    exit(EXIT_FAILURE);
                }
            }
	    */
        }
	total_reads += 1;
	if (total_reads == num_reads) {
	    break;
	}
    }

    // Save the packed array
    save_large_array_to_file(output_file, encoded_reads, total_bases);

    free(encoded_reads);
    gzclose(file);
    return total_bases;
}

void error_usage() {
    fprintf(stderr, "Usage:   dna_array_fastq [options]\n");
    fprintf(stderr, "Example: dna_array_fastq -o out.bin -k 32 -n 1000000 -i input.txt\n");
    fprintf(stderr, "Options:\n");
    fprintf(stderr, "  -o <FILE>   output file\n");
    fprintf(stderr, "  -l <FILE>   log file if `-i` is set\n");
    fprintf(stderr, "  -i <FILE>   text file storing fastq files - one per line\n");
    fprintf(stderr, "  -q <FILE>   fastq file, if set overwrite `-i`\n");
    fprintf(stderr, "  -n <int>    number of reads (default: int(1e6))\n");
    fprintf(stderr, "  -k <int>    kmer length to clip (default: 32)\n");
    exit(EXIT_FAILURE);
}

const char *get_basename(const char *file_path) {
    const char *base = strrchr(file_path, '/'); // Find the last '/' character
    if (!base) {
        base = strrchr(file_path, '\\'); // For Windows-style paths
    }
    return base ? base + 1 : file_path; // Return the portion after the last '/'
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        error_usage();
    }

    const char *input_file = NULL;
    const char *fastq_file = NULL;
    const char *log_file = NULL;
    const char *output_file = NULL;
    size_t num_reads = 1000000;  // 1Mb reads
    size_t kmer_length = 32;

    for (int i = 1; i < argc; i+=2) {
        // do some basic validation
        if (i + 1 >= argc) { error_usage(); } // must have arg after flag
        if (argv[i][0] != '-') { error_usage(); } // must start with dash
        if (strlen(argv[i]) != 2) { error_usage(); } // must be -x (one dash, one letter)
        // read in the args
        if (argv[i][1] == 'o') { output_file = argv[i + 1]; }
        else if (argv[i][1] == 'q') { fastq_file = argv[i + 1]; }
        else if (argv[i][1] == 'i') { input_file = argv[i + 1]; }
        else if (argv[i][1] == 'n') { num_reads = atoi(argv[i + 1]); }
        else if (argv[i][1] == 'k') { kmer_length = atoi(argv[i + 1]); }
        else if (argv[i][1] == 'l') { log_file = argv[i + 1]; }
        else { error_usage(); }
    }

    if (fastq_file != NULL) {
        size_t total_bases = process_fastq(fastq_file, output_file, num_reads, kmer_length);
    } else {
	if (log_file == NULL) {
	    perror("You must provide a log_file via `-l`.");
	    exit(EXIT_FAILURE);
	}

	if (access(log_file, F_OK) == 0) {
            printf("Log file `%s` exists, exit.\n", log_file);
            return 0;
        }

	char buffer[1024];
	char out[2048];
        FILE *fp = fopen(input_file, "r");
	FILE *fout = fopen(log_file, "w");
	fprintf(fout, "file_path,total_base\n");
	while (fgets(buffer, sizeof(buffer), fp)) {
	    buffer[strcspn(buffer, "\r\n")] = '\0';
	    //output_file = get_basename(buffer);
	    sprintf(out, "%s%s", get_basename(buffer), ".bin");
	    size_t total_bases = process_fastq(buffer, out, num_reads, kmer_length);
	    fprintf(fout, "\"%s\",%ld\n", out, total_bases);
	    fflush(fout);
	}
	fclose(fp);
	fclose(fout);
    }

    return EXIT_SUCCESS;
}

