//---------------------------------------------------------------
//
//  4190.308 Computer Architecture (Fall 2022)
//
//  Project #1:
//
//  September 6, 2022
//
//  Seongyeop Jeong (seongyeop.jeong@snu.ac.kr)
//  Jaehoon Shim (mattjs@snu.ac.kr)
//  IlKueon Kang (kangilkueon@snu.ac.kr)
//  Wookje Han (gksdnrwp@snu.ac.kr)
//  Jinsol Park (jinsolpark@snu.ac.kr)
//  Systems Software & Architecture Laboratory
//  Dept. of Computer Science and Engineering
//  Seoul National University
//
//---------------------------------------------------------------

typedef unsigned char u8;

/* TODO: Implement this function */
void write_a_bit(u8* dst, u8 value, int idx) {
    // dst: start pointer
    // idx: index of bit
    int bit_size = sizeof(u8);
    if (value != 0 && value != 1) return;

    if (value == 0) {
        *(dst + idx/bit_size) &= 1 << ~(bit_size - (idx % bit_size));
        // example
        // 1 to 0, idx = 5
        // 0111 1111 -> 0111 0111
        // 0111 1111 AND 1111 0111 (mask)
        // 0111 1111 AND (NOT 0000 1000)
        // 0111 1111 AND (NOT 1<<3)
        // 0111 1111 AND (NOT 1<<8-idx)
    }
    else {
        *(dst + idx/bit_size) |= 1 << (bit_size - (idx % bit_size));
        // 0 to 1, idx = 5
        // 0111 0111 -> 0111 1111
        // 0111 0111 OR 0000 1000 (mask)
        // 0111 0111 OR (1<<3)
        // 0111 0111 OR (1<<8-idx)
    }
}

u8 get_a_bit (u8 value, int idx) {
    int bit_size = sizeof(u8);
    return value >> (bit_size - idx) & 1;
    // example
    // 1000 1111 -> "1" (idx 5)
    // 1000 1111 >> 3 AND 1
    // 0001 0001 AND 1
    // 1

}
int encode(const u8* src, int width, int height, u8* result) {
    if (width==0 || height==0) {
        return 0;
    }
    // phase 1
    int locate, cnt, sum, avg, filter;
    int base, n, max_delta, max_filter;
    for (int i=0; i<height; i++) {
        base = 0;
        n = 0;
        max_delta = 0;
        max_filter = 0;
        for (int j=0; j<width; j++) { // calculate the base
            // 1. finding average of three neighboring pixels
            locate = i*width + j;
            cnt = 0;
            sum = 0;
            avg = 0;
            filter = 0;
            if (i-1 >= 0) { // upper
                sum += *(src + locate-width);
                cnt++;
            }
            if (j-1 >= 0) { // left
                sum += *(src + locate-1);
                cnt++;
            }
            if (i-1 >= 0 && j-1 >= 0) { // upper-left
                sum += *(src + locate-width-1);
                cnt++;
            }
            if (cnt != 0) {
                avg = sum / cnt;
            }

            // 2. get the filtered value

            // cannot save the filtered value or delta
            // need to calculate it whenever need
            if (*(src+locate) >= avg) {
                filter = *(src+locate) - avg;
            }
            else {
                filter = *(src+locate) + 256 - avg;
            }

            // 3. calculate the base and max_delta
            if (base > filter) base = filter;
            if (max_filter < filter) max_filter = filter;
        }

        // 4. Find the number of bits needs for representing the delta
        max_delta = max_filter - base;
        if (max_delta == 0) n=0;
        else if (max_delta == 1) n=1;
        else if (max_delta < 4) n=2;
        else if (max_delta < 8) n=3;
        else if (max_delta < 16) n=4;
        else if (max_delta < 32) n=5;
        else if (max_delta < 64) n=6;
        else if (max_delta < 128) n=7;
        else n=8;

        // 5. encode the row
        int idx = 0;
        for (int k=idx; k<idx+8; k++) { // base
            write_a_bit(result, get_a_bit(base, k), k);
        }
        idx += 8;
        for (int k=idx; k<idx+4; k++) { // base
            write_a_bit(result, get_a_bit(n, k), k);
        }
        idx += 4;

        int delta = 0;
        for (int j=0; j<width; j++) {
            for (int k=idx; k<idx+n; k++) {
                locate = i*width + j; // calculate delta again
                cnt = 0;
                sum = 0;
                avg = 0;
                filter = 0;
                delta = 0;
                if (i-1 >= 0) { // upper
                    sum += *(src + locate-width);
                    cnt++;
                }
                if (j-1 >= 0) { // left
                    sum += *(src + locate-1);
                    cnt++;
                }
                if (i-1 >= 0 && j-1 >= 0) { // upper-left
                    sum += *(src + locate-width-1);
                    cnt++;
                }
                if (cnt != 0) {
                    avg = sum / cnt;
                }

                if (*(src+locate) >= avg) {
                    filter = *(src+locate) - avg;
                }
                else {
                    filter = *(src+locate) + 256 - avg;
                }
                delta = filter - base;
                write_a_bit(result, get_a_bit(delta, k), k);
            }
            idx += n;
        }

    }







  return 0;
}



