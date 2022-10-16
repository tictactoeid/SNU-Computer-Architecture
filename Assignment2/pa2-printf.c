// ----------------------------------------------------------------
// 
//   4190.308 Computer Architecture (Fall 2022)
// 
//   Project #2: SFP16 (16-bit floating point) Adder
// 
//   October 4, 2022
// 
//   Seongyeop Jeong (seongyeop.jeong@snu.ac.kr)
//   Jaehoon Shim (mattjs@snu.ac.kr)
//   IlKueon Kang (kangilkueon@snu.ac.kr)
//   Wookje Han (gksdnrwp@snu.ac.kr)
//   Jinsol Park (jinsolpark@snu.ac.kr)
//   Systems Software & Architecture Laboratory
//   Dept. of Computer Science and Engineering
//   Seoul National University
// 
// ----------------------------------------------------------------

#include <stdio.h> // TODO

typedef unsigned short SFP16;
#define bias (short) 63

/* Add two SFP16-type numbers and return the result */

// typedef unsigned char u8;

// from assignment 1
SFP16 write_a_bit(SFP16 bits, short value, short idx) { // ok
    if (value != 0 && value != 1) return bits;
    short bit_size = sizeof(SFP16)*8;
    if (idx<0 || idx>=bit_size) return bits;

    if (value == 0) {
        return bits & ~((unsigned short) 1 << idx);
    }
    else {
        return bits | ((unsigned short) 1 << idx);
    }
}

SFP16 get_a_bit (SFP16 value, short idx) { // ok
    if (idx<0 || idx>=16) return 0;
    // 15 14 13 12 11 10 9  8  7  6  5  4  3  2  1  0
    return (value & ((unsigned short) 1 << idx)) >> idx;
}

/* short get_a_bit (short value, short dgt) {
    // 7654 3210 : dgt
    // 0000 1000 -> "1" (dgt 3)
    return (value & (1 << dgt)) >> dgt;
} */

// 15 14 13 12 11 10 9  8  7  6  5  4  3  2  1  0
// S  E  E  E  E  E  E  E  F  F  F  F  F  F  F  F

unsigned short get_fraction(SFP16 value) { // ok
    return ((unsigned short) value & 255);
}

unsigned short get_unsigned_exponent(SFP16 value) { // ok
    return ((value & ((unsigned short) 127 << 8)) >> 8);
}

short unsigned_exp_to_signed(unsigned short e) {
    //e to E
    if (e==0) return 1-bias; // denormalized form : exp = 000 0000
    else return e-bias;
}

signed short get_signed_exponent(SFP16 value) {
    return unsigned_exp_to_signed(get_unsigned_exponent(value));
}

unsigned short get_sign(SFP16 value) { // ok
    return (value & ((unsigned short) 1 << 15)) >> 15;
}

short check_NaN_or_not(SFP16 value) {
    // NaN : exp = 111 1111, frac != 0000 0000
    // frac will be 0b00000001 for NaN in this project
    if (value == 0x7f01 || value == 0xff01) return 1;
    return 0;
}

short check_inf_or_not(SFP16 value) {
    // returns 1 if value is +inf, -1 if -inf, otherwise 0
    // inf: exp = 111 1111, frac = 0000 0000
    if (value == 0x7f00) return 1;
    if (value == 0xff00) return -1;
    return 0;
}

short compare(SFP16 x, SFP16 y) {
    // return 0 if x==y
    // return positive if x>y
    // return negative if x<y
    // TODO: consider NaN, inf, sign
    if (get_sign(x) != get_sign(y)){
        if (get_unsigned_exponent(x) == 0 && get_fraction(x) == 0 && get_unsigned_exponent(y) == 0 && get_fraction(y) == 0) {
            // -0 == +0
            return 0;
        }
        return get_sign(y) - get_sign(x);
        // sign = 1 is smaller than sign = 0
    }

    if (get_sign(x) == 1 && get_sign(y) == 1) {
        if (get_unsigned_exponent(y) != get_unsigned_exponent(x)){
            return get_unsigned_exponent(y) - get_unsigned_exponent(x);
        }

        return get_fraction(x) - get_fraction(y);
    }

    if (get_unsigned_exponent(x) != get_unsigned_exponent(y)){
        return get_unsigned_exponent(x) - get_unsigned_exponent(y);
    }

    return get_fraction(x) - get_fraction(y);
}

