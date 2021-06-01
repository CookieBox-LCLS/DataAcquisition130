import matplotlib.pyplot as pyplt
import numpy as np
import math
import sys
from scipy.signal import argrelmax, argrelmin

#this library contains different CFD methods that may be used for on-the-fly processing 



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
def andreiKamalovCFD_main(dataIn):
	#initialize 'hitIndices', which will contain the indices of any hits found in the trace supplied as 'dataIn_Amplitude'
	hitIndices = []

	#subtract a mean offset
	dataIn_Centered = dataIn - np.mean(dataIn)
	#calculate the variance of the trace
	sigma = np.std(dataIn_Centered)

	#calculate an upper threshold above which to look for peaks in the raw trace
	threshold = 4*sigma
	#return the indices for which the raw data exceeds the threshold.
	dataIn_AboveThreshold_Indices = np.flatnonzero(dataIn_Centered > threshold)

	#if it's likely that there are zero hits in this trace, there's no need to perform the remainder of the CFD processing.
	if(len(dataIn_AboveThreshold_Indices) == 0):
		#create an empty array of found hits
		#NOT IMPLEMENTED YET BUT SHOULD BE
		return dataIn_Centered, hitIndices


	#convolve the raw data with a triangular filter
	convFilterLength = 35#this must be an odd value
	convolvedData = convoluteByTriangle(dataIn_Centered, convFilterLength)

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

	#there are now a set of found hitIndices.  but these are in respect to the processed comparedTrace.  need to un-shift the indices to represent hits for the actual trace (dataIn_Centered)
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

			pyplt.plot(range(lowBound, highBound), dataIn_Centered[lowBound:highBound])
			if (len(hitIndices) > 0):
				pyplt.scatter(hitIndices[ind].item(), dataIn_Centered[hitIndices[ind].item()])
			pyplt.show()

	return dataIn_Centered, hitIndices


#CFD that finds hits based on statistical analysis of the raw trace.  The main idea is to look at the stastitical probability of each trace having it's magnitude.  Look for clusters that are above some threshold, and consider those clusters as unique.  Then look through the cluster to see if theres multiple separate hits within it.
zScoreUnversal = 6
def andreiKamalovCFD_statistical(dataIn, noiseRegionLimitLow=0, noiseRegionLimitHigh=1000):
	hitIndices = []
	hitLimitsHigh = []
	convPeakMax = []

	#normalize the trace to be positive, and have max value of +1
	normedTrace = normalizeTrace(dataIn)
	# dataInNormalize = normedTrace
	dataInNormalize = np.diff(normedTrace)
	#use the suggested noise region to establish some understanding of the trace and it's signal/noise ratio
	stdDev = np.std(dataInNormalize[noiseRegionLimitLow:noiseRegionLimitHigh])
	#convert trace to a series of z-scores
	zScoresArray = dataInNormalize/stdDev

	#convolve zScoresArray across some length
	minimumWidthOfHit = 9
	convolved_zScores = np.convolve(zScoresArray, np.ones(minimumWidthOfHit), 'same')

	#use convolved z-scores array to look for local maxima
	findMaxIndices = argrelmax(convolved_zScores)
	findMaxIndices = findMaxIndices[0]#unwrap the output of argrelmax

	firstRealPeakZScore = 0
	firstPeakEstablished = False
	#look through each local maxima
	for localMax in findMaxIndices:
		combined_zScoreHere = convolved_zScores[localMax]
		#check whether the current local maxima meets criteria for certainty that a peak is found
		if combined_zScoreHere/math.sqrt(minimumWidthOfHit) > zScoreUnversal:
			#check if localMax is already accounted for in between a previously located low and high limit pair
			if not checkIfAlreadyConsidered(localMax, hitIndices, hitLimitsHigh):

				if not firstPeakEstablished:
					firstRealPeakZScore = combined_zScoreHere
					firstPeakEstablished = True

				if combined_zScoreHere > 0.2*firstRealPeakZScore:
					#current maxima believed to be a legitimate peak.  Process it to isolate the domain of the peak.
					peakLimitLow, peakLimitHigh = isolatePeakBy_zScores(zScoresArray, localMax, minimumWidthOfHit)

					#check if this is possible ringing - basic check is to see if the start is negative valued and if the positive value is not that much larger in terms of magnitude
					if (normedTrace[peakLimitLow] < 0) and (np.absolute(normedTrace[peakLimitHigh]) <= 3.5*np.absolute(normedTrace[peakLimitLow])):
						#this could be a ringing peak, better to drop it
						pass
					else:
						hitIndices.append(peakLimitLow)
						hitLimitsHigh.append(peakLimitHigh)
						convPeakMax.append(localMax)

	# #go backwards from end to start, and eliminate peaks that begin too soon after the end of the previous peak.  This helps eliminate ripples that the algorithm claims are separate peaks, but are actually part of the previous peak, just separated by a short burst of low z-score
	# for i in range(len(hitIndices)-1, 0, -1):
	# 	if ((hitIndices[i] - hitLimitsHigh[i-1]) < 7):
	# 		#hit is too close to previous hit.  remove it from the list
	# 		hitIndices.pop(i)
	# 		hitLimitsHigh.pop(i)
	# 		convPeakMax.pop(i)

	#convert hitIndices list into an array
	hitIndices = np.asarray(hitIndices)
	hitLimitsHigh = np.asarray(hitLimitsHigh)
	convPeakMax = np.asarray(convPeakMax)

	return dataIn, hitIndices, hitLimitsHigh, convPeakMax



