##########
#Description
##########
#DataAcquisition130.py is designed to be the master script for data acquisition performed in 130.

import sys
#select the folder to which data will be written out
saveToDirectory = "C:\\Andrei\\dataWriteOut\\"
#write out the folder from which the libraries can be found
sys.path.append("C:/Users/Kevin/Documents/GitHub/DataAcquisition130/libraries")

#import needed libraries
import numpy as np
import tkinter as tk
import datetime
from plottingAndGUI_lib import *
#import commands from libraries.
#commands should be renamed as what they will be used as in the main executiong script
#from lecroyLiveAcquisition_lib import checkDataReadiness as getDataBuffered
#from lecroyLiveAcquisition_lib import readInDataFromScope_c1 as readInData
from simulatingWithCollectedData_lib import dataBufferRandomSimulation as getDataBuffered
from simulatingWithCollectedData_lib import readInDataFromFolder as readInData
from generalPurposeProcessing_lib import returnWaveformAndHits as onTheFlyProcessing
from generalPurposeProcessing_lib import writeOutRawData as writeOut
from generalPurposeProcessing_lib import generateNewFileAndHeader as generateNewFileAndHeader
#setup variables
#numChannels = 1 #currently, support for only one channel at a time is implemented


class MainScriptManager_TK(tk.Tk):

	#this is a method that compiles all methods in the main data acquisition branch of the loop.  the processed data 'buffer' array is passed in and returned out as well.  this 'buffer' exists to store values that have been acquired but not yet written out.
	def dataAcquisitionBranch(self):
		#proceed to read out data into arrays
		newData = readInData()

		#perform on the fly processing for the arrays
		rawData, hitIndices = onTheFlyProcessing(newData)

		#apply the new hits found in 'hitIndices' to the histogram being updated in the GUI plot.
		self.histogramCollected = addHitsToHistogram(hitIndices, self.histogramCollected)

		#send processed data to array that is wating to be written out from
		self.rawDataToWriteArray.append(rawData)

		#newdata is saved as the last trace observed, and the respective hit indices
		self.lastTrace = newData
		self.lastHitIndices = hitIndices


	def runMainLoop(self):
		while self.mainLoopFlag:

			if getDataBuffered():
				#call method that does main acquisition.  the array rawDataToWriteArray will have an element attached to it that represents the acquired data post-fly-processing
				self.dataAcquisitionBranch()
			else:
				#write out any data in variable arrays that are awaiting to be written out.
				#the array 'rawDataToWriteArray' is returned as an empty array that can be re-filled.  It serves as a temporary variable buffer between data acquisitions and data write-outs.
				self.rawDataToWriteArray = writeOut(self.fileNameNowFull, self.rawDataToWriteArray)

				#update internal variables with written out data for plotting purposes

				#see if there is data in the buffer now.  if there is, go ahead and acquire it.
				if getDataBuffered():
					#there is buffered data, need to go acquire it from the data buffer
					self.dataAcquisitionBranch()
				else:
					#command the GUI object to update the plots with new values
					self.GUIHandle.updatePlotsMaster(self.histogramCollected, self.lastTrace, self.lastHitIndices)

					pass


	#postConstructionClassInitialization is intended to be the __init__ constructor - but it cannot be used as an init, since tk.Tk() seems to require its own initializer to be run for proper tk usage.  This contruction performs variable initialization, and runs the first step of data acquisition to help construct other objects needed for program execution.
	def postConstructionClassInitialization(self):
		#setup lines and initialization of variables
		#mainLoopFlag is used as a flag to continue the main loop.  it can be cancelled to close out the program in a controlled way
		self.mainLoopFlag = True
		#variable 'rawDataToWriteArray' is the buffer that stores data that needs to be written out
		self.rawDataToWriteArray = []
		#the filenames are used to create the written files.  they are based on the saveToDirectory, and the time at which the program was initiated
		self.fileNameNow = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")#the file name that writeout data will be saved to
		self.fileNameNowFull = saveToDirectory+str(self.fileNameNow)

		#run a loop to generate file that stores data, and file that stores information about the format.  Do all one time events here.  It is necessary to do in a loop, because a while loop with a controlled flag will ensure that the data will be available for collection.  getDataBuffered will only allow the loop to continue when there is data that is ready to be collected.
		entryLoopCompleted = False
		while not entryLoopCompleted:
			if getDataBuffered():
				#collect a first trace, and put it into the data array.  this needs to be done to see what the data looks like.
				newRawData = readInData()
				#perform on the fly processing for the new data.  the expected return is 'rawData', which is the data that needs to be written to the file.  rawData can be identical to the input value 'newRawData'.  hitIndices contains the index of all the hits found in 'newRawData' with a CFD
				rawData, hitIndices = onTheFlyProcessing(newRawData)
				#send rawData to array that is waiting to be written out
				self.rawDataToWriteArray.append(rawData)
				#initialize the histogram (variable 'histogamCollected') that will be used to keep track of the data collected in this run.  need the size of a raw trace to produce a histogram array of the same size.
				self.histogramCollected = initializeHistogram(rawData)
				#apply the new hits found in 'hitIndices' to the histogram being updated in the GUI plot.
				self.histogramCollected = addHitsToHistogram(hitIndices, self.histogramCollected)

				#take the first sample data, and use it to generate a new file.  generateNewFileAndHeader also creates a header file that contains information regarding the size of an individual data chunk.  data from 'rawDataToWriteArray' is written out, and an empty array is returned to take its place
				self.rawDataToWriteArray = generateNewFileAndHeader(self.fileNameNowFull, self.rawDataToWriteArray)

				#initialize the visual element of the program.  The class 'DataAcqGUI' is designed to manage the GUI's graphics, and it requires the current tkinter object to link the GUI button presses with this loop.  it is also required that self.histogramCollected is created, because some of the plots will need a 'dummy' histogram to make plots and initialize line objects.  DataAcqGUI constructor will call on the current object's histogram itself.
				self.GUIHandle = DataAcqGUI(self)
				#lastTrace is needed for plotting the raw trace.  in case the plot is done before any new data is acquired, it's good to have the variable initialized
				self.lastTrace = newRawData
				#save the latest hit indices for the next trace plot
				self.lastHitIndices = hitIndices

				#change flag to denote that initialization is complete
				entryLoopCompleted = True


def buttonTestPressed():
	print("test button has been pressed.")


#run program

#initialize the tk (tkinter) object.  tk enables a freamwork to generate GUI's and listen for button presses.  button presses can trigger methods to be called and executed.  without a button press, the method 'after' for a tk object enables a method to be run some time after the tk/gui program begins it's loop of listening for button presses.
#in this program, the main data acquisition/processing loop is performed by a tk object, and used as the .after() call.  the graphical interface side of the GUI program is handled by a separate class (below).  the two objects of different classes must interface to successfully execute the program
dataProcessor = MainScriptManager_TK()
#the TK object still has to go through Tkinter's constructor.  this method performs the current program's necessary initialization operations.
dataProcessor.postConstructionClassInitialization()


dataProcessor.after(1, dataProcessor.runMainLoop())
# #pretty sure mainloop actually never gets called.  it seems once the after method is initiated, the thing works well enough as a gui
dataProcessor.mainloop()


print("the end of the program has been reached")