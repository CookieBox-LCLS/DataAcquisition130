##########
#Description
##########
#DataAcquisition130.py is designed to be the master script for data acquisition performed in 130.

#import needed libraries
import sys
sys.path.append("C:/Users/andre/Documents/GitHub/DataAcquisition130/libraries")
import numpy
import datetime
#import commands from libraries.
#commands should be renamed as what they will be used as in the main executiong script
from simulatingWithCollectedData_lib import dataBufferRandomSimulation as getDataBuffered
from simulatingWithCollectedData_lib import readInDataFromFolder as readInData
from simulatingWithCollectedData_lib import performNoProcessing as onTheFlyProcessing
from simulatingWithCollectedData_lib import writeOutProcessedData as writeOut
from simulatingWithCollectedData_lib import generateNewFileAndHeader as generateNewFileAndHeader
#setup variables
keepGoingFlag = True
numChannels = 1 #currently, support for only one channel at a time is implemented
saveToDirectory = "C:\\Users\\andre\\Desktop\\DataWriteOut\\"#written out data to be saved to this folder


#run program
#initialize and setup lines
processedDataToWrite = []
fileNameNow = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")#the file name that writeout data will be saved to
fileNameNowFull = saveToDirectory+str(fileNameNow)

#run a loop to generate file and place delimiter.  Do all one time events here, so that no further processing will be necessary
entryLoopCompleted = False
while not entryLoopCompleted:
	if getDataBuffered:
		#read in sacrificial first data into an array.
		sampleData = readInData()
		#apply processing.  this is done to see what the processed data looks like
		processedData = onTheFlyProcessing(sampleData)
		processedDataToWrite.append(processedData)
		#take the sample data
		processedDataToWrite = generateNewFileAndHeader(fileNameNowFull, processedDataToWrite)
		entryLoopCompleted = True


#begin main loop
while keepGoingFlag:

	if getDataBuffered():
		#proceed to read out data into arrays
		newData = readInData()

		#perform on the fly processing for the arrays
		processedData = onTheFlyProcessing(newData)

		#send processed data to array that is wating to be written out from
		processedDataToWrite.append(processedData)
	else:
		#write out any data in variable arrays that are awaiting to be written out.
		#the array 'processedDataToWrite' is returned as an empty array that can be re-filled.  It serves as a temporary variable buffer between data acquisitions and data write-outs.
		processedDataToWrite = writeOut(fileNameNowFull, processedDataToWrite)

		#update internal variables with written out data for plotting purposes
		#check if data is now buffered


print("end of loop reached")