#quick hack to apply CFD to MCP direct output.  This is a quick hack to use the normal CFD but negate the data to help it find the hits associated with the MCP readout.
def andreiKamalovCFD_MCPHack(dataIn):
	dataInNegated = -1 * dataIn

	dataOut_Centered, hitIndices = andreiKamalovCFD_main(dataInNegated)

	return dataOut_Centered, hitIndices

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

		#verify that series crossing isn't too close to either start or end of the trace.  If it is too near to either, can't test whether zero crossing is valid.
		#Note that the condition checks look at seriesLowest - 1 and seriesHighest + 1.  This is because the way the while loops go through below, the loop can cause either indLow or indHigh to go out of bounds of comparedTrace, and then require a call to comparedTrace with an invalid index on the next boolean condition check.
		if (seriesLowest - 1) < 0 or seriesHighest < 0:
			#verify that the seriesToProcess does not include negative integers - that is, that it is not too close to the start of trace to pass the test
			#if it is, return that the series is not valid
			return False, 0
		elif (seriesHighest + 1) >= len(comparedTrace) or seriesLowest >= len(comparedTrace):
			#verify that the seriesToProcess is not too close to the end of the trace - that is, verify it isn't at the cutoff edge of the time axis.
			#if it is, return that the series is not valid
			return False, 0


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



#function to normalize a trace to be positive, such that the max of the trace is 1.
def normalizeTrace(dataIn):
	#ensure that the dataIn value is normalized to zero.  Do this by finding a median value of the trace
	dataInNorm = dataIn - np.median(dataIn)
	#normalize the data such that the highest point has absolute value of 1.  First, find the maximal value but also figure out if peak is upwards or downwards going
	maximalValueAbs = np.absolute(np.max(dataInNorm))
	minimalValueAbs = np.absolute(np.min(dataInNorm))
	if(maximalValueAbs > minimalValueAbs):
		#the peak is positive going.  normalize with positive value
		dataInNorm = dataInNorm/maximalValueAbs
	else:
		#the peak is negative going.  normalize with negative value
		dataInNorm = -1*dataInNorm/minimalValueAbs

	return dataInNorm