short compare_abs(SFP16 x, SFP16 y) {

    if (get_sign(x) == 0 && get_sign(y) == 0) return compare(x, y);
    if (get_sign(x) == 1 && get_sign(y) == 1) return compare(y, x);
    if (get_unsigned_exponent(x) != get_unsigned_exponent(y)) {
        return get_unsigned_exponent(x) - get_unsigned_exponent(y);
    }

    return get_fraction(x) - get_fraction(y);
}

SFP16 shift_right_M(SFP16 M, short d) { // ok


    // only for step 2

    // shifts right (16-bits extended) M d bits, and updates GRS

    // d = 5
    // ----1FFF FFFFFGRS
    // -------- -1FFFFFFFF
    //               GRSSS => d bits will be truncated / 1 G, 1 R, (d-2) Sticky

    if (d>=16) return 0x0000;

    short s = 0;
    for (short i=3; i<=d; i++){
        if (get_a_bit(M, i)==1) {
            s = 1;
            break;
        }
    }
    M = M >> d; // shift right, update G, R automatically
    // My = write_a_bit(My, 1, 10-d);
    M = write_a_bit(M, s, 0); // update S
    // TODO: consider denormalized values
    // TODO: consider shifting more than 16 bits

    // -----1FF FFFFFFGRS
    // -----001 FFFFFFGRS if d==2, last three bits becomes new GRS

    return M;
}

short normalize(SFP16 *M, short E) {
    // E = exp - bias (norm)
    // E = 1 - bias (denorm), exp = 0
    // 1-bias <= E <= 127-bias
    if (E==0) return 0;
    short d = 0;
    for (short i=15; i>=0; i--) {
        if (i>11 && get_a_bit(*M,i) == 1) { // shift right
            d = i-11;
            if (E+d > 127-bias) {
                // TODO
                // E out of range
                // result will be a special value
                return E;
            }
            unsigned char G, R, S;
            G = get_a_bit(*M, 3);
            R = get_a_bit(*M, 2);
            S = get_a_bit(*M, 1) || get_a_bit(*M, 0);
            *M = *M >> d;
            E += d;
            *M = write_a_bit(*M, G, 2);
            *M = write_a_bit(*M, R, 1);
            *M = write_a_bit(*M, S, 0);
            break;
        }
        if (i==11 && get_a_bit(*M, i) == 1) break; // already done!

        if (i<11 && get_a_bit(*M, i) == 1) { // shift left
            d = -(11-i);
            if (E+d < 1-bias) {
                // result will be denormalized form
                d = 1-bias - E; // makes exp = 000 0000
            }

            *M = *M << -d;
            E += d;
            break;
        }
    }
    return E;
    // shifted left if d is negative
    // shifted right if d is positive
}

