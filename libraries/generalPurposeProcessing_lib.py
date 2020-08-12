import sys
import math
from scipy import fft
import numpy as np
#select which CFD to use to process data
from CFD_lib import andreiKamalovCFD_main as CFD
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
	####figure out the header file first
	fileNameHeader = fileNameNow + '_HEADER.txt'
	#create and open the file that will be used to store processed data.
	file = open(str(fileNameHeader), 'w')
	#there should only be one entry here - use it to gauge length of write out, and create a header with that information.
	toWriteList = rawDataToWriteArray.pop(0)
	#the popped value is likely a list.  convert it to a numpy array to optimize writeout speed.
	toWrite = np.asarray(toWriteList)
	#get binary size of data sample
	binaryDataSize = sys.getsizeof(toWrite)
	#output size of binary data
	file.write("The size of an individual bit of binary data is: " + str(binaryDataSize) + "\n")
	#close file
	file.close()

	#####also save the sampled binary data to the real file so as to not waste it.
	#open the file to which post-on-the-fly-processed data is written.
	file = open(str(fileNameNow), 'ab')
	#the portion of binary data that needs saving is the single trace pop'd off of the array earlier.
	toWrite.tofile(file)
	#keep alternate method (below) commented out in case .tofile still fails
	#file.write(toWrite)
	
	file.close()

	#the empty array is returned so that the loop that called this function knows that there is nothing else to read out of the array.
	return rawDataToWriteArray
