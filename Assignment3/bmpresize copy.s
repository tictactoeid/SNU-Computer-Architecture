#----------------------------------------------------------------
#
#  4190.308 Computer Architecture (Fall 2022)
#
#  Project #3: Image Resizing in RISC-V Assembly
#
#  November 20, 2022
# 
#  Seongyeop Jeong (seongyeop.jeong@snu.ac.kr)
#  Jaehoon Shim (mattjs@snu.ac.kr)
#  IlKueon Kang (kangilkueon@snu.ac.kr)
#  Wookje Han (gksdnrwp@snu.ac.kr)
#  Jinsol Park (jinsolpark@snu.ac.kr)
#  Systems Software & Architecture Laboratory
#  Dept. of Computer Science and Engineering
#  Seoul National University
#
#----------------------------------------------------------------

####################
# void bmpresize(unsigned char *imgptr, int h, int w, int k, unsigned char *outptr)
####################

# a0 imgptr(0x8001003c), a1 h, a2 w, a3 k, a4 outptr(0x80018000)
# x0, sp(0x80017ffc), ra, a0 a1 a2 a3 a4, t0 t1 t2 t3 t4

	.globl bmpresize
bmpresize:

	#addi sp, sp, 200
	#sw a0, 4(sp)
	#ebreak

	addi sp, sp, -20
	sw a0, 16(sp) #imgptr
	sw a1, 12(sp) #h
	sw a2, 8(sp) #w
	sw a3, 4(sp) #k
	sw a4, 0(sp) #outptr
	
	# imgptr h w k outptr(sp)
	addi t0, x0, 1
	sll t0, t0, a3
	# t0 = 2 ** k
	addi sp, sp, -4
	sw t0, 0(sp)
	# imgptr h w k outptr scaling_factor(sp)
	

	mv t0, a1
	mv t1, a2
	srl t0, t0, a3
	srl t1, t1, a3
	addi sp, sp, -8
	sw t0, 4(sp) # h/2^k
	sw t1, 0(sp) # w/2^k
	# imgptr h w k outptr scaling_factor h/2^k w/2^k(sp)

	lw t3, 20(sp) # t3 = w_r
	mv t0, t3
	slli t3, t3, 1 
	add t3, t0, t3 # t3 = w*3
	mv t1, t3 # w*3
	srli t1, t1, 2 # w*3 / 4
	slli t1, t1, 2 # t1 = w*3 / 4 * 4

	sub t2, t3, t1 # t2 = w*3 % 4	
	beq t2, x0, L1 # w_bytes = 3*w if 3*w % 4 == 0
	addi t3, t1, 4 # else ((3*w)/4) * 4 + 4 : t1 + 4

L1:
	
	addi sp, sp, -4
	sw t3, 0(sp)
	# imgptr h w k outptr scaling_factor h/2^k w/2^k w_bytes(sp)
	lw t0, 4(sp) #w_resized

	mv t3, t0
	slli t3, t3, 1
	add t3, t3, t0 # t3 = 3*w_r

	mv t1, t3
	srl t1, t1, 2 
	slli t1, t1, 2 # t1 = w_r*3 / 4 *4
	sub t2, t3, t1 # t2 = w_r*3 % 4

	beq t2, x0, L2 # w_bytes_resized = 3*wr if 3*wr % 4 == 0
	addi t3, t1, 4 # else ((3*wr)/4) * 4 + 4 : t1 + 4

L2:
	addi sp, sp, -4
	sw t3, 0(sp)
	# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
	mv t0, x0 # avg

	# sp = 0x80017fd4

	# ------------------------- Init Variables --------------------------------

	# Init - For1
	addi sp, sp, -4
	sw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a1(sp)
	lw a1, 16(sp) # h/2^k
	addi a0, a1, -1 # a0 : h_resized - 1 initially
	lw a1, 0(sp)
	addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)

