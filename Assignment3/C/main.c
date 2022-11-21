#include <stdio.h>
#include <math.h>

void write_a_bit(unsigned char* bits, unsigned char value, short idx) { // ok
    if (value != 0 && value != 1) return;
    short bit_size = sizeof(unsigned char)*8;
    if (idx<0 || idx>=bit_size) return;

    if (value == 0) {
        *bits &= ~((unsigned char) 1 << idx);
    }
    else {
        *bits |= ((unsigned char) 1 << idx);
    }
}

unsigned char get_a_bit (unsigned char value, short idx) { // ok
    if (idx<0 || idx>=8) return 0;
    // 7  6  5  4  3  2  1  0
    return (value & ((unsigned char) 1 << idx)) >> idx;
}


void bmpresize(unsigned char *imgptr, int h, int w, int k, unsigned char *outptr) {
    unsigned char result[36];
    for (int i=0; i<36; i++) result[i] = 255;
    int scaling_factor = (int) pow(2, k);
    int h_resized = h / scaling_factor;
    int w_resized = w / scaling_factor;
    int w_bytes = 3*w % 4 == 0 ? 3*w : ((3*w)/4) * 4 + 4;
    int w_bytes_resized = 3*w_resized % 4 == 0 ? 3*w_resized : ((3*w_resized)/4) * 4 + 4;
    // unsigned char avg_b, avg_g, avg_r = 0;
    // int sum_b, sum_g, sum_r = 0;
    // unsigned char avg = 0;
    unsigned int avg = 0;

    int locate = 0;
    int locate_out = 0;
    for (int i=0; i<h_resized; i++) {
        for (int j=0; j<w_resized*3; j=j+3) { // j = j+3
            for (int x=0; x<3; x++) {

                avg = 0;
                for (int m = i * scaling_factor; m < (i + 1) * scaling_factor; m++) {
                    for (int n = j * scaling_factor; n < (j+3) * scaling_factor; n+=3) { // n = n+3
                        locate = m * w_bytes + n+x;
                        avg += *(imgptr + locate);
                        printf("value: %d, pixel: %d %d, color: %d, address: %d\n", *(imgptr + locate), m, n/3, x,
                               locate);
                    }
                }
                printf("\n");

                printf("sum: %d, ", avg);
                avg /= (scaling_factor * scaling_factor);
                locate_out = i * w_bytes_resized + (j+x);
                printf("avg: %d\n", avg);
                printf("write at pixel: %d %d, color: %d, address: %d\n\n", i, j/3, x, locate_out);
                result[locate_out] = avg;
                for (short idx = 7; idx >= 0; idx--) {
                    // TODO: buggy when casting locate_out to uchar
                    write_a_bit(outptr + (unsigned char) locate_out, get_a_bit(avg, idx), idx);
                }
            }
        }
        int pad_bytes = w_resized * 3 % 4 == 0 ? 0 : 4 - (w_resized * 3 % 4);
        for (int idx = w_resized * 3; idx < w_resized * 3 + pad_bytes; idx++) {
            // write_a_bit(outptr + (unsigned char)i*w_bytes_resized + h_resized, 0, idx);
            result[i * w_bytes_resized + idx] = 0;
            printf("zero-pad %d\n", i * w_bytes_resized + idx);
            // locate = i * w_bytes_resized + idx
        }
    }
    for (int i=0; i<12; i++) {
        printf("0x%04x ", result[i]);
    }
    printf("\n");
    for (int i=12; i<24; i++) {
        printf("0x%04x ", result[i]);
    }
    printf("\n");
    for (int i=24; i<36; i++) {
        printf("0x%04x ", result[i]);
    }
    printf("\n");
}

int main() {
    unsigned char imgptr[] = {0x00, 0x00, 0x00, 0x35, 0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                              0x35,  0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x35, 0xf2, 0xfb, 0x0a, 0x6a, 0xfa, 0x0a, 0x6a, 0xfa, 0x00, 0x00, 0x00, 0x00, 0x00,
                              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x35, 0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

    unsigned char outptr[24] = {0,}; // dummy

    bmpresize(imgptr, 4, 6, 1, outptr);

    return 0;
}
