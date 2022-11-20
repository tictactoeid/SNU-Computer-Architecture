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

# ao imgptr, a1 h, a2 w, a3 k, a4 outptr
# x0, sp, ra, a0 a1 a2 a3 a4, t0 t1 t2 t3 t4

	.globl bmpresize
bmpresize:
	addi sp, sp, -16
	sw a0, 16(sp) #imgptr
	sw a1, 12(sp) #h
	sw a2, 8(sp) #w
	sw a3, 4(sp) #k
	sw a4, 0(sp) #outptr
	# imgptr h w k outptr(sp)
	li t0, 1
	sll t0, t0, a3
	# t0 = 2 ** k
	addi sp, sp, -4
	sw t0, 0(sp)
	# imgptr h w k outptr scaling_factor(sp)
	mv t0, a1
	mv t1, a2
	srl t0, a3
	srl t1, a3
	addi sp, sp, -8
	sw t0, 4(sp) # h/2^k
	sw t1, 0(sp) # w/2^k
	# imgptr h w k outptr scaling_factor h/2^k w/2^k(sp)
	mul t0, a2, 3 # w*3
	mv t1, t0
	srl t1, 2 # w*3 / 4
	mul t1, 4 # w*3 / 4 * 4
	sub t2, t0, t1 # t2 = w*3 % 4
	sub t3, t0, t2
	bne t2, x0, L1
	mv t3, x0 # w_resized = 0, skipped if t2 != x0
L1:
	addi sp, sp, -4
	sw t3, 0(sp)
	# imgptr h w k outptr scaling_factor h/2^k w/2^k w_bytes(sp)
	lw t0, 4(sp) #w_resized
	mul t0, t0, 3
	mv t1, t0
	srl t1, 2 # w_r*3 / 4
	mul t1, 4
	sub t2, t0, t1 # t2 = w_r*3 % 4
	sub t3, t0, t2
	bne t2, x0, L2
	mv t3, x0 # skipped if t3 != x0
L2:
	addi sp, sp, -4
	sw t3, 0(sp)
	# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)

	mv t0, x0 # avg

	# Init - For1
	mv a0, x0 # i
	# ! i<h_resized => i >= h/2^k => a1 >= a2

