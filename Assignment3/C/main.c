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
    int scaling_factor = (int) pow(2, k);
    int h_resized = h / scaling_factor;
    int w_resized = w / scaling_factor;
    int w_bytes = 3*w % 4 == 0 ? 3*w : ((3*w)/4) * 4 + 4;
    int w_bytes_resized = 3*w_resized % 4 == 0 ? 3*w_resized : ((3*w_resized)/4) * 4 + 4;
    unsigned char avg_b, avg_g, avg_r = 0;
    int sum_b, sum_g, sum_r = 0;
    int locate = 0;
    int locate_out = 0;
    for (int i=0; i<h_resized; i++) {
        for (int j=0; j<w_resized*3; j=j+3) {
            sum_b = 0;
            sum_g = 0;
            sum_r = 0;

            // b g r 세트 말고, 하나씩 따로 움직이도록 바꿀것

            // locate = i*scaling_factor*w_resized + j*scaling_factor; // start address of the original large pixels
            // i=0, j=0
            // m = 0, 1
            // n = 0, 4
            // n = 0*2^1 = 0
            // n < 3*2^1 = 6


            for (int m=i*scaling_factor; m<(i+1)*scaling_factor; m++) {
                for (int n=j*scaling_factor; n<(j+3)*scaling_factor; n=n+3) {

                    locate = m*w_bytes + n;

                    // real_locate = 

                    sum_b += *(imgptr + locate);
                    sum_g += *(imgptr + locate+1);
                    sum_r += *(imgptr + locate+2);
                    // printf("%d %d %d\n", m, n, locate);
                    // printf("value: %d %d %d\n", *(imgptr + locate), *(imgptr + locate+1), *(imgptr + locate+2));
                }
                // printf("\n");
            }
            // printf("sum: %d %d %d\n", sum_b, sum_g, sum_r);
            avg_b = sum_b / (scaling_factor*scaling_factor);
            avg_g = sum_g / (scaling_factor*scaling_factor);
            avg_r = sum_r / (scaling_factor*scaling_factor);
            locate_out = i*w_bytes_resized + j;
            // printf("avg: %d %d %d i: %d j: %d\n", avg_b, avg_g, avg_r, i, j);
            // printf("write at %d\n\n",locate_out);
            for (short idx=7; idx>=0; idx--) {
                // TODO: Logic is fine but some bug in writing ?
                write_a_bit(outptr + locate_out, get_a_bit(avg_b, idx), idx);
                write_a_bit(outptr + locate_out + 1, get_a_bit(avg_g, idx), idx);
                write_a_bit(outptr + locate_out + 2, get_a_bit(avg_r, idx), idx);
            }

        }
        int pad_bytes = w_resized*3 % 4 == 0 ? 0 : 4 - (w_resized*3 % 4);
        for (int idx=0; idx<pad_bytes; idx++) {
            write_a_bit(outptr + i*w_bytes_resized + h_resized, 0, idx);
        }
    }

}

int main() {
    unsigned char imgptr[] = {0x00, 0x00, 0x00, 0x35, 0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                              0x35,  0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x35, 0xf2, 0xfb, 0x0a, 0x6a, 0xfa, 0x0a, 0x6a, 0xfa, 0x00, 0x00, 0x00, 0x00, 0x00,
                              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x35, 0xf2, 0xfb, 0x35, 0xf2, 0xfb, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

    unsigned char outptr[24] = {0,};
    bmpresize(imgptr, 4, 6, 1, outptr);
    for (int i=0; i<2; i++) {
        for (int j=0; j<12; j++) {
            printf("0x%04x ", outptr[i*3+j]);
        }
        printf("\n");
    }

    return 0;
}
