import random
import glob
import lecroyparser

###########################################
def dataBufferRandomSimulation():
	return random.getrandbits(1)


###########################################
   #denote the folder which contains collected .trc files from which to simulate run time.
dataFolderDirectory = 'C:\\Andrei\\fileTransfer\\03162020\\03_16_2020_CX60_6013E-S+'
# dataFolderDirectory = 'C:\\Andrei\\fileTransfer\\03162020\\03_16_2020_CX60_V63+_and_6013E-S+_highcount'
# dataFolderDirectory = 'C:\\Andrei\\fileTransfer\\03162020\\03_16_2020_ZJL4g+_20Vacc'
globPathname = dataFolderDirectory + '\\*.trc'
fileArray = glob.glob(globPathname)
fileArrayIndex = 0
#return the trace data from the next file
def readInDataFromFolder():
	global fileArrayIndex
	fileNameNow = fileArray[fileArrayIndex]
	dataNow = lecroyparser.ScopeData(fileNameNow)
	fileArrayIndex += 1
	return dataNow.y

#return the trace data, as well as the time axis for the next file.
def readInDataFromFolderWithTime():
	global fileArrayIndex
	fileNameNow = fileArray[fileArrayIndex]
	dataNow = lecroyparser.ScopeData(fileNameNow)
	fileArrayIndex += 1
	return dataNow.y, dataNow.x