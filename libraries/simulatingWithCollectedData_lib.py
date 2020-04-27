import random
import glob
import lecroyparser

###########################################
def dataBufferRandomSimulation():
	return random.getrandbits(1)


###########################################
   #denote the folder which contains collected .trc files from which to simulate run time.
dataFolderDirectory = 'C:\\Andrei\\fileTransfer\\03162020\\03_16_2020_CX60_6013E-S+'
globPathname = dataFolderDirectory + '\\*.trc'
fileArray = glob.glob(globPathname)
fileArrayIndex = 0
def readInDataFromFolder():
	global fileArrayIndex
	fileNameNow = fileArray[fileArrayIndex]
	dataNow = lecroyparser.ScopeData(fileNameNow)
	fileArrayIndex += 1
	return dataNow.y