##########
#Description
##########
#WaveformSpectralAnalyzer130.py is a script that produces a GUI that specializes in looking at the raw waveforms collected by the cookiebox eToF's.


import sys
#set to True if code is running on LeCroy scope.  if proto-testing, set to False.
runningOnScope = True
if(runningOnScope):
	#select the folder to which data will be written out
	saveToDirectory = "D:/Waveforms/ScopeCollect/"
	#write out the folder from which the libraries can be found
	sys.path.append("D:/DataAcquisition130/libraries")

	#import libraries meant to acquire data on scope.  commands written to libraries need to be renamed to what they're called in the script.  this is to encourage cross-platform development
	from lecroyLiveAcquisition_lib import dataIsReadyForReadout as getDataBuffered
	from lecroyLiveAcquisition_lib import readInDataFromScope_c1 as readInData
	from lecroyLiveAcquisition_lib import readInDataFromScopeWithTime_c1 as readInDataWithTime
else:
	#provide the directory folder from which the libraries can be found
	sys.path.append("C:/Users/Kevin/Documents/GitHub/DataAcquisition130/libraries")
	#select the folder to which data will be written out
	saveToDirectory = "C:\\Andrei\\dataWriteOut\\"

	#import libraries meant to simulate data acquisition with pre-acquired .trc files.  commands written to libraries need to be renamed to what they're called in the script.  this is to encourage cross-platform development
	from simulatingWithCollectedData_lib import dataBufferRandomSimulation as getDataBuffered
	from simulatingWithCollectedData_lib import readInDataFromFolder as readInData
	from simulatingWithCollectedData_lib import readInDataFromFolderWithTime as readInDataWithTime




#import needed libraries
import tkinter as tk
import numpy as np
from waveformDisplayGUI_lib import *
#import commands from libraries.
#consider renaming commands as what they will be used as in the main execution script
from generalPurposeProcessing_lib import *
from generalPurposeProcessing_lib import returnWaveformHitsAndPSD as onTheFlyProcessing
#initialize any constants used within the program
ZOOMED_REGION_BUFFER_WIDTH = 25