For1: # loop with i : use a0(i)
	addi sp, sp, -4
	sw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a1(sp)
	lw a1, 16(sp) # h/2^k
	bge a0, a1, ForExit1 # if i >= h/2^k EXIT
	lw a1, 0(sp)
	addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)

	# Body - For1
		mv a1, x0 # Init - For2
	For2: # loop with j : use a1(j)
		addi sp, sp, -4
		sw a2, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a2(sp)
		lw a2, 12(sp) # w/2^k
		mul a2, a2, 3
		bge a1, a2, ForExit2
		lw a2, 0(sp)
		addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)

		#Body - For2
		nop
			mv a2, x0 # Init - For3
			
		For3: # loop with x : use a2(x)	
			addi sp, sp, -4
			sw t1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t1(sp)
			addi t1, x0, 3
			bge a2, t1, ForExit3
			lw t1, 0(sp)
			addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)

			#Body - For3

			mv t0, x0 # avg = 0
				# Init - For4
				lw a3, 16(sp) # scaling factor, 2^k
				addi t2, a3, 1
				mul a3, a3, a0 # m = i * scaling_factor						
				mul t2, t2, a0 # (i + 1) * scaling_factor
				# cant reduce maybe

			For4: # a3(m), t2
				#addi sp, sp, -4
				#sw t2, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2(sp)
				
				bge a3, t2, ForExit4
				#lw t2, 0(sp)
				#addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)

				nop
					#Init - For5
					lw a4, 16(sp)
					addi t3, a4, 3
					mul a4, a4, a1 # n = j * scaling_factor	
					mul t3, t3, a1
				For5: # a4(n), t3
					bge a4, t3, ForExit5
					nop
					# load and compute avg

					# t1, t4 : free
					# t0 : avg
					# t2, t3 : for loop

					# locate = m * w_bytes + n+x // for load value
					lw t1, 4(sp) # w_bytes
					mul t1, t1, a3 # *m
					add t1, t1, a4 # +n
					add t1, t1, a2 # +x
					# consider little endian
					mv t4, t1
					srli t4, 2 # locate / 4
					slli t4, 2 # locate/4 * 4


					addi sp, sp, -16
					sw t2, 12(sp)
					sw t3, 8(sp)
					sw a0, 4(sp)
					sw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a0 a1(sp)

					sub a0, t1, t4 # locate % 4
					lw a1, 44(sp) # imgptr
					addi a1, a1, t4 # imgptr + locate/4*4
					lw a1, 0(a1) # load value - 4byte
					addi t2, x0, 3
					sub t2, t2, a0
					mul t2, t2, 2
					# little endian : 33 22 11 00
					# locate % 4 = 0 -> 6, 1->4, 2->2, 3->0 shift left
					# shift left (3 - locate%4) * 2
					sll a1, t2 # ex) l%4 = 2, shift left 2, 22 11 00 00
					# shift right 6 - ((3 - locate%4) * 2)
					addi t3, x0, 6
					sub t3, t3, t2
					srl a1, t3 # a1: 00 00 00 value

					add t0, a1 # avg += *(imgptr + locate);

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

				#addi sp, sp, -4
				#sw t2, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2(sp)
				#addi t2, a3, 1				
				#mul t2, t2, a0 # (i + 1) * scaling_factor				
				blt a3, t2, For4

			ForExit4:
				#lw t2, 0(sp)
				#addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
			lw t4, sp(24) # k
			mul t4, t4, 2 #  2*k
			srl t0, t4 # avg /= (scaling_factor * scaling_factor);

			# locate_out = i * w_bytes_resized + (j+x);
			lw t1, 0(sp)
			mul t1, t1, a0
			add t1, t1, a1
			add t1, t1, a2			
			mv t4, t1
			srli t4, 2
			slli t4, 2 # locate/4 * 4

			addi sp, sp, -16
			sw t2, 12(sp)
			sw t3, 8(sp)
			sw a0, 4(sp)
			sw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a0 a1(sp)

			sub a0, t1, t4 # locate % 4
			lw a1, 36(sp) # outptr
			addi a1, a1, t4 # out word address
			lw t2, 0(a1) # load value - 4byte

			# 00 00 00 value -> shift left -> add a1 -> sw a1
			# 33 22 11 00 -> shift left 3*(locate%4)
			addi sp, sp, -4
			sw t1, 0(sp)
			addi t1, x0, 3
			mul t1, a0, t1
			sll t0, t1 # 00 value 00 00
			lw t1, 0(sp)
			addi sp, sp, 4

			addi t2, t2, t0
			sw t2, 0(a1)  # write avg with little endian

			lw t2, 12(sp)
			lw t3, 8(sp)
			lw a0, 4(sp)
			lw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
			addi sp, sp, 16

			addi a2, a2, 1 # update for3
			addi sp, sp, -4
			sw t1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t1(sp)
			addi t1, x0, 3
			blt a2, t1, For3
		ForExit3:		
			lw t1, 0(sp)
			addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
		addi a1, a1, 3 # update for2
		addi sp, sp, -4
		sw a2, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a2(sp)
		lw a2, 12(sp) # w/2^k
		mul a2, a2, 3
		blt a1, a2, For2
		#lw a2, 0(sp)
		#addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)

	ForExit2:
		lw a2, 0(sp)
		addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)

	# TODO: padding
	# pad_bytes = w_resized * 3 % 4 == 0 ? 0 : 4 - (w_resized * 3 % 4);
	addi sp, sp, -16
	sw t2, 12(sp)
	sw t3, 8(sp)
	sw a2, 4(sp)
	sw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a2 a1(sp)

	// a0 - t3 swap

	#lw a0, 24(sp) # w/2^k
	lw t3, 24(sp)
	addi t2, x0, 3
	# mul a0, a0, t2
	mul t3, t3, t2 # 3*w_resized
	#srli a1, a0, 2
	srli a1, t3, 2
	slli a1, a1, 2
	#sub t2, a0, a1
	sub t2, t3, a1 # 3*W_r % 4
	#addi t3, x0, 4
	addi a2, x0, 4
	mv a1, x0
	#beq a0, x0, L3
	beq t2, x0, L3
	#sub a1, t3, t2 # 4 - (w_resized * 3 % 4)
	sub a1, a2, t2 # 4 - (w_resized * 3 % 4)
	# skip if 3*W_r % 4 == 0
