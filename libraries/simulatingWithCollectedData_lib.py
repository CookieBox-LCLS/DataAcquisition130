import random
import glob
import lecroyparser

def dataBufferRandomSimulation():
	return random.getrandbits(1)


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

#method 'performNoProcessing' is designed as a stand in.  it does not actually do any processing, but rather returns the data provided immediately.
def performNoProcessing(dataIn):
	return dataIn


#the method 'writeOutProcessedData' takes the temporary data buffer in the program, and writes it out to the file in fileNameNowFull
def writeOutProcessedData(fileNameNowFull, processedDataToWrite):
	#open the file to which post-on-the-fly-processed data is written.
	file = open(str(fileNameNowFull), 'w')
	#the inbound list is a series associated with each readout trace
	for i in range(len(processedDataToWrite)):
		#for each element in the list, remove the first element and write it out
		toWrite = processedDataToWrite.pop(0)
		file.write("1")
	file.close()

	return processedDataToWrite