SFP16 fpadd(SFP16 x, SFP16 y) {
    /* TODO */

    // check for special values
    if (check_NaN_or_not(x) == 1 || check_NaN_or_not(y) == 1) return 0x7f01; // x or y is NaN
    if (check_inf_or_not(x)!=0 || check_inf_or_not(y)!=0) {
        switch (check_inf_or_not(x)) {
            case 1:
                switch (check_inf_or_not(y)) {
                    case -1:
                        return 0x7f01;
                    case 0:
                        return x;
                    case 1:
                        return x;
                }
            case 0:
                switch (check_inf_or_not(y)) {
                    case -1:
                        return y;
                    case 0:
                        break;
                    case 1:
                        return y;
                }
            case -1:
                switch (check_inf_or_not(y)) {
                    case -1:
                        return x;
                    case 0:
                        return x;
                    case 1:
                        return 0x7f01;
                }
        }
    }


    // step 1
    if (compare_abs(x, y) < 0) {
        return fpadd(y, x);
    }

    if (get_signed_exponent(x) - get_signed_exponent(y) > 15) return x;

    // step 2
    // ok (for normalized)
    unsigned short Mx = 0 | (get_fraction(x) << 3);
    unsigned short My = 0 | (get_fraction(y) << 3);
    if (get_unsigned_exponent(x) != 0)  Mx = write_a_bit(Mx, 1, 11);
    if (get_unsigned_exponent(y) != 0) My = write_a_bit(My, 1, 11);
    // TODO: consider denormalized values
    // extended to 16 bits
    // 1.FFFFFFFF => ----1FFF FFFFFGRS : -'s are wasted bits, initially 0

    printf("before shift, My: ");
    printf("0x%04x\n", My);

    short d = get_signed_exponent(x) - get_signed_exponent(y);
    My = shift_right_M(My, d);

    printf("after step 2: ");
    printf("0x%04x %d shifted %d\n", My, get_signed_exponent(x), d);

    // step 3
    unsigned short M = 0;
    short E = get_signed_exponent(x);
    if (get_sign(x) == get_sign(y)) M = Mx+My;
    else M = Mx-My;

    printf("after step 3: ");
    printf("0x%04x %d\n", M, E);

    // step 4
    E = normalize(&M, E);

    printf("after step 4: ");
    printf("0x%04x %d\n", M, E);

    // step 5
    short L_adjusted, R_adjusted, S_adjusted;
    L_adjusted = get_a_bit(M, 3);
    R_adjusted = get_a_bit(M, 2);
    S_adjusted = (get_a_bit(M, 1)==0 && get_a_bit(M, 0)==0) ? 0 : 1;


    M = M>>3; // truncate old GRS
    if (R_adjusted==1 && S_adjusted == 1) {
        M++; // round up;
        printf("round-up\n");
    }
    else if (L_adjusted==1 && R_adjusted==1 && S_adjusted==0) {
        M++; // round up;
        printf("round-up\n");
    }

    // -------1 FFFFFFFF
    printf("after step 5: ");
    printf("0x%04x %d\n", M, E);

    if (E == 64) {
        if (get_sign(x) == 0) return 0x7F00; // +inf
        return 0xFF00; // -inf
    }

    /*if (E == 64) {
        if (M == 0x0100 && get_sign(x) == 0) {
            return 0x7F00; // +inf
        }
        else if (M == 0x0100 && get_sign(x) == 1) {
            return 0xFF00; // -inf
        }
        else return 0xFF01; // NaN
    } */

    // step 6
    // E += normalize(&M);

    if (get_a_bit(M, 9) == 1) { // re-normalize
        // cannot use normalize() because now there are no GRS bits in M
        M = M >> 1; // normalize 10.xxx => 1.0xx
        E++;
        printf("re-normed\n");
        // TODO: result becomes special value?
    }

    // there's no round-"up" twice
    // 1.xxx0 -> round-up -> 1.xxx1 (no re-normalization)
    // 1.xxx1 -> round-up -> may be 10.xx0 -> 1.0xx / 0 discards (round-down)
    printf("after step 6: ");
    printf("0x%04x %d\n", M, E);

    // step 7
    if (E == 64) {
        if (get_sign(x) == 0) return 0x7F00; // +inf
        return 0xFF00; // -inf
    }
    /* if (E == 64) {
        if (M == 0x0100 && get_sign(x) == 0) {
            return 0x7F00; // +inf
        }
        else if (M == 0x0100 && get_sign(x) == 1) {
            return 0xFF00; // -inf
        }
        else return 0xFF01; // NaN
    } */

    printf("%d %d 0x%04x\n", get_sign(x), E, M);

    SFP16 res = 0;
    res = write_a_bit(res, get_sign(x), 15);  // Sign == sign(x)

    for (short i=0; i<7; i++) {
        if (M >= 0x0100) { // M = -------- FFFFFFFF, M has leading 1, normalized form
            res = write_a_bit(res, get_a_bit((SFP16) (E+bias), i), i+8);
        }
        else { // denormalized form
            res = write_a_bit(res, get_a_bit(0, i), i+8);
        }
        // TODO: how can I know if the result is normalized or denormalized?  ==>  M has leading 1 or not
    }
    for (short i=0; i<8; i++) {
        res = write_a_bit(res, get_a_bit(M, i), i);
    }


    return res;
}