L3: 
	# t3: w_resized * 3


	# a1: pad_bytes

	lw t3, 24(sp)
	addi t2, x0, 3
	mul t3, t3, t2 # don't need actually
	add t2, t3, a1
	ForInner: # t3 t2
		bge t3, t2, ForInnerExit
		#	Body
		# locate =  i * w_bytes_resized + idx
		lw a1, 16(sp) # w_b_r
		mul a1, a1, a0
		add a1, a1, t3 # locate

		mv a2, a1
		srli a2, 2
		slli a2, 2 # l/4*4

		addi sp, sp, -20
		sw t2, 16(sp)
		sw t3, 12(sp)
		sw a0, 8(sp)
		sw a3, 4(sp)
		sw a4, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t2 t3 a2 a1 / t2 t3 a0 a3 a4(sp)


		sub a3, a1, a2 # a3 = locate % 4
# TODO
		lw a4, 56(sp) # outptr
		add a4, a4, a2 # padding locate
		lw a1, 0(a4) # 33 22 11 00
		
		# TODO
		# 33 22 11 00 -> 33 00 11 00


					addi t2, x0, 3
					sub t2, t2, a0
					mul t2, t2, 2
					# little endian : 33 22 11 00
					# locate % 4 = 0 -> 6, 1->4, 2->2, 3->0 shift left
					# shift left (3 - locate%4) * 2
					sll a1, t2 # ex) l%4 = 2, shift left 2, 22 11 00 00
					# shift right 6 - ((3 - locate%4) * 2)
					addi t3, x0, 6
					sub t3, t3, t2
					srl a1, t3 # a1: 00 00 00 value

					add t0, a1 # avg += *(imgptr + locate);


		
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



	addi a0, a0, 1 # update for1
	sw a1, 0(sp) # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a1(sp)
	lw a1, 16(sp) # h/2^k
	blt a0, a1, For1 # if i >= h/2^k EXIT
	# TODO: two lines need or not? may be executed in ForExit1 after not branch blt
	#lw a1, 0(sp)
	#addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)



ForExit1:
	lw a1, 0(sp)
	addi sp, sp, 4 # imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)




/*	
For1: #for loop 1: a0
	lw a1, 12(sp) #h/2^k
	bge a0, a1, ForExit1 # if i >= h/2^k EXIT
	# Body - For1
	mv a2, x0 # Init - for2, a2 = j
	lw a3, 8(sp) #w/2^k	
	mul a3, a3, 3
For2: # for loop 2 (inner): a2, a3
	bge a2, a3, ForExit2
	# Body - For2
	mv t0, x0 # avg_b
	mv t1, x0 # g
	mv t2. x0 # r

	#Init - For3
	addi sp, sp, -4
	sw t4, 0(sp)
	# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t4(sp)
	lw t4, 20(sp) # 2^k, scaling factor
	mul a4, a0, t4
	addi a1, a0, 1 # i+1
	mul a1, a1, t4
	lw t4, 0(sp)
	addi sp, sp, 4
	# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
For3: # for (int m=i*scaling_factor; m<(i+1)*scaling_factor; m++)
	# a4, a1
	bge a4, a1, ForExit3
	#Body - For3

	#Init - For4
	addi sp, sp, -4
	sw t0, 0(sp)
	# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized t0(sp)
	lw t0, 20(sp) # scaling factor
	mul t3, a0, t0 # i*sf
	addi t4, a0, 1
	mul t4, t4, t0
	lw t0, 0(sp) # restore
	addi sp, sp, 4
	# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)
For4: # t3, t4
	# Body - For4
	addi sp, sp, -4
	sw a0, 0(sp)
	# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a0(sp)
	# a0 : locate = m*w_bytes + n;
	lw a0, 8(sp)
	mul a0, a0, a4 # m*w_bytes
	add a0, a0, t3 # +n
	

	# Update - For4
	addi t3, t3, 3
	blt t3, t4, For4

	#Update - For3
	addi a4, a4, 1
	blt a4, a1, For3
ForExit3:
	# Update - For2
	addi a2, a2, 3
	blt a2, a3, For2
ForExit2:
	# Update - For1
	addi a0, a0, 1
	addi sp, sp, -4
	sw a1, 0(sp)
	# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized a1(sp)
	lw a1, 16(sp) #h/2^k
	blt a0, a1, For1
	lw a1, 0(sp)
	addi sp, sp, 4
	# imgptr h w k outptr 2^k h/2^k w/2^k w_bytes w_bytes_resized(sp)

ForExit1: 

*/
	











	

















	ret