#a suspected peak was found based on combined z-scores.  find a good length for it based on the middle.
def isolatePeakBy_zScores(zScoresArray, localMaxIndex, minimumWidthOfHit):
	#I should use indices (localMaxIndex-minimumWidthOfHit/2):(localMaxIndex+minimumWidthOfHit/2).  IF supplied width is odd, give preference to rising edge

	streakBreakerCount = 3
	thresholdScore = zScoreUnversal
	#denote the starintg upper and lower boundaries for the peak.  calling method provides some minimal width.
	indexCutoffLow = localMaxIndex - int(np.ceil(minimumWidthOfHit/2))#set starting high cutoff as max index minus half the width
	indexCutoffHigh = localMaxIndex + int(np.floor(minimumWidthOfHit/2)) - 1#set starting high cutoff as max index plus half the width
	if indexCutoffHigh >= len(zScoresArray):
		indexCutoffHigh = len(zScoresArray) - 1
	#start by trying to find the later times for which the peak still seems statistically significant
	current_zScoreSum = np.sum(zScoresArray[indexCutoffLow:(indexCutoffHigh + 1)])
	currentLength = indexCutoffHigh - indexCutoffLow + 1
	lastImproved_zScore = (current_zScoreSum/math.sqrt(currentLength))
	lastImproved_zScoreSum = current_zScoreSum
	currentStrikes = 0
	#loop through later times, increasing the upper x-limit of the found peak until enough strikes have been taken
	while currentStrikes < streakBreakerCount:
		#find new variables associated with an incremented width of peak

		if(indexCutoffHigh + 1 == len(zScoresArray)):
			break
			breakpoint()
		else:
			indexCutoffHigh += 1

		currentLength += 1
		current_zScoreSum = current_zScoreSum + zScoresArray[indexCutoffHigh]
		new_zScore = (current_zScoreSum/math.sqrt(currentLength))
		#see if adding this index helped the cumulative z-score or not
		if new_zScore >= lastImproved_zScore:
			#expanding to this index benefits the cumulative z-score, so thi series is likely part of the hit
			lastImproved_zScore = new_zScore
			lastImproved_zScoreSum = current_zScoreSum
			#upper index has been increased, reset the strike count so method can continue to try expanding the peak length
			currentStrikes = 0
		else:
			#expanding to this index hurts the cumulative z-score metric.  Would be better to not include this index as part of the found hit
			currentStrikes += 1

	#the while loop has been exited, suggesting that the max permissible number of strikes has been reached while trying to expand the peak.  This number of indices appended to the peak on the positive side failed to improve the cumulative z-score, and they should be removed from the final result
	indexCutoffHigh -= streakBreakerCount
	currentLength -= streakBreakerCount

	#perform a similar process to expand the lower time limit of the found peak
	currentStrikes = 0
	current_zScoreSum = lastImproved_zScoreSum
	#loop through earlier times, decreasing the lower x-limit of the found peak until strike limit has been reached
	while currentStrikes < streakBreakerCount:
		indexCutoffLow -= 1
		currentLength += 1
		current_zScoreSum = current_zScoreSum + zScoresArray[indexCutoffLow]
		new_zScore = (current_zScoreSum/math.sqrt(currentLength))
		#see if adding this index helped the cumulative z-score or not
		if new_zScore >= lastImproved_zScore:
			#expanding to this index benefits the cumulative z-score, so thi series is likely part of the hit
			lastImproved_zScore = new_zScore
			lastImproved_zScoreSum = current_zScoreSum
			#upper index has been increased, reset the strike count so method can continue to try expanding the peak length
			currentStrikes = 0
		else:
			#expanding to this index hurts the cumulative z-score metric.  Would be better to not include this index as part of the found hit
			currentStrikes += 1

	#the while loop has completed, meaning the max permissible of invalid indices on the lower limit have been investigated across.  Undo their effects here
	indexCutoffLow += streakBreakerCount
	currentLength -= streakBreakerCount

	#the cutoff indices found thus far normally under-represent the width of the peak.  This is because of how small the noise floor can be compared to a good peak.  Can optionally continue to add tid-bit sections until the noise is confidently encountered.
	#this double while loop below will scout out regions of incrementally smaller steps to check them for whether they may be added on or not.
	lengthsToCheck = 3
	keepAddingHighSide = True
	addOnScoreThresh = 2
	while lengthsToCheck > 0:
		while keepAddingHighSide:
			if(indexCutoffHigh + lengthsToCheck >= len(zScoresArray)):
				break
			zScoreSumAddOn = np.sum(zScoresArray[indexCutoffHigh:(indexCutoffHigh + lengthsToCheck)])
			if (zScoreSumAddOn/math.sqrt(lengthsToCheck)) > addOnScoreThresh:
				indexCutoffHigh += lengthsToCheck
				currentLength += lengthsToCheck
			else:
				keepAddingHighSide = False

		#reset the loop for the next, shorter checking iteration.
		lengthsToCheck -= 1
		keepAddingHighSide = True


	#repeat the process for the lower cutoff index.
	lengthsToCheck = 3
	keepAddingLowSide = True
	addOnScoreThresh = 2
	while lengthsToCheck > 0:
		while keepAddingLowSide:
			zScoreSumAddOn = np.sum(zScoresArray[(indexCutoffLow-lengthsToCheck):indexCutoffLow])
			if (zScoreSumAddOn/math.sqrt(lengthsToCheck)) > addOnScoreThresh:
				indexCutoffLow -= lengthsToCheck
				currentLength += lengthsToCheck
			else:
				keepAddingLowSide = False

		#reset the loop for the next, shorter checking iteration.
		lengthsToCheck -= 1
		keepAddingLowSide = True

	#return x-limits of the found hit
	return indexCutoffLow, indexCutoffHigh


