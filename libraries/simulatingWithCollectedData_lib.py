import random
import glob
import lecroyparser
import numpy
import sys
from CFD_lib import andreiKamalovCFD_main as CFD

###########################################
def dataBufferRandomSimulation():
	return random.getrandbits(1)


###########################################
dataFolderDirectory = 'C:\\Andrei\\dataTransfer\\03_16_2020_CX60_6013E-S+'
globPathname = dataFolderDirectory+'\\*.trc'
fileArray = glob.glob(globPathname)
fileArrayIndex = 0
def readInDataFromFolder():
	global fileArrayIndex
	fileNameNow = fileArray[fileArrayIndex]
	dataNow = lecroyparser.ScopeData(fileNameNow)
	fileArrayIndex += 1
	return dataNow.y


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

