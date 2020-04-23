import sys
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
#methods for on the fly processiong
##########################################
#method 'performNoProcessing' is designed as a stand in.  it does not actually do any processing, but rather returns the data provided immediately.
def performNoProcessing(dataIn):
	return dataIn

#method 'returnWaveformAndHits' takes the raw dataIn and returns the waveform and CFD-based histogram of the data
def returnWaveformAndHits(dataIn):
	#binary .trc files provide the raw waveform as the dataIn
	dataTrace, hitIndices = CFD(dataIn)
	return dataIn, hitIndices

###########################################
#the method 'writeOutRawData' takes the temporary data buffer in the program, and writes it out to the file in fileNameNowFull
def writeOutRawData(fileNameNowFull, rawDataToWrite):
	#open the file to which post-on-the-fly-processed data is written.
	file = open(str(fileNameNowFull), 'ab')
	#the inbound list is a series associated with each readout trace
	for i in range(len(rawDataToWrite)):
		#for each element in the list, remove the first element and write it out
		toWrite = rawDataToWrite.pop(0)
		toWrite.tofile(file, "")

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
	toWrite = rawDataToWriteArray.pop(0)
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
	toWrite.tofile(file, "")
	file.close()

	#the empty array is returned so that the loop that called this function knows that there is nothing else to read out of the array.
	return rawDataToWriteArray