#method for checking whether a peak is in fact a peak and not probable ringing
def validatePeak(dataIn, peakIndex):
	spanToIntegrateAcrossPerDirection = 30

	#figure out limits across which to integrate to do the peak validation
	indexIntegralLow = peakIndex - spanToIntegrateAcrossPerDirection
	if indexIntegralLow < 0:
		indexIntegralLow = 0

	indexIntegralHigh = peakIndex + spanToIntegrateAcrossPerDirection
	if indexIntegralHigh >= len(dataIn):
		indexIntegralHigh = len(dataIn) - 1

	integral = np.sum(dataIn[indexIntegralLow:indexIntegralHigh])

	if integral >= 0:
		return True
	else:
		return False


# #test whether there is a double peak that is about to be reported.
# def postFindValidate(dataIn, peakLimitLow, peakLimitHigh):
# 	convolvedTrace = np.convolve(dataIn[peakLimitLow:peakLimitHigh], np.ones(7), 'same')

# 	#test whether theres more than one peak, and handle the situation if so.
# 	foundPeaks = argrelmax(convolvedTrace)
# 	if len(foundPeaks[0]) == 1:
# 		return True
# 	else:
# 		return False


#This method will take a supplied range and inspect it to be either a single peak or a cluster of multiple peaks that never return to noise floor level.  IF it is a multipeak, it goes ahead and separates the conglomerate by separating based on local minima.
def separateStructureIntoUniquePeaks(normalizedData, startOfStructure, endOfStructure):
	#convolve the subset of the trace that is believed to be a multi-peak
	convolvedSubTrace = np.convolve(normalizedData[startOfStructure:endOfStructure], np.ones(31), 'same')

	#look for breaking points.  minima probably serve as good as anything
	peakMaxima = argrelmax(convolvedSubTrace) + startOfStructure
	peakMaxima = peakMaxima[0]
	foundMinima = argrelmin(convolvedSubTrace) + startOfStructure
	foundMinima = foundMinima[0]
	#the code expects there to be one more maxima than minima.  if this is not the case, there are a number of potential causes, and it seems non-trivial to figure out what to do.
	if peakMaxima.size == foundMinima.size + 1:
		# may proceed
		pass
	else:
		#something weird happening with max/min finders.  cannot split a peak up into sub-components.
		peakStarts = np.zeros(1, dtype=int)
		peakStarts[0] = startOfStructure
		peakEnds = np.zeros(1, dtype=int)
		peakEnds[0] = endOfStructure
		return peakStarts, peakEnds, peakStarts


	# if peakMaxima.size > foundMinima.size:
	# 	#this is fine, we should have 1 more maxima than minima
	# 	pass
	# else:
	# 	if peakMaxima.size == foundMinima.size :
	# 		#likely have to delete a minima peak.  but first, make sure theyre not both zero
	# 		if peakMaxima.size == 0:
	# 			#they are both zero due to this and the previous if statements.  something has gone wrong with the man/min finders, return original series as single peak
	# 			#convert values from integer to array to be consistent with other output option.
	# 			peakStarts = np.zeros(1, dtype=int)
	# 			peakStarts[0] = startOfStructure
	# 			peakEnds = np.zeros(1, dtype=int)
	# 			peakEnds[0] = endOfStructure
	# 			return peakStarts, peakEnds, peakStarts
	# 		if foundMinima.size == 0 or peakMaxima.size == 0:
	# 			breakpoint()
	# 		#look for a faulty minima (minima that is between either startOfStructure and 1st maxima or last maxima and endOfStructure) and drop it
	# 		if foundMinima[0] < peakMaxima[0]:
	# 			#faulty minima is between start and 1st peak
	# 			foundMinima = foundMinima[1:]
	# 		elif foundMinima[-1] > peakMaxima[-1]:
	# 			#faulty minima lies between final maxima and end
	# 			foundMinima = foundMinima[0:-1]
	# 		else:
	# 			#not sure what went wrong, might be best to simply return initial conditions.
	# 			peakStarts = np.zeros(1, dtype=int)
	# 			peakStarts[0] = startOfStructure
	# 			peakEnds = np.zeros(1, dtype=int)
	# 			peakEnds[0] = endOfStructure
	# 			return peakStarts, peakEnds, peakStarts
	# 			# #error out and inform terminal
	# 			# sys.exit("ERROR: There is a mismatch between number of found local minima and maxima.  This means the code mut be further developed to figure out the origin of this.")



	if(len(peakMaxima) == 1):
		#there is only one peak here.  no need to do the other possible processing
		#convert values from integer to array to be consistent with other output option.
		peakStarts = np.zeros(1, dtype=int)
		peakStarts[0] = startOfStructure
		peakEnds = np.zeros(1, dtype=int)
		peakEnds[0] = endOfStructure
		return peakStarts, peakEnds, peakMaxima
	else:
		#there are truly multiple peaks here, and it is important to separate the construct into its sub-peaks

		#decide on number of sub-peaks to report back.  Use this number to initialize start/end lists
		numPeaks = foundMinima.size + 1
		peakStarts = np.zeros(numPeaks, dtype=int)
		peakEnds = np.zeros(numPeaks, dtype=int)
		#break up the start/end of structures with the discovered minima
		for i in range(numPeaks):
			if i == 0:
				#if first peak in series, the start is the overall structure start
				peakStarts[i] = startOfStructure
				peakEnds[i] = foundMinima[i] - 1#the subtract 1 is to not have overlap between what is considered end of a peak and start of a new one
			elif i == (numPeaks - 1):
				#if this is the final peak in the series, the end of the peak is the overall structure end
				peakStarts[i] = foundMinima[i - 1]
				peakEnds[i] = endOfStructure
			else:
				#use the found local minima as start/ends of the peaks in the multipeak structure
				peakStarts[i] = foundMinima[i - 1]
				peakEnds[i] = foundMinima[i] - 1#the subtract 1 is to not have overlap between what is considered end of a peak and start of a new one

		#return the indices at which the peaks are claimed to start and end at.
		return peakStarts, peakEnds, peakMaxima

#check if index localMax is already accounted for, by seeing if there's a pair of corresponding hitStarts and hitEnds that encompass localMax's index
def checkIfAlreadyConsidered(localMax, hitStarts, hitEnds):
	#set the default return value.  if a hit is found in previously accounted list, this flag is changed to true
	flagFound = False
	#figure out how many previous hits to check through
	numPreviousHits = len(hitStarts)

	#scan through each of the previous hits
	for i in range(numPreviousHits):
		#check if local max falls within the i'th previous hit
		if (localMax > hitStarts[i]) and (localMax < hitEnds[i]):
			#if it does, return True.
			flagFound = True
			return flagFound

	return flagFound