class WaveformAnalyzer_TK(tk.Tk):

	#runMainLoop is a command that is called after GUI construction and initialization.  The loop within runMainLoop will be the loop that the program runs through.
	def runMainLoop(self):
		#run in a loop to keep going, until the user has hit the quit button
		while self.mainLoopFlag:
			#while the program is running, run in a loop only if the user keeps the checkbox for auto-un on.
			while self.flagAutoPlot:
				#call compartmentalized function that's responsible for updating all internal variables with new data
				self.updateWithNewTrace();
				#new data has been processed.  command the GUI to update plots with new data.
				self.GUIHandle.updatePlots();

			#or, if auto-plot loop is turned off, the user can perform singular updates on demand
			if self.flagPlotOnce:
				#call compartmentalized function that's responsible for updating all internal variables with new data
				self.updateWithNewTrace();
				#new data has been processed.  command the GUI to update plots with new data.
				self.GUIHandle.updatePlots();
				#now that this has been done once, disable this branch until the user inputs another button press to plot once.
				self.flagPlotOnce = False

			#if the auto plot is disengaged, as long as the code is not actively processing a single scan button press command, it will be in this loop and needs to keep updating the GUI to listen for button presses
			self.update()


	#updateWithNewTrace is a compartmental method that goes through the process of acquiring new data, processing it, and then updating all internal variables.  plotting of updated variables is NOT done here.
	def updateWithNewTrace(self):
		#collect new data trace
		newData = readInData()
		#find the individual hits in the new trace in newData, and also compute the power spectral density of the signal.  rawTrace is a returned copy of newData.
		rawTrace, hitIndices, PSDOfTrace = onTheFlyProcessing(newData)
		#add the PSD of the new sample to the incoherent sum of PSD's from individual traces. 
		self.summedPSD = np.add(self.summedPSD, PSDOfTrace)
		#find the measured rise time of each hit in the trace
		riseTimesNew = calculateRiseTimes(rawTrace, hitIndices)
		#decide on a zoomed in subset of the full trace that will be highlighted in the GUI
		zoomedWindowRegion = selectZoomedRegion(rawTrace, hitIndices, self.zoomedRegionWidth, ZOOMED_REGION_BUFFER_WIDTH)
		#use the found zoomed in window to calculate the PSD for that windowed region
		psdOfZoomedRegion = calculatePSD(rawTrace[zoomedWindowRegion])

		#update any other self stored variables to reflect newest available data
		self.lastTraceFull = rawTrace
		self.lastTraceHits = hitIndices
		self.lastTracePSD = PSDOfTrace
		#append the array of rise times to the growing array of previosly measured rise times.  This will be used to build up a histogram of the rise time distribution.
		self.arrayOfRiseTimes = np.append(self.arrayOfRiseTimes, riseTimesNew)
		#store the zoomed in window region.  this region is a list of integer indices that represent the index range for the zoomed in window.
		self.lastZoomIndices = zoomedWindowRegion
		#store the calculated PSD of the zoomed in region
		self.zoomedRegionPSD = psdOfZoomedRegion


	#this class is inherited from tk.Tk.  Cannot over-write tk's init constructor because that prevents tkinter functionality from being initialized.  This method serves to initialize anything needed for the class, much like how a true constructor would.
	def waveformAnalyzerSpecificInitialization(self):
		#define the initial width (in indices) that will be used for the zoomed in sub-trace.  This value can later be adapted with user input.
		self.zoomedRegionWidth = 500
		#define this object's main loop flags and dictate their preset values
		self.mainLoopFlag = True
		self.flagAutoPlot = False
		self.flagPlotOnce = False

		#some initialization needs collected data to be processed.  To make sure the data is buffered before collection, a while loop is structured such that it ends after one successful collection
		entryLoopCompleted = False
		while not entryLoopCompleted:
			if getDataBuffered():
				#collect raw data as well as a sample of the time-axis.  This is the rare instance in which the time axis is needed, as most future needs only need the y-values of new traces and can repurpose the time axis measured in the first trace.
				collectedData, self.timeValuesFull = readInDataWithTime()
				#perform on the fly processing on the new data, to find the location of the individual hits.  The location of individual hits is needed to look at zoomed in traces of individual hits in the waveform analyzer GUI.  Processing command 'returnWaveformHitsAndPSD' (probably renames as onTheFlyProcessing) also returns the power spectral density of the raw trace, returning the PSD only for non-degenerate (positive) frequencies.
				rawTrace, hitIndices, PSDOfTrace = onTheFlyProcessing(collectedData)
				#convert the time-values of the trace into the corresponding frequency axis, to represent what frequencies are seen with the FFT
				frequencyAxisFull = convertTimeAxisToFrequencies(self.timeValuesFull)
				#convertTimeAxisToFrequencies returns the complete spectral axis.  To match the PSD in PSDOfTrace, degenerate and DC frequencies must be dropped.  this is done by calling cutFourierScaleInHalf
				self.frequencyAxisNondegenerate = cutFourierScaleInHalf(frequencyAxisFull)
				#use the size of the sample PSD to initialize the summed up PSD
				self.summedPSD = initializeSummedPSD(PSDOfTrace)
				#add the PSD of the first sample into the initialized empty array that will track the incoherent summation 
				self.summedPSD = np.add(self.summedPSD, PSDOfTrace)
				#find the measured rise time of each hit in the trace
				riseTimesNew = calculateRiseTimes(rawTrace, hitIndices)
				#decide on a zoomed in subset of the full trace that will be highlighted in the GUI
				zoomedWindowRegion = selectZoomedRegion(rawTrace, hitIndices, self.zoomedRegionWidth, ZOOMED_REGION_BUFFER_WIDTH)
				#use the found zoomed in window to calculate the PSD for that windowed region.  Note that calculatePSD shapes the output to only include non-degenerate frequencies
				psdOfZoomedRegion = calculatePSD(rawTrace[zoomedWindowRegion])
				#compute the frequency axis for the size of the zoomed in window. Start by establishing a sample time axis based on the first such window
				zoomedRegionTimeAxisSample = self.timeValuesFull[zoomedWindowRegion]
				#convert the sampled window into a frequency axis.  Since the only thing that matters is the number of samples in the time axis and the spacing, the resulting frequency axis should apply to all zoom regions
				self.freqAxisZoomedRegion = convertTimeAxisToFrequencies(zoomedRegionTimeAxisSample)
				#cut out degenerate (negative) frequencies and the DC term
				self.freqAxisZoomedRegion = cutFourierScaleInHalf(self.freqAxisZoomedRegion)

				#update any other self stored variables to reflect newest available data
				self.lastTraceFull = rawTrace
				self.lastTraceHits = hitIndices
				self.lastTracePSD = PSDOfTrace
				#create an array of rise times.  Future results will be appended to this array
				self.arrayOfRiseTimes = riseTimesNew
				#store the zoomed in window region.  this region is a list of integer indices that represent the index range for the zoomed in window.
				self.lastZoomIndices = zoomedWindowRegion
				#store the calculated PSD of the zoomed in region
				self.zoomedRegionPSD = psdOfZoomedRegion

				#construct the GUI class object to create the needed figure, axis, and line objects.
				self.GUIHandle = WaveformAnalysisGUI(self)

				#change the loop flag, signaling that data-based initialization has concluded
				entryLoopCompleted = True

#run program

#initialize the tkinter based object.  tkinter is a package that allows a program to update a GUI while also maintaining a main run loop.  The object must first go through a traditional/proper tkinter class initialization and then a supplemental purpose-specific initialization.  The tkinter class has a default init constructor that enables tk capability.  The user cannot overwrite the initialization with another constructor (say, in the inherited class) and expect TK to work.
waveformAnalyzer = WaveformAnalyzer_TK()#inherited tkinter constructor called
waveformAnalyzer.waveformAnalyzerSpecificInitialization()#purpose specific initializer

#tkinter has the built in command 'after', which is used to run a command after the GUI is launches.  This enables a loop in the method called by 'after' to run while the GUI stays active.
waveformAnalyzer.after(1, waveformAnalyzer.runMainLoop())

#run the main loop command of tkinter.  this is needed for tkinter to function properly.
waveformAnalyzer.mainloop()