For1: # loop with i : use a0 = h/2^k-1 - i
	blt a0, x0, ForExit1

	# Body - For1
		# Init - For2
		addi sp, sp, -8
		sw a3, 4(sp)
		sw a2, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a3 a2(sp)
		lw a2, 16(sp) # w/2^k

		mv a3, a2
		slli a3, a3, 1
		add a2, a3, a2 # a2 = w/2^k *3

		addi a1, a2, -1 # init a1: a1=w_r*3-1; a1>=0; a1-=3
		
		lw a3, 4(sp)
		lw a2, 0(sp)
		addi sp, sp, 8 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
	

	For2: # loop with j : use a1(j)
		
		#bge a1, a2, ForExit2
		blt a1, x0, ForExit2
		#Body - For2
		addi a2, x0, 2 # Init - For3
			
		For3: # loop with x : use a2(2-x): 2, 1, 0
			blt a2, x0, ForExit3
			#Body - For3			
			mv t0, x0 # avg = 0
				# Init - For4
				lw a3, 16(sp) # scaling factor, 2^k
				mv t2, a3

				addi sp, sp, -12
				sw t0, 8(sp)
				sw t1, 4(sp)
				sw t4, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t0 t1 t4(sp)

				lw t1, 24(sp)
				addi t1, t1, -1
				sub t1, t1, a0 # i = h/2^k-1 - a0
				# mv t1, a0 
				mv t0, x0
				mv t4, x0
				Multiple1: #mul a3, a3, i # m = i * scaling_factor		
					bge t0, t1, MultipleExit1
					add t4, t4, a3 # t4 += sf
					addi t0, t0, 1
					blt t0, t1, Multiple1

				MultipleExit1:
					mv a3, t4
				
				lw t0, 8(sp)
				lw t1, 4(sp)
				lw t4, 0(sp)
				addi sp, sp, 12 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
				add t2, t2, a3 # (i + 1) * scaling_factor / sf + i*sf
				
			For4: # a3(m), t2				
				bge a3, t2, ForExit4

					#Init - For5
					lw a4, 16(sp)
					mv t3, a4 # sf
					slli t3, t3, 1 # 2*sf
					add t3, t3, a4 # 3*sf					

					addi sp, sp, -12
					sw t0, 8(sp)
					sw t1, 4(sp)
					sw t2, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t0 t1 t2(sp)
					
					lw t1, 20(sp) # w_r
					mv t0, t1
					slli t0, t0, 1 
					add t1, t0, t1 # 3*w_r
					addi t1, t1, -1
					sub t1, t1, a1 # t1: j = w_resized*3 - 1 - a1
					mv t0, x0
					mv t2, x0
					Multiple2: # mul a4, a4, j
						bge t0, t1, MultipleExit2
						add t2, t2, a4 # t2 += a4
						addi t0, t0, 1 # j times
						blt t0, t1, Multiple2
					MultipleExit2:
						mv a4, t2 # j * scaling_factor
					
					lw t0, 8(sp)
					lw t1, 4(sp)
					lw t2, 0(sp)
					addi sp, sp, 12 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)					
					add t3, t3, a4 # (j+3) * scaling_factor	
				 
				For5: # a4(n), t3
					bge a4, t3, ForExit5
					nop
					# load and compute avg

					# t1, t4 : free
					# t0 : avg
					# t2, t3 : for loop

					# locate = m * w_bytes + n+x // for load value

					lw t1, 4(sp) # w_bytes
				

					addi sp, sp, -12
					sw t0, 8(sp)
					sw t2, 4(sp)
					sw t3, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t0 t2 t3(sp)

					mv t0, x0
					mv t2, a3
					mv t3, x0
					Multiple3: # mul t1, t1, a3 # *m
						bge t0, t2, MultipleExit3
						add t3, t3, t1
						addi t0, t0, 1
						blt t0, t2, Multiple3
					MultipleExit3:
						mv t1, t3					
					lw t0, 8(sp)
					lw t2, 4(sp)
					lw t3, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
					addi sp, sp, 12

					add t1, t1, a4 # +n

					addi sp, sp, -4
					sw a0, 0(sp)
					addi a0, x0, 2
					sub a0, a0, a2 # a2 = 2-x, a0 = x
					add t1, t1, a0
					lw a0, 0(sp)
					addi sp, sp, 4

					#+x
					# consider little endian
					mv t4, t1
					srli t4, t4, 2 # locate / 4
					slli t4, t4, 2 # locate/4 * 4

					addi sp, sp, -16
					sw t2, 12(sp)
					sw t3, 8(sp)
					sw a0, 4(sp)
					sw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a0 a1(sp)

					sub a0, t1, t4 # locate % 4
					
					lw a1, 52(sp) # imgptr
					
					add a1, a1, t4 # imgptr + locate/4*4
					lw a1, 0(a1) # load value - 4byte

					addi t2, x0, 3			
					sub t2, t2, a0		
					slli t2, t2, 3
					# 00000001 00000010 00000011 00000100
					
					# little endian : 33333333 22222222 11111111 00000000
					# locate % 4 = 0 ->24, 1->16, 2->8, 3->0 shift left
					# shift left (3 - locate%4) * 8
					sll a1, a1, t2 # ex) l%4 = 2, shift left 2, 22222222 11111111 00000000 00000000

					# 01020304 << 6					
					# shift right 24
					addi t3, x0, 24					
					srl a1, a1, t3 # a1: 0x00 00 00 value
					add t0, t0, a1 # avg += *(imgptr + locate);
					
					lw t2, 12(sp)
					lw t3, 8(sp)
					lw a0, 4(sp)
					lw a1, 0(sp)
					addi sp, sp, 16
					# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
										
					addi a4, a4, 3 # update for5
					blt a4, t3, For5
				ForExit5:
					nop
				addi a3, a3, 1 # update for4

				blt a3, t2, For4
				

			ForExit4:
				#lw t2, 0(sp)
				#addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
			lw t4, 24(sp) # k
			
			# stack pointer ok

			slli t4, t4, 1 #  2*k			
			srl t0, t0, t4 # avg /= (scaling_factor * scaling_factor);
			# locate_out = i * w_bytes_resized + (j+x);
				lw t1, 0(sp) # w_b_r

				addi sp, sp, -12
				sw t0, 8(sp)
				sw t2, 4(sp)
				sw t4, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t0 t2 t4(sp)

				lw t2, 24(sp)
				addi t2, t2, -1
				sub t2, t2, a0
				# mv t2, i # i = h/2^k-1 - a0
				mv t0, x0
				mv t4, x0
				Multiple4: # mul t1, t1, i
					bge t0, t2, MultipleExit4
					add t4, t4, t1 # t4 += w_b_r
					addi t0, t0, 1
					blt t0, t2, Multiple4

				MultipleExit4:
					mv t1, t4 # t1 = i * wbr

				lw t0, 8(sp)
				lw t2, 4(sp)
				lw t4, 0(sp)
				addi sp, sp, 12

			addi sp, sp, -8
			sw t3, 4(sp)
			sw t4, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t3 t4(sp)

			lw t3, 16(sp) # w/2^k
			slli t4, t3, 1 # w_r *2
			add t3, t3, t4 
			addi t3, t3, -1
			sub t3, t3, a1 # j = w_resized*3 - 1 - a1
			add t1, t1, t3 # t1 = i*wbr + j
 
			lw t3, 4(sp)
			lw t4, 0(sp)
			addi sp, sp, 8 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
			
			addi sp, sp, -4
			sw a0, 0(sp)
			addi a0, x0, 2
			sub a0, a0, a2 # a2 = 2-x, a0 = x
			add t1, t1, a0 # t1 = i*wbr + j + x = locate_out
			lw a0, 0(sp)
			addi sp, sp, 4
			mv t4, t1		

			srli t4, t4, 2
			slli t4, t4, 2 # locate/4 * 4					


			addi sp, sp, -16
			sw t2, 12(sp)
			sw t3, 8(sp)
			sw a0, 4(sp)
			sw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a0 a1(sp)

		
			sub a0, t1, t4 # locate % 4
			lw a1, 36(sp) # outptr		
			
			add a1, a1, t4 # out word address
			# locate_out = i * w_bytes_resized + (j+x);
			
			lw t2, 0(a1) # load value - 4byte
			
			
			slli t1, a0, 3
			
			/*
			# for test zero-masking
			addi t2, x0, 0
			not t2, t2 */
			
			# little endian : 33333333 22222222 11111111 00000000
			# 

			# 0x00 00 00 value -> shift left -> make t2 zero at that byte -> add t2(4byte) -> sw t2


			sll t0, t0, t1 # 0x00 value 00 00
			# shift left done	
			
			addi sp, sp, -12
			sw a1, 8(sp)
			sw a3, 4(sp)
			sw a4, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a0 a1 / a1 a3 a4(sp)

			beq a0, x0, Mask0
			addi a1, x0, 1
			beq a0, a1, Mask1
			addi a1, x0, 2
			beq a0, a1, Mask2
			j Mask3


		Mask0:
			li a3, 0xFFFFFF00
			j MaskEnd
		Mask1:
			li a3, 0xFFFF00FF
			j MaskEnd
		Mask2:
			li a3, 0xFF00FFFF
			j MaskEnd
		Mask3:
			li a3, 0x00FFFFFF
			j MaskEnd
		MaskEnd:
			and t2, t2, a3			

			lw a1, 8(sp)
			lw a3, 4(sp)
			lw a4, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a0 a1 (sp)
			addi sp, sp, 12 # make t2 zero at that byte

			add t2, t2, t0
			sw t2, 0(a1)  # write avg with little endian		

			
			
			lw t2, 12(sp)
			lw t3, 8(sp)
			lw a0, 4(sp)
			lw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
			addi sp, sp, 16

			addi a2, a2, -1 # update for3

			
			#blt a2, t1, For3
			
			bge a2, x0, For3
		ForExit3:
			nop
			


		addi a1, a1, -3 # update for2

		addi sp, sp, -4
		sw a2, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a2(sp)
		lw a2, 12(sp) # w/2^k

		addi sp, sp, -4
		sw t0, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a2 t0(sp)
		# mul a2, a2, 3
		mv t0, a2
		slli t0, t0, 1
		add a2, a2, t0 # a2 *= 3
		lw t0, 0(sp)
		addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a2(sp)

		lw a2, 0(sp)
		addi sp, sp, 4
		 
		# update a2
		# a1: j, a2: w_resized*3

		bge a1, x0, For2


	ForExit2:
		nop
	addi sp, sp, -16
	sw t2, 12(sp)
	sw t3, 8(sp)
	sw a2, 4(sp)
	sw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a2 a1(sp)

	lw t3, 24(sp) # w/2^k

	mv t2, t3
	slli t2, t2, 1 # 2*w
	add t3, t3, t2 # 3*w_resized

	srli a1, t3, 2
	slli a1, a1, 2 # 3*wr/4 *4
	sub t2, t3, a1 # 3*wr % 4
	
	mv a1, x0 # pad_bytes = 0 
	beq t2, x0, L3 # if w_resized * 3 % 4 == 0
	## else
	addi a2, x0, 4 
	sub a1, a2, t2 # 4 - (w_resized * 3 % 4)
