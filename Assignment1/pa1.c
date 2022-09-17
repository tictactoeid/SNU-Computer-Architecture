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
    /*
    *(dst + idx / BITS_PER_UNIT) &= ~(1<<(idx%BITS_PER_UNIT));
    *(dst + idx / BITS_PER_UNIT) |= (value <<(idx%BITS_PER_UNIT));
     * */

    // dst: start pointer
    // idx: index of bit
    int bit_size = sizeof(u8)*8;
    if (value != 0 && value != 1) return;
    /*
    *(dst + idx/bit_size) &= ~(1 << (bit_size - (idx % bit_size)));
    *(dst + idx/bit_size) |= value << (bit_size - (idx % bit_size));
    */

    if (value == 0) {
        *(dst + idx/bit_size) &= ~(1 << (bit_size-1 - (idx % bit_size)));
        // example
        // 1 to 0, idx = 4
        // 0111 1111 -> 0111 0111
        // 0111 1111 AND 1111 0111 (mask)
        // 0111 1111 AND (NOT 0000 1000)
        // 0111 1111 AND (NOT 1<<3)
        // 0111 1111 AND (NOT 1<<8-idx)
    }
    else {
        *(dst + idx/bit_size) |= 1 << (bit_size-1 - (idx % bit_size));
        // 0 to 1, idx = 5
        // 0111 0111 -> 0111 1111
        // 0111 0111 OR 0000 1000 (mask)
        // 0111 0111 OR (1<<3)
        // 0111 0111 OR (1<<8-idx)
    }
}

int get_a_bit (int value, int dgt) {
    return (value & (1 << dgt)) >> dgt;
    // example
    // 1000 1111 -> "1" (dgt 3)
    // 1000 1111 AND 0000 0001<<3
    // 1000 1111 AND 0000 1000
    // 0000 1000
    // 0000 1000 >> 3
    // 1
}

int encode(const u8* src, int width, int height, u8* result) {
    /*
    for (int k=0; k<8; k++) { // base
        write_a_bit(result, get_a_bit( 9, 7-k), k);
    }
    return 8;


    write_a_bit(result, 1, 0);
    write_a_bit(result, 1, 1);
    write_a_bit(result, 1, 2);
    write_a_bit(result, 1, 3);
    write_a_bit(result, 1, 4);
    write_a_bit(result, 1, 5);
    write_a_bit(result, 1, 6);
    write_a_bit(result, 1, 7);
    return 8;
    */


    int idx = 0;
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
            if (j==0) {
                base = filter;
                max_filter = filter;
            }

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

        for (int k=0; k<8; k++) { // base
            write_a_bit(result, get_a_bit(base, 7-k), idx+k);
        }
        idx += 8;
        for (int k=0; k<4; k++) { // base
            write_a_bit(result, get_a_bit(n, 3-k), idx+k);
        }
        idx += 4;

        int delta = 0;
        for (int j=0; j<width; j++) {
            for (int k=0; k<n; k++) {
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
                write_a_bit(result, get_a_bit(delta, n-1-k), idx+k);
            }
            idx += n;
        }

    }
    // 6. padding
    if (idx%8==0) return idx/8;
    for (int i=0; i<8-idx%8; i++){
        write_a_bit(result, 0, idx+i);
    }
    return idx/8+1;

}



