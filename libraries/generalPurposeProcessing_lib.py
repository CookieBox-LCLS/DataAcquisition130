import sys
import math
import os
from scipy import fft
import numpy as np
#select which CFD to use to process data
# from CFD_lib import andreiKamalovCFD_main as CFD
# from CFD_lib import andreiKamalovCFD_MCPHack as CFD
from CFD_lib import andreiKamalovCFD_statistical as CFD
# from CFD_lib import aveGattonCFD_main as CFD
# from CFD_lib import ryanCoffeeCFD_main as CFD #IS NOT CURRENTLY COMPATIBLE (04/23/2020)


##############################################
#methods to manage the histogram and hit rate metrics
##############################################

#initialize histogram is used to create an array for the collected histogram.  at initialization, it is an array of zero's, the same size as a raw data trace
def initializeHistogram(rawData):
	histogram = np.zeros(len(rawData), dtype=int)
	return histogram


#addHitsToHistogram takes the indexes listed in 'newHits', and increments the respective bins in the array 'histogram'.  the method returns the updated version of 'histogram'
def addHitsToHistogram(newHits, histogram):
	#for each of the new hits in the array 'newHits',
	for ind in range(len(newHits)):
		#isolate the hit index
		hitIndexNow = newHits[ind].item()
		#and increment the respective bin in 'histogram'
		histogram[hitIndexNow] += 1

	return histogram

#addToHitRateDistribution will take in an array that representes a histogram of hit rate, and increment the bin that represents the number of hits in the trace represented by 'newHits'
def addToHitRateDistribution(newHits, hitRateOld):
	#clone the hit rate distribution
	hitRateNew = hitRateOld
	#update the hit rate distribution for the bin that needs to be incremented
	numHits = len(newHits)
	hitRateNew[numHits] = hitRateOld[numHits] + 1

	return hitRateNew

#bin a raw histogram into the bin width specified by the user.  return a plot line's y-values to resemble histogram blocks, but be of the same length as the input variable 'rawHistogram'
def calculateBinnedHistogramTrace(rawHistogram, binWidth):
	lenFullTrace = rawHistogram.size
	#calculate the number of complete bins that rawHistogram can be binned into, for given binWidth
	numberCompleteBins = int(np.floor(lenFullTrace/binWidth))
	#reshape as much of the rawHistogram trace as possible
	lengthToBeReshaped = numberCompleteBins*binWidth
	reshapedTraceArray = np.reshape(rawHistogram[0:lengthToBeReshaped], [numberCompleteBins, binWidth])
	#use the reshaped trace to simplify calculation of bins.  sum up along axis 1 to sum across the bin width dimension.  in other words, sum up the components of a single bin with width binWidth.
	sumsOfBins = np.sum(reshapedTraceArray, 1)

	#using the binnedTrace, and the unutilized tail end of rawHistogram, stich together an array of the same dimension as rawHistogram, but with values that represent binned data.
	binnedPortionOfTrace = np.repeat(sumsOfBins, binWidth)#account for the binned portion of the trace.
	#stitch on any part of the trace not used in the binning
	unusedTraceTail = rawHistogram[lengthToBeReshaped:lenFullTrace]
	binnedTrace = np.concatenate((binnedPortionOfTrace, unusedTraceTail))#need argument of method to be a tuple of the two arrays to be stitched together.

	return binnedTrace

#updateHitRateRunningWindow updates the running window that is used to keep track of the recent hit rate.  a runnind window of some size is used to store the recent hit rates per trace.  when the hit rate is needed, the window contents will be averaged.  this method will take the old window (hitRateMonitoringWindowOld), replace the oldest entry as indicated with modulo(windowIndexToUse, lengthWindow), with the number of hits in newHits
def updateHitRateRunningWindow(windowIndexToUse, newHits, hitRateMonitoringWindowOld):
	#create the new window from the old window, and update the oldest entry with the most recent supplied trace
	hitRateMonitoringWindowNew = hitRateMonitoringWindowOld
	#the index supplied is the number of total traces worked through.  use this value to find the oldest bin in the runnind window array and replace it's value with the number of hits in the most recent trace
	indexCorrect = windowIndexToUse % len(hitRateMonitoringWindowOld)
	hitRateMonitoringWindowNew[indexCorrect] = len(newHits)
	#update the windowIndex for the next iteration
	windowIndexToUse += 1

	return windowIndexToUse, hitRateMonitoringWindowNew



###########################################
#methods for managing on the fly processiong
##########################################
#method 'performNoProcessing' is designed as a stand in.  it does not actually do any processing, but rather returns the data provided immediately.
def performNoProcessing(dataIn):
	return dataIn

#method 'returnWaveformAndHits' takes the raw dataIn and returns the waveform and CFD-based histogram of the data
def returnWaveformAndHits(dataIn):
	#binary .trc files provide the raw waveform as the dataIn
	dataTrace, hitIndices = CFD(dataIn)
	return dataIn, hitIndices

