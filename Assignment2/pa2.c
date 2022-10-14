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

typedef unsigned short SFP16;
#define bias 63

/* Add two SFP16-type numbers and return the result */

// typedef unsigned char u8;

// from assignment 1
SFP16 write_a_bit(SFP16 bits, int value, int idx) {
    if (value != 0 && value != 1) return bits;
    int bit_size = sizeof(SFP16)*8;
    if (idx<0 || idx>=bit_size) return bits;

    if (value == 0) {
        return bits & (0 << idx);
    }
    else {
        return bits | (1 << idx);
    }
}

int get_a_bit (SFP16 value, int idx) {
    // 15 14 13 12 11 10 9  8  7  6  5  4  3  2  1  0
    return (value & (1 << idx)) >> idx;
}

/* int get_a_bit (int value, int dgt) {
    // 7654 3210 : dgt
    // 0000 1000 -> "1" (dgt 3)
    return (value & (1 << dgt)) >> dgt;
} */

// 15 14 13 12 11 10 9  8  7  6  5  4  3  2  1  0
// S  E  E  E  E  E  E  E  F  F  F  F  F  F  F  F

int get_fraction(SFP16 value) {
    return (value & 255);
}

int get_exponent(SFP16 value) {
    return ((value & (127 << 8)) >> 8) - bias;
}

int get_sign(SFP16 value) {
    return (value & (1 << 15)) >> 15;
}

int compare(SFP16 x, SFP16 y) {
    // return 0 if x==y
    // return positive if x>y
    // return negative if x<y
    // TODO: consider NaN, inf, sign
    if (get_sign(x) != get_sign(y)){
        if (get_exponent(x) == -bias && get_fraction(x) == 0 && get_exponent(y) == -bias && get_fraction(y) == 0) {
            // -0 == +0
            return 0;
        }
        return get_sign(y) - get_sign(x);
        // sign = 1 is smaller than sign = 0
    }

    if (get_exponent(x) != get_exponent(y)){
        return get_exponent(x) - get_exponent(y);
    }

    return get_fraction(x) - get_fraction(y);
}

int compare_abs(SFP16 x, SFP16 y) {
    if (get_sign(x) == 0 && get_sign(y) == 0) return compare(x, y);
    if (get_sign(x) == 1 && get_sign(y) == 1) return compare(y, x);
    if (get_exponent(x) != get_exponent(y)) {
        return get_exponent(x) - get_exponent(y);
    }

    return get_fraction(x) - get_fraction(y);
}

SFP16 shift_right_M(SFP16 M, int d) {
    // shifts right (16-bits extended) M d bits, and updates GRS

    // d = 5
    // ----1FFF FFFFFGRS
    // -------- -1FFFFFFFF
    //               GRSSS => d bits will be truncated / 1 G, 1 R, (d-2) Sticky
    int s = 0;
    for (int i=3; i<=d; i++){
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

SFP16 fpadd(SFP16 x, SFP16 y) {
  /* TODO */
  // step 1
  if (compare_abs(x, y) < 0) return fpadd(y, x);

  // step 2
  unsigned short Mx = 0 | (get_fraction(x) << 3);
  unsigned short My = 0 | (get_fraction(y) << 3);
  Mx = write_a_bit(Mx, 1, 11);
  My = write_a_bit(My, 1, 11);
  // TODO: consider denormalized values
  // extended to 16 bits
  // 1.FFFFFFFF => ----1FFF FFFFFGRS : -'s are wasted bits, initially 0

  int d = get_exponent(x) - get_exponent(y);
  My = shift_right_M(My, d);





  // step 3
  unsigned short M = 0;
  int E = get_exponent(x);
  if (get_sign(x) == get_sign(y)) M = Mx+My;
  else M = Mx-My;

  // step 4

  // shift right
  if (get_a_bit(M,15) == 1) {
      M = shift_right_M(M, 4);
      E = E+4;
  }
  else if (get_a_bit(M, 14) == 1) {
      M = shift_right_M(M, 3);
      E = E+3;
  }
  else if (get_a_bit(M, 13) == 1) {
      M = shift_right_M(M, 2);
      E = E+2;
  }
  else if (get_a_bit(M, 12) == 1) {
      M = shift_right_M(M, 1);
      E = E+1;
  }
  // get_a_bit(M, 11) == 1 do nothing
  else { // shift left
      for (int i=10; i>=0; i--) {
          if (get_a_bit(M, i) == 1) {
              M = M << (11-i);
              E = E-(11-i);
              break;
          }
      }
  }

  // step 5
  if (get_a_bit(M, 2) == 1) { // adjusted R (previous G) == 1
      if ((get_a_bit(M, 1) | get_a_bit(M, 0)) == 0 || get_a_bit(M, 3) == 1) { // L==1 or S==1
          M >> 3; // truncate old GRS
          M++; // round up;
      } else M>>3;
  } else M>>3;
  // -------1 FFFFFFFF

  // step 6
  if (get_a_bit(M, 9) == 1) { // re-normalize
      M >> 1; // normalize 10.xxx => 1.0xx
      E++;
  }

  // there's no round-"up" twice
  // 1.xxx0 -> round-up -> 1.xxx1 (no re-normalization)
  // 1.xxx1 -> round-up -> may be 10.xx0 -> 1.0xx / 0 discards (round-down)

  // step 7
  SFP16 res = 0;
  res = write_a_bit(res, 15, get_a_bit(x, 15));  // Sign == sign(x)
  for (int i=0; i<7; i++) {
      res = write_a_bit(res, i+8, get_a_bit((SFP16) (E+bias), i));
  }
  for (int i=0; i<8; i++) {
      res = write_a_bit(res, i, get_a_bit(M, i));
  }

  return res;
}
