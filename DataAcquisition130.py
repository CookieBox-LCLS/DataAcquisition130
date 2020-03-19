##########
#Description
##########
#DataAcquisition130.py is designed to be the master script for data acquisition performed in 130.

#import needed libraries
import sys
sys.path.append("C:/Users/andre/Documents/GitHub/DataAcquisition130/libraries")
import numpy as np
import datetime
#import commands from libraries.
#commands should be renamed as what they will be used as in the main executiong script
from simulatingWithCollectedData_lib import dataBufferRandomSimulation as getDataBuffered
from simulatingWithCollectedData_lib import readInDataFromFolder as readInData
from simulatingWithCollectedData_lib import performNoProcessing as onTheFlyProcessing
from simulatingWithCollectedData_lib import writeOutProcessedData as writeOut
#setup variables
keepGoingFlag = True
numChannels = 1 #currently, support for only one channel at a time is implemented
saveToDirectory = "C:\\Users\\andre\\Desktop\\DataWriteOut\\"#written out data to be saved to this folder


#run program
#initialize and setup lines
processedDataToWrite = []
fileNameNow = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")#the file name that writeout data will be saved to
fileNameNowFull = saveToDirectory+str(fileNameNow)

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
		#write out any data in variable arrays that are awaiting to be written out
		processedDataToWrite = writeOut(fileNameNowFull, processedDataToWrite)

		#update internal variables with written out data for plotting purposes
		#check if data is now buffered


print("end of loop reached")