#method 'returnWaveformHitsAndFFT' finds the individual hit locations of a raw trace, and also calculates the power spectral density of the trace.
def returnWaveformHitsAndPSD(dataIn):
	#binary .trc files provide the raw waveform as the dataIn
	dataTrace, hitIndices = CFD(dataIn)
	#call calculatePSD to get the power spectral density of the FFT of the current trace
	PSDOfTrace = calculatePSD(dataIn)

	return dataIn, hitIndices, PSDOfTrace


###########################################
#methods for performing fourier spectra calculations and rise time calculations
###########################################
def initializeSummedPSD(PSDSample):
	#use a sampled PSD of a trace to get the size of the array needed to keep track of the summed PSD
	summedPSD = np.zeros(len(PSDSample), dtype=float)
	#return the empty array.  the population of the PSD with the first trace should be performed elsewhere
	return summedPSD

#calculatePSD takes a time-domain input, dataIn, and calculates the PSD in frequency space.  The frequency components are trimmed to only return non-degenerate positive frequencies.
def calculatePSD(dataIn):
	#calculate the FFT of the raw trace
	discreteFourierTransform = fft(dataIn)
	#calculate the PSD of the trace by first taking the absolute value, and then squaring the FFT
	absOfFFT = np.absolute(discreteFourierTransform)
	PSD = np.square(absOfFFT)
	#output fourier space components should be trimmed to only include the non-degenerate terms
	PSDOfTrace = cutFourierScaleInHalf(PSD)

	#return the calculated power spectral density
	return PSDOfTrace

#convert the time-axis of the collected trace into an axis of frequencies.
def convertTimeAxisToFrequencies(timeAxis):
	#make sure that the timeAxis is a numpy array
	timeAxisArray = np.asarray(timeAxis)
	#calculate the number of samples and the time differential between each step
	numSamples = len(timeAxisArray)
	differentialSpacing = (timeAxisArray[-1] - timeAxisArray[0])/(numSamples-1)
	#use these values to call fftfreq
	freqAxis = np.fft.fftfreq(numSamples, differentialSpacing)

	return freqAxis

#method for cutting the frequency spectrum in half.  Fourier transforms produce identical positive and negative frequency components.  Plotting both is unnecessary, so it is useful to have a method that scales an axis in half.
def cutFourierScaleInHalf(inputFourierSpaceArray):
	#there's a slightly different procedure depending on whether the length of the array is even or odd
	numElements = len(inputFourierSpaceArray)
	if((numElements % 2) == 0):
		#the number of elements is even
		#keep the first half of the frequency-space axis.  the second half is redundant
		halfwayIndex = int(numElements/2)
		#also drop the 0th term (the DC component).  keep all remaining non-degenerate frequency components
		nonDegenerateAxis = inputFourierSpaceArray[1:halfwayIndex]
	else:
		#the number of elements is odd
		#first, find the inflection point of the FFT axis (final index before negative frequencies are included)
		inflectionIndex = int(math.ceil(numElements/2))
		#pick out the section of the fourier space axis to keep.  include all frequencies before the inflection point, but drop the 0th term (the DC term)
		nonDegenerateAxis = inputFourierSpaceArray[1:inflectionIndex]

	return nonDegenerateAxis



#function 'selectZoomedRegion' decides on what region of the complete 'rawTrace' is to be zoomed in on to produce a region that has a single hit on display.  It's important that the hit window also is not within some buffer width, zoomRegionBufferWidth, of any other hit so that residual effects of any other hit aren't observed in the window
def selectZoomedRegion(rawTrace, hitIndices, zoomRegionWidth, zoomRegionBufferWidth):
	#handle the case that no hits were found in the trace
	if(len(hitIndices) == 0):
		windowRegion = list(range(0, zoomRegionWidth))
	#temporary (5/20/20) handle the case of any other hit.  for now, just return the first viable region
	else:
		#simplify the rawTrace into a smaller window for consideration- if a hit is found too close to either edge of the full trace time-axis, it won't be centered in the zoomed in frame.
		#first calculate the size of the lower bound
		cutOffLow = int(round(zoomRegionWidth/2))
		#make the upper bound same size but opposite side of lower bound
		cutOffHigh = len(rawTrace) - cutOffLow
		
		#create a flag to indicate whether a good hit has been found so far, and initialize the index counter for the upcoming while loop
		foundGoodHit = False
		indexNow = 0
		numberHits = len(hitIndices)
		#run the loop as long as a good hit has not been found, and as long as there are more hits to look at
		while((not foundGoodHit) and (indexNow < numberHits)):
			#find the hit location presently being looked at
			hitNow = hitIndices[indexNow]
			#see if the hit checks criteria TEMPORARY (05/20/20) set to only make sure its not near the edge of the trace.  in the future, need to implement a way to find hits that aren't too close to other hits.
			if((hitNow > cutOffLow) and (hitNow < cutOffHigh)):
				hitLocation = hitNow
				foundGoodHit = True
			else:
				indexNow += 1

		if foundGoodHit:
			#a good hit was successfully found.
			#construct a zoomed in window.  first, include half of the zoomRegionWidth as trace that comes before the hit
			lowerIncludeLength = zoomRegionWidth/2
			#select the window that is zoomRegionWidth wide, and starts at lowerIncludeLength before the good hit, stored in hitLocation
			windowStartIndex = hitLocation - int(round(lowerIncludeLength))
			windowRegion = list(range(windowStartIndex, (windowStartIndex + zoomRegionWidth)))
		else:
			#no good hit was successfully found after full completion of the while loop.  return some pre-set windowed region
			windowRegion = list(range(0, zoomRegionWidth))

	return windowRegion


