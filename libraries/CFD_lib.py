import matplotlib.pyplot as pyplt

#this library contains different CFD methods that may be used for on-the-fly processing 

###########################################
#Ryan CFD section
###########################################
def ryanCoffeeCFD_main(dataIn_Amplitude):
    pass



##################################################
#Andrei CFD section
##################################################
def andreiKamalovCFD_main(dataIn_Amplitude):
	#convolve the raw data with a triangular filter
	convFilterLength = 11#this must be an odd value
	convolvedData = convoluteByTriangle(dataIn_Amplitude, convFilterLength)



	#diagnostic plots
	pyplt.plot(convolvedData[6300:6700])
	pyplt.show()
	breakpoint()
	pass

#convolute the array 'signalIn' by a triangular waveform, with true width (binWidth + 2).  the two extra bits are for the 'zero' value of the triangles convolution.  the max height occurs at the central bin.  think of the convolution filter as a sawtooth.
def convoluteByTriangle(signalIn, binWidth):
	#convoluteByTriangle requires an odd value for 'binWidth' to work.  

	#construct triangular convolution pattern
	multipliers = [0] * binWidth
	numTriangleSide = ((binWidth+1)//2)#this is the number of non-zero points associated with the triangular pattern of the conv filter
	#run a for loop to populate the convolution filter
	for ind in range(0, numTriangleSide):
		#populate the leading side of triangular filter
		multipliers[ind] = (ind+1)/numTriangleSide
		#populate the falling side of the triangular filter
		multipliers[binWidth - 1 - ind] = (ind+1)/numTriangleSide
	normFactor = sum(multipliers)
	multipliers[:] = [x/normFactor for x in multipliers]


	lengthData = len(signalIn)
	#apply the convolution filter
	#convolution produces a list of the same length + 2*offsets
	offsets = (binWidth - 1)//2
	convolvedData = [0]*(lengthData + (binWidth - 1))#populate a list of zeroes
	for ind in range(0, binWidth):
		#apply convolution
		convolvedData[ind:(lengthData+ind)] += multipliers[ind] * signalIn

	#return the subset of the convolved data that represents the correct data length
	return convolvedData[offsets:(lengthData + offsets)]