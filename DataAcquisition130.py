##########
#Description
##########
#DataAcquisition130.py is designed to be the master script for data acquisition performed in 130.

#import needed libraries
import sys
sys.path.append("C:/Users/andre/Documents/GitHub/DataAcquisition130/libraries")
import numpy as np
import datetime
from plottingAndGUI_lib import *
#import commands from libraries.
#commands should be renamed as what they will be used as in the main executiong script
from simulatingWithCollectedData_lib import dataBufferRandomSimulation as getDataBuffered
from simulatingWithCollectedData_lib import readInDataFromFolder as readInData
from simulatingWithCollectedData_lib import returnWaveformAndHits as onTheFlyProcessing
from simulatingWithCollectedData_lib import writeOutRawData as writeOut
from simulatingWithCollectedData_lib import generateNewFileAndHeader as generateNewFileAndHeader
#setup variables
#numChannels = 1 #currently, support for only one channel at a time is implemented
saveToDirectory = "C:\\Users\\andre\\Desktop\\DataWriteOut\\"#written out data to be saved to this folder


class dataAcqGUI(tk.Tk):
	def initializeDataAcq(self):
		#initialize and setup lines
		self.mainLoopFlag = True
		self.rawDataToWriteArray = []
		self.histogramCollected = []
		self.fileNameNow = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")#the file name that writeout data will be saved to
		self.fileNameNowFull = saveToDirectory+str(self.fileNameNow)

		#run a loop to generate file and place delimiter.  Do all one time events here, so that no further processing will be necessary
		entryLoopCompleted = False
		while not entryLoopCompleted:
			if getDataBuffered():
				#collect a first trace, and put it into the data array.  this needs to be done to see what the data looks like.
				newData = readInData()
				#perform on the fly processing for the array
				rawData, hitIndices = onTheFlyProcessing(newData)
				#send data to array that is wating to be written out from
				self.rawDataToWriteArray.append(rawData)
				#initialize the histogram (variable 'histogamCollected') that will be used to keep track of the data collected in this run.  need the size of the trace to produce the histogram
				self.histogramCollected = initializeHistogram(rawData)
				#apply the new hits found in 'hitIndices' to the histogram being updated in the GUI plot.
				self.histogramCollected = addHitsToHistogram(hitIndices, self.histogramCollected)

				#take the first sample data, and use it to generate a new file.  the generateNewFileAndHeader file is unique in that it also creates a header file that contains information regarding the size of an individual data chunk.
				self.rawDataToWriteArray = generateNewFileAndHeader(self.fileNameNowFull, self.rawDataToWriteArray)
				#initialize plotting tools
				self.GUIHandle = initializeGUI(self, self.histogramCollected)
				#lastTrace is needed for plotting the raw trace.  in case the plot is done before any new data is acquired, it's good to have the variable initialized
				self.lastTrace = newData

				#change flag to denote that initialization is complete
				entryLoopCompleted = True




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

		#newdata is saved as the last trace observed
		self.lastTrace = newData


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
					#if GUI flags are raised
					#execute GUI flags

					#else
					#updateThePlots
					updatePlotsMaster(self.GUIHandle, self.histogramCollected, self.lastTrace)

					pass

	def decrease(self):
		print("method decrease has been accessed")





#run program

#create the class object that will be the main GUI window
mainWindow = dataAcqGUI()
#testing stuff out
mainWindow.title("Data Acquisition")

mainWindow.initializeDataAcq()


mainWindow.after(1, mainWindow.runMainLoop())

breakpoint()

mainWindow.mainloop()

breakpoint()


print("end of loop reached")