L3: 
	
	# t3: w_resized * 3	initially
	# a1: pad_bytes
	
	add t2, t3, a1 # w_resized * 3 + pad_bytes

	ForInner: # t3: idx, t2(fixed) : w_resized * 3 + pad_bytes
	
		bge t3, t2, ForInnerExit 
		
		#	Body
		# locate =  i * w_bytes_resized + idx
			lw a1, 16(sp) # w_bytes_resized
		
			addi sp, sp, -12
			sw t0, 8(sp)
			sw t2, 4(sp)
			sw t4, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a2 a1/t0 t2 t4(sp)

			
			# mv t2, a0 # i
			lw t2, 40(sp) # i = h/2^k - 1 - a0
			addi t2, t2, -1
			sub t2, t2, a0
			mv t0, x0
			mv t4, x0
			
			Multiple6: # mul a1, a1, i
				bge t0, t2, MultipleExit6
				add t4, t4, a1 
				addi t0, t0, 1 # cnt
				blt t0, t2, Multiple6		

			MultipleExit6:
				mv a1, t4 # a1 =  a1 = w_b_r * i

			lw t0, 8(sp)
			lw t2, 4(sp)
			lw t4, 0(sp)
			addi sp, sp, 12
		
		add a1, a1, t3 # locate = i * w_bytes_resized + idx = a1 + t3

		
	# TODO: chk locate

		mv a2, a1

		
		srli a2, a2, 2
		slli a2, a2, 2 # a2 = locate/4*4	
		
		addi sp, sp, -20
		sw t2, 16(sp)
		sw t3, 12(sp)
		sw a0, 8(sp)
		sw a3, 4(sp)
		sw a4, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a2 a1 / t2 t3 a0 a3 a4(sp)

		sub a3, a1, a2 # a3 = locate % 4

		lw a4, 56(sp) # outptr

		add a4, a4, a2 # padding locate
		
		lw a1, 0(a4) # 3333 2222 1111 0000
		
		#slli t2, a3, 1
		#addi t2, t2, 2 # locate % 4 *2 +2

		addi sp, sp, -4
		sw a1, 0(sp)		
		
		beq a3, x0, Pad0
		addi a1, x0, 1 # a1: temp value
		beq a3, a1, Pad1
		addi a1, x0, 2
		beq a3, a1, Pad2
		j Pad3
		
		#addi sp, sp, -4
		#sw a3, 0(sp) # inside?
		
		Pad0:
			lw a1, 0(sp)
			addi sp, sp, 4

			addi sp, sp, -4
			sw a3, 0(sp)
			li a3, 0xFFFFFF00
			j PadEnd
		Pad1:
			lw a1, 0(sp)
			addi sp, sp, 4

			addi sp, sp, -4
			sw a3, 0(sp)
			li a3, 0xFFFF00FF
			j PadEnd
		Pad2:
			lw a1, 0(sp)
			addi sp, sp, 4

			addi sp, sp, -4
			sw a3, 0(sp)
			li a3, 0xFF00FFFF
			j PadEnd
		Pad3:
			lw a1, 0(sp)
			addi sp, sp, 4

			addi sp, sp, -4
			sw a3, 0(sp)
			li a3, 0x00FFFFFF
			j PadEnd
		PadEnd:
			and a1, a1, a3
			lw a3, 0(sp)
			addi sp, sp, 4
			sw a1, 0(a4)
				
		
		lw t2, 16(sp)
		lw t3, 12(sp)
		lw a0, 8(sp)
		lw a3, 4(sp)
		lw a4, 0(sp)
		addi sp, sp, 20 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a2 a1(sp)		

		# Update
		addi t3, t3, 1
		blt t3, t2, ForInner
	ForInnerExit:
		nop
			
	lw t2, 12(sp)
	lw t3, 8(sp)
	lw a2, 4(sp)
	lw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a2 a1(sp)
	addi sp, sp, 16


	addi a0, a0, -1 # update for1
	bge a0, x0, For1

ForExit1:	
	ret

