import matplotlib.pyplot as pyplt
import numpy as np

#this library contains different CFD methods that may be used for on-the-fly processing 

###########################################
#Ryan CFD section
###########################################
def ryanCoffeeCFD_main(dataIn_Amplitude):
    pass


###########################################
#Ave CFD section
###########################################
def aveGattonCFD_main(dataIn_Amplitude):
	CFD_TH = 10.  # the noise is scaled to approximately 5. This sets the threshold to 10x the noise level.
	CFD_offset = 5
	conv_len = 3



	wf_amp = dataIn_Amplitude


	#these look like threshold calculations
	wf_amp_avg = np.sum(wf_amp) / wf_amp.shape[0]
	wf_amp_sigma = .5 * np.sqrt(np.sum((wf_amp - wf_amp_avg) ** 2) / wf_amp.shape[0])
	wf_amp = (wf_amp - wf_amp_avg) / wf_amp_sigma
	#this loop is executed once.  not apparent why it is in a loop statement
	for _ in np.arange(1):
		#interesting choice of convolution filter
	    wf_amp = np.convolve(wf_amp, np.concatenate((np.ones(conv_len), np.zeros(conv_len))) / conv_len,
	                         mode='same')

	#some sort of thresholding
	wf_histo, wf_bins = np.histogram(wf_amp, bins=100)
	wf_log_histo = np.log(wf_histo)
	good_value_cut = np.logical_not(np.isinf(wf_log_histo))
	coeff = np.polynomial.polynomial.polyfit(x=wf_bins[:-1][good_value_cut], y=wf_log_histo[good_value_cut], deg=5)
	sigma = np.sqrt(-1. / coeff[2])
	CFD_TH = 3.0 * sigma

	boolean_threshold = np.logical_or(wf_amp > CFD_TH, wf_amp < -CFD_TH)
	boolean_zero_padding = np.logical_and(np.append(np.logical_not(boolean_threshold), np.zeros(CFD_offset)),
	                                      np.append(np.zeros(CFD_offset), boolean_threshold))[0:-CFD_offset]

	wf_zeroed = wf_amp.copy()
	wf_zeroed[boolean_zero_padding] = 0

	#i think boolean_select is True at indices that contain a found hit?
	boolean_select = np.logical_or(boolean_threshold, boolean_zero_padding)

	th_wave = wf_zeroed[boolean_select]

	indexList = np.arange(1, (len(wf_amp) + 1))
	th_time_wave = indexList[boolean_select]

	#some sort of traditional CFD method
	CFD_input = np.append(th_wave, np.zeros(CFD_offset))
	CFD_shift_scale = np.append(np.zeros(CFD_offset), th_wave)
	CFD_wave = CFD_input - CFD_shift_scale

	CFD_wave_pos = np.where(CFD_wave > 0, True, False)
	CFD_wave_neg = np.where(CFD_wave <= 0, True, False)
    #zero_points is a zero crossing within a local subset?
	zero_points = np.logical_and(CFD_wave_pos[:-1], CFD_wave_neg[1:])
	time_locs = th_time_wave[:-1][zero_points[5:]]

	return dataIn_Amplitude, time_locs