#given a list of hits (hitIndices) that denote MCP hits in the raw data trace (rawTrace), calculate the rise time of each individual hit.
def calculateRiseTimes(rawTrace, hitIndices):
	#for the short term (5/20/20), return an array of rise times that are zero until more of the code is complete
	arrayOfZeros = np.zeros(len(hitIndices), dtype=float)

	return arrayOfZeros



###########################################
#methods for handling file write out
###########################################
#the method 'writeOutRawData' takes the temporary data buffer in the program, and writes it out to the file in fileNameNowFull
def writeOutRawData(fileNameNowFull, rawDataToWrite):
	#open the file to which post-on-the-fly-processed data is written.
	file = open(str(fileNameNowFull), 'ab')
	#the inbound list is a series associated with each readout trace
	for i in range(len(rawDataToWrite)):
		#for each element in the list, remove the first element and write it out
		toWriteList = rawDataToWrite.pop(0)
		#the popped value is likely a list.  convert it to a numpy array to optimize writeout speed.
		toWrite = np.asarray(toWriteList)
		toWrite.tofile(file)
		#keep alternate method (below) commented out in case .tofile still fails
		#file.write(toWrite)

		#process the data that is to be written, and acquire new updates to variables needed for GUI
	file.close()

	return rawDataToWrite

###########################################
#method 'generateNewFileAndHeader' is designed to look at a sampling of data and get it's binary data size, and output it to the file's associated header.txt file.  It then creates the actual data file and saves the first bit of sampled data to it, so as to not waste it.
def generateNewFileAndHeader(fileNameNow, rawDataToWriteArray):
	#first, process the data that needs to be written, and then write it to the binary file that will house all of the data for this run

	#there should only be one entry here - use it to gauge length of write out.  Header writeout will be determined by that information.
	toWriteList = rawDataToWriteArray.pop(0)
	#the popped value is likely a list.  convert it to a numpy array to optimize writeout speed.
	toWrite = np.asarray(toWriteList)
	#save the sampled binary data to the run output file
	#open the file to which post-on-the-fly-processed data is written.
	file = open(str(fileNameNow), 'ab')
	#the portion of binary data that needs saving is the single trace pop'd off of the array earlier.
	toWrite.tofile(file)
	#close appending to fileNameNow
	file.close()

	####figure out the header file, now that binary file has been processed
	fileNameHeader = fileNameNow + '_HEADER.txt'
	#create and open the file that will be used to store processed data.
	file = open(str(fileNameHeader), 'w')
	#get binary size of data sample.  This is done by looking at file size of the recently created binary file, which should only have 1 trace in it so far.
	binaryDataSize = os.stat(str(fileNameNow)).st_size
	#output size of binary data
	file.write("The size of an individual trace, in bytes, within the binary file is: " + str(binaryDataSize) + "\n")
	#close file
	file.close()

	#the empty array is returned so that the loop that called this function knows that there is nothing else to read out of the array.
	return rawDataToWriteArray


#The original method of storing collected data into binary format has some drawbacks.  It was decided that there is a benefit to saving data in the HDF5 format, for which there is a package, h5py.
#The method is worked on here, while the original data storage methods are kept, so as to minimize interference of work while improvements are made
#this method is ran when the first bit of data is generated.  It looks at the dimensions of the first bit of data, and creates an appropriate data file and header file prior to any further accumulation.  As a consequence, there will only be 1 trace passed in through rawDataToWriteArray, and only one call to np.pop is necessary.
def generateNewFileAndHeader_h5py(fileNameNow, rawDataToWriteArray):
	#extract what the acquired trace looks like.  There should only be one trace measured before this method has been called
	toWriteList = rawDataToWriteArray.pop(0)
	#ensure the measured trace is a numpy array, and of the desired data type.
	toWrite = np.asarray(toWriteList, dtype=np.float32)


	pass