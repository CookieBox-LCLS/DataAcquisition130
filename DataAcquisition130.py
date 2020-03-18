##########
#Description
##########
#DataAcquisition130.py is designed to be the master script for data acquisition performed in 130.

#import needed libraries
import sys
sys.path.append("C:/Users/andre/Documents/GitHub/DataAcquisition130/libraries")

#import commands from libraries.
#commands should be renamed as what they will be used as in the main executiong script
#from simulatingWithCollectedData_lib import dataBufferRandomSimulation as getDataBuffered
from simulatingWithCollectedData_lib import dataBufferRandomSimulation as getDataBuffered
#setup variables
keepGoingFlag = True

#run program
#initialize and setup lines

#begin main loop
while keepGoingFlag:

	if getDataBuffered():
		print('reading in data')
	else:
		print('writing out data')


print("end of loop reached")