##################################################
#Andrei CFD section
##################################################
def andreiKamalovCFD_main(dataIn_Amplitude):
	#initialize 'hitIndices', which will contain the indices of any hits found in the trace supplied as 'dataIn_Amplitude'
	hitIndices = []

	#subtract a mean offset
	dataIn_Amplitude -= np.mean(dataIn_Amplitude)
	#calculate the variance of the trace
	sigma = np.std(dataIn_Amplitude)

	#calculate an upper threshold above which to look for peaks in the raw trace
	threshold = 4*sigma
	#return the indices for which the raw data exceeds the threshold.
	dataIn_AboveThreshold_Indices = np.flatnonzero(dataIn_Amplitude > threshold)

	#if it's likely that there are zero hits in this trace, there's no need to perform the remainder of the CFD processing.
	if(len(dataIn_AboveThreshold_Indices) == 0):
		#create an empty array of found hits
		#NOT IMPLEMENTED YET BUT SHOULD BE
		return dataIn_Amplitude, hitIndices


	#convolve the raw data with a triangular filter
	convFilterLength = 35#this must be an odd value
	convolvedData = convoluteByTriangle(dataIn_Amplitude, convFilterLength)

	#add up an inverse and an offset.  this is the type of approach an electronic CFD performs.
	lengthTrace = len(convolvedData)
	CFDOffset = 20
	inverseMultiplier = -0.75
	offsetTrace = convolvedData[0:(lengthTrace - CFDOffset)]
	inverseTrace = inverseMultiplier * convolvedData[CFDOffset:lengthTrace]
	#traditional CFD adds a time-offset copy of the trace with an inverser copy of original trace.
	comparedTrace = offsetTrace + inverseTrace
	#shift the region with zero-point crossing to be more centered on the zero cross.  The initial array is found based on being above some amount of standard deviations
	indicesShift = round(CFDOffset * (1 + inverseMultiplier))
	dataIn_AboveThreshold_Indices -= indicesShift

	#call a method which will take the array of indices, and separate that one array into a set of arrays, wherein each array is a continuous set of integers.
	tupleOfRegionIndicesArrays = separateArrayIntoTupleOfContinuousArrays(dataIn_AboveThreshold_Indices)

	#findZeroCrossings for each array of continuous integers
	for ind in range(len(tupleOfRegionIndicesArrays)):
		seriesToProcess = tupleOfRegionIndicesArrays[ind]
		#method 'findZeroCrossings' inspects a series to validate it.  if it's a good zero-crossing, it returns: True, indexOfCrossing.  if it's a bad series, the return is 'False, 0'
		validSeriesFlag, hitIndex = findZeroCrossings(seriesToProcess, comparedTrace)
		#append good hits to the array 'hitIndices'
		if(validSeriesFlag):
			hitIndices.append(hitIndex)

	#there are now a set of found hitIndices.  but these are in respect to the processed comparedTrace.  need to un-shift the indices to represent hits for the actual trace (dataIn_Amplitude)
	hitIndices = [x + indicesShift for x in hitIndices]

	#control whether to do diagnostic plots or not
	if(False):
		halfSpan = 200
		for ind in range(len(hitIndices)):
			#diagnostic plots
			lowBound = hitIndices[ind].item() - halfSpan
			highBound = hitIndices[ind].item() + halfSpan
			pyplt.plot(range(lowBound, highBound), convolvedData[lowBound:highBound])
			if (len(hitIndices) > 0):
				pyplt.scatter(hitIndices[ind].item(), convolvedData[hitIndices[ind].item()])
			pyplt.show()

			pyplt.plot(range(lowBound, highBound), dataIn_Amplitude[lowBound:highBound])
			if (len(hitIndices) > 0):
				pyplt.scatter(hitIndices[ind].item(), dataIn_Amplitude[hitIndices[ind].item()])
			pyplt.show()

	return dataIn_Amplitude, hitIndices





#####################################################################################
#support methods for andrei's CFD


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


#this method is designed to take an array of integers, some of which are continuous, and separate it into a set of arrays wherein each array is a continuous set of integers.  these individual arrays are placed into a tuple that is then returned.
def separateArrayIntoTupleOfContinuousArrays(dataIn_AboveThreshold_Indices):
	#setup the 'first' currentList and the tuple that will be populated
	currentList = []
	tupleOfLists = ()

	#handle the odd case that there is exactly 1 index found.  This is a rarity, but it needs to be handled to avoid error
	if len(dataIn_AboveThreshold_Indices) == 1:
		currentList += dataIn_AboveThreshold_Indices[0]
		tupleOfLists += (currentList,)
	#the cases which matter are the ones that have more than one element, and are handled in the else statement
	else:
		for ind in range(0, len(dataIn_AboveThreshold_Indices) - 1):
			#add the current index to the current list
			currentList.append(dataIn_AboveThreshold_Indices[ind])

			#inspect whether the next element in the list of indices is the start of a new continuous set.  if it is, close out this list
			if (dataIn_AboveThreshold_Indices[ind + 1] - dataIn_AboveThreshold_Indices[ind]) != 1:
				#the next index is a the start of a new continuous set
				tupleOfLists += (currentList,)
				#clear the currentList, so that the next value considered will be the first value in a new array
				currentList = []

		#process the final index in the array, and close out the current list since the list of indices is complete
		currentList.append(dataIn_AboveThreshold_Indices[-1])
		tupleOfLists += (currentList,)

	return tupleOfLists


#method findZeroCrossings inspects the index series in seriesToProcess, and verifies that the associated y-values in comparedTrace are an appropriate rising edge.  if it's a good series, return true and the zero crossing index.  if false, return False and 0
def findZeroCrossings(seriesToProcess, comparedTrace):
	numIndices = len(seriesToProcess)
	if numIndices <= 1:
		#series of length 1 won't have a proper zero crossing and are therefore, not valid zero crossings
		return False, 0
	else:
		#the ideal zero crossing series starts negative and trends positive.  it is good to filter series for validity by verifying this.
		seriesLowest = seriesToProcess[0]
		seriesHighest = seriesToProcess[-1]

		#inspect where the series stops being negative
		indLow = seriesLowest
		while (comparedTrace[indLow] < 0) and (indLow <= seriesHighest):
			indLow += 1

		#inspect where the series stops being positive if coming in from the positive side
		indHigh = seriesHighest
		while (comparedTrace[indHigh] > 0) and (indHigh >= seriesLowest):
			indHigh -= 1

		#if indLow and indHigh are adjacent to each other, then the series passed in was a monotonically positive zero-crossing.
		if ((indHigh + 1) == indLow): #the way the while loops are broken out of, it's a valid series if indLow is one value higher than indHigh
			#return true, and the index of the first positive value after the crossing.
			return True, indHigh
		else:
			#this was not a valid series
			return False, 0