##########
#Description
##########
#DataAcquisition130.py is designed to be the master script for data acquisition performed in 130.

#import needed libraries
import sys
sys.path.append("C:/Users/andre/Documents/GitHub/DataAcquisition130/libraries")
import numpy as np
#import commands from libraries.
#commands should be renamed as what they will be used as in the main executiong script
from simulatingWithCollectedData_lib import dataBufferRandomSimulation as getDataBuffered
from simulatingWithCollectedData_lib import readInDataFromFolder as readInData
from simulatingWithCollectedData_lib import performNoProcessing as onTheFlyProcessing
#setup variables
keepGoingFlag = True
numChannels = 1 #currently, support for only one channel at a time is implemented
processedDataToWrite = []
#run program
#initialize and setup lines

#begin main loop
while keepGoingFlag:

	if getDataBuffered():
		#proceed to read out data into arrays
		newData = readInData()

		#perform on the fly processing for the arrays
		processedData = onTheFlyProcessing(newData)

		#send processed data to array that is wating to be written out from
		processedDataToWrite.append(processedData)

		breakpoint()
	else:
		pass
		#write out any data in variable arrays that are awaiting to be written out

		#update internal variables with written out data for plotting purposes
		#check if data is now buffered


print("end of loop reached")