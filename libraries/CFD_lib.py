import matplotlib.pyplot as pyplt
import numpy as np

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
	#subtract a mean offset
	dataIn_Amplitude -= np.mean(dataIn_Amplitude)
	#calculate the variance of the trace
	sigma = np.std(dataIn_Amplitude)

	#calculate an upper threshold above which to look for peaks in the raw trace
	threshold = 4*sigma
	#return the indices for which the raw data exceeds the threshold.
	dataIn_AboveThreshold_Indices = np.argwhere(dataIn_Amplitude > threshold)

	#if it's likely that there are zero hits in this trace, there's no need to perform the remainder of the CFD processing.
	if(len(dataIn_AboveThreshold_Indices) == 0):
		#create an empty array of found hits
		#NOT IMPLEMENTED YET BUT SHOULD BE
		return dataIn_Amplitude


	#convolve the raw data with a triangular filter
	convFilterLength = 35#this must be an odd value
	convolvedData = convoluteByTriangle(dataIn_Amplitude, convFilterLength)

	#add up an inverse and an offset.  this is the type of approach an electronic CFD performs.
	lengthTrace = len(convolvedData)
	CFDOffset = 25
	inverseMultiplier = -0.25
	offsetTrace = convolvedData[0:(lengthTrace - CFDOffset)]
	inverseTrace = inverseMultiplier * convolvedData[CFDOffset:lengthTrace]
	#traditional CFD adds a time-offset copy of the trace with an inverser copy of original trace.
	comparedTrace = offsetTrace + inverseTrace
	#shift the region with zero-point crossing to be more centered on the zero cross
	indicesShift = round(CFDOffset * (1 + inverseMultiplier))
	dataIn_AboveThreshold_Indices -= indicesShift

	#process the list of indices and break it up into individual arrays, each array representing a single continuous string of indices
	currentList = []
	tupleOfLists = ()
	for ind in range(0, len(dataIn_AboveThreshold_Indices) - 1):
		#add the current index to the current list
		currentList = np.append(currentList, dataIn_AboveThreshold_Indices[ind])

		#inspect whether the next element in the list of indices is the start of a new continuous set.  if it is, close out this list
		if (dataIn_AboveThreshold_Indices[ind + 1] - dataIn_AboveThreshold_Indices[ind]) != 1:
			#the next index is a the start of a new continuous set
			breakpoint()
			tupleOfLists += (currentList,)
			currentList = []
	#process the final index in the array, and close out the current list since the list of indices is complete
	currentList += dataIn_AboveThreshold_Indices[-1]
	tupleOfLists += (currentList,)
	breakpoint()

	#diagnostic plots
	pyplt.plot(convolvedData[6250:6650])
	pyplt.show()
	pyplt.plot(offsetTrace[6250:6650])
	pyplt.show()
	pyplt.plot(inverseTrace[6250:6650])
	pyplt.show()
	pyplt.plot(comparedTrace[6250:6650])
	pyplt.show()
	pyplt.plot(comparedTrace[dataIn_AboveThreshold_Indices])
	pyplt.show()
	breakpoint()
	pass

#convolute the array 'signalIn' by a triangular waveform, with true width (binWidth + 2).  the two extra bits are for the 'zero' value of the triangles convolution.  the max height occurs at the central bin.  think of the convolution filter as a sawtooth.
def convoluteByTriangle(signalIn, binWidth):
	#convoluteByTriangle requires an odd value for 'binWidth' to work.  

	#construct triangular convolution pattern
	multipliers = np.zeros(binWidth)
	numTriangleSide = ((binWidth+1)//2)#this is the number of non-zero points associated with the triangular pattern of the conv filter
	#run a for loop to populate the convolution filter
	for ind in range(0, numTriangleSide):
		#populate the leading side of triangular filter
		multipliers[ind] = (ind+1)/numTriangleSide
		#populate the falling side of the triangular filter
		multipliers[binWidth - 1 - ind] = (ind+1)/numTriangleSide
	normFactor = np.sum(multipliers)
	multipliers = multipliers/normFactor


	lengthData = len(signalIn)
	#apply the convolution filter
	#convolution produces a list of the same length + 2*offsets
	offsets = (binWidth - 1)//2
	convolvedData = np.zeros(lengthData + (binWidth - 1))#populate a list of zeroes
	for ind in range(0, binWidth):
		#apply convolution
		convolvedData[ind:(lengthData+ind)] += multipliers[ind] * signalIn

	#return the subset of the convolved data that represents the correct data length
	return convolvedData[offsets:(lengthData + offsets)]