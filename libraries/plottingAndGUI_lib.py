import matplotlib.pyplot as pyplt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np	
import tkinter as tk
import time


##################################################
#GUI CLASS
##################################################
class DataAcqGUI:

	#use plotInitHistogram to initialize the histogram plot.  this is done only at startup.  future histograms are plotted by changing the data of the plotted trace, which is created once with this method.
	def plotInitHistogram(self, histogramSample):
		self.histogramHandle, = self.axisHistogram.plot(histogramSample)
		
		#store the trace length as maximum width of a bin possible.  In the 'updateHistogram' method, the raw histogram distribution will be rebinned into bins of user-set width.  that width cannot exceed the length of the trace.  also initialize the current bin width of the histogram.
		self.maxHistoBinWidthPossible = len(histogramSample)
		#initialize the current histogram bin width of the run.  1 by default.
		self.currentHistoBinWidth = 1

	#This is a method to initialize the energy histogram axis and all relevant components.
	def plotInitEnergyHistogram(self, histogramTime, overlapMatrix):
		#calculate the initial energy histogram
		energyHistogram = np.matmul(overlapMatrix, histogramTime)

		#plot the initial histogram, save the output handle
		self.energyHistogramHandle, = self.axisEnergy.plot(energyHistogram)
		#set the y-limits for this axis
		yLimitHigh = np.amax(energyHistogram) + 1
		self.axisEnergy.set_ylim(0, yLimitHigh)

		#initialize the internal variables that store the energy limits.
		self.plotLimitsELow, self.plotLimitsEHigh = self.axisEnergy.get_xlim()
		
	def plotInitRawTrace(self, histogramSample):
		#initialize the raw trace
		self.rawTraceHandle, = self.axisRawTrace.plot(histogramSample)
		self.axisRawTrace.set_ylim(0, 0.1)
		#initialize the scatter plot object used to indicate where hits were found for a specific trace.
		self.traceHitsScatterMarkerHandle = self.axisRawTrace.scatter([],[])

		#initialize the internal variables that store the x limits.
		self.plotLimitsXLow, self.plotLimitsXHigh = self.axisRawTrace.get_xlim()

	#initialize the lineout for the hit rate distribution
	def plotInitHitRateDistribution(self, hitRateDistribution):
		self.hitRateDistHandle, = self.axisRateDistribution.plot(hitRateDistribution)
		#set the x-limits.  there is no reason for these to be changed after initialization.
		self.axisRateDistribution.set_xlim(0, len(hitRateDistribution))


#########################################################
#functions for updating the GUI
#########################################################

	#updatePlotsMaster is a function that update the plots individually.  this is done as a separate method to help prevent the main loop from getting too long to read on it's own, and to help keep the code well organized
	def updatePlotsMaster(self, histogramToPlot, newTrace, traceHitIndices, hitRateDist, hitRateRunningWindow):
		#update the plots
		#update the histogram
		self.updateHistogram(histogramToPlot)
		#update the trace that is on display with a new trace
		self.updateTrace(newTrace, traceHitIndices)
		#update the hit rate plot
		self.updateHitRateDist(hitRateDist)
		#update the energy histogram
		self.updateEnergyHistogram(histogramToPlot)

		#update other user feedback
		#update the running window hit rate
		self.updateRunningHitRate(hitRateRunningWindow)

		#allow everything to be updated
		self.canvasHandle.draw()
		self.scriptManager_TK_Handle.update()

		return

	#update the histogram plot with new data that is provided
	def updateHistogram(self, newHistogram):
		#rearrange the histogram to be plotted into the bin width specified by the user.  but only do it if bin width exceeds the default value of 1, to avoid unnecessary processing.
		if(self.currentHistoBinWidth != 1):
			#call method that rearranges a raw histogram into a binned histogram
			traceToPlot = self.calculateBinnedHistogramTrace(newHistogram, self.currentHistoBinWidth)
		else:
			traceToPlot = newHistogram

		self.histogramHandle.set_ydata(traceToPlot)
		#auto re-scale the y-axis to best show the histogram
		yLimitHigh = np.amax(traceToPlot) + 1
		self.axisHistogram.set_ylim(0, yLimitHigh)

	#bin a raw histogram into the bin width specified by the user.  return a plot line's y-values to resemble histogram blocks, but be of the same length as the input variable 'rawHistogram'
	def calculateBinnedHistogramTrace(self, rawHistogram, binWidth):
		lenFullTrace = rawHistogram.size
		#calculate the number of complete bins that rawHistogram can be binned into, for given binWidth
		numberCompleteBins = int(np.floor(lenFullTrace/binWidth))
		#reshape as much of the rawHistogram trace as possible
		lengthToBeReshaped = numberCompleteBins*binWidth
		reshapedTraceArray = np.reshape(rawHistogram[0:lengthToBeReshaped], [numberCompleteBins, binWidth])
		#use the reshaped trace to simplify calculation of bins.  sum up along axis 1 to sum across the bin width dimension.  in other words, sum up the components of a single bin with width binWidth.
		sumsOfBins = np.sum(reshapedTraceArray, 1)

		#using the binnedTrace, and the unutilized tail end of rawHistogram, stich together an array of the same dimension as rawHistogram, but with values that represent binned data.
		binnedPortionOfTrace = np.repeat(sumsOfBins, binWidth)#account for the binned portion of the trace.
		#stitch on any part of the trace not used in the binning
		unusedTraceTail = rawHistogram[lengthToBeReshaped:lenFullTrace]
		binnedTrace = np.concatenate((binnedPortionOfTrace, unusedTraceTail))#need argument of method to be a tuple of the two arrays to be stitched together.

		return binnedTrace


	#Sometimes, the user may have ToF spectra saved as references, and then later on update the histogram binning.  It is good to have the saved references reflect the changes in binning to be comprable to the active histogram that is being built up and plotted.  The function 'replotReferenceHistograms' cycles through the saved reference spectra, calculates what they should look like with the new binning, and updates their respective handles.
	#The entryChanged_HistoBinWidth function is activated when there is a new entry - near the end of entryChanged_HistoBinWidth, the method 'replotReferenceHistograms' is called.
	def replotReferenceHistograms(self):
		numReferences = len(self.referencesListHistogram)
		#iterate the process for each reference spectra
		for n in range(numReferences):
			#load the respective reference data
			dataThisReference = self.referencesListHistogramData[n]
			#call method that rearranges a raw histogram into a binned histogram
			traceToPlot = self.calculateBinnedHistogramTrace(dataThisReference, self.currentHistoBinWidth)
			#update the reference plot line with the new y-data
			lineHandle = self.referencesListHistogram[n]
			lineHandle.set_ydata(traceToPlot)

	#update the raw trace plot with latest trace provided by the execution loop
	def updateTrace(self, newTrace, traceHitIndices):
		self.rawTraceHandle.set_ydata(newTrace)
		#get the y-values for the hits.  Will need special handling for the case of no hits.  This is because an empty hit indices ([]) list will cause an error when fed in as a parameter into the values list, newTrace.
		if len(traceHitIndices) == 0:
			#special case of zero hits found in trace.
			traceHitValues = []
			#remove the previous scatter plot
			self.axisRawTrace.collections[0].remove()
			#plot an empty scatter placeholder, so that next call to collections[0].remove() does not fail
			self.axisRawTrace.scatter(traceHitIndices, traceHitValues, c='r')
		else:
			traceHitValues = newTrace[traceHitIndices]
			#remove the previous scatter plot
			self.axisRawTrace.collections[0].remove()
			#plot the scatter points for the current trace
			self.axisRawTrace.scatter(traceHitIndices, traceHitValues, c='r')

	#update the hit distribution plot with newHitRateDist.  updates the y-axis as well to best image the distribution.
	def updateHitRateDist(self, newHitRateDist):
		#update the hit rate distribution, and set new y-limits
		self.hitRateDistHandle.set_ydata(newHitRateDist)
		yLimitHigh = np.amax(newHitRateDist) + 1
		self.axisRateDistribution.set_ylim(0, yLimitHigh)

	#update the energy histogram - this method takes the time histogram and the overlap matrix, and uses them to calculate the energy histogram.  it then updates the plotted line
	def updateEnergyHistogram(self, histogramTime):
		#calculate the new energy histogram
		newEnergyHistogram = np.matmul(self.scriptManager_TK_Handle.overlapMatrix, histogramTime)
		#update the plot with the new energy histogram
		self.energyHistogramHandle.set_ydata(newEnergyHistogram)
		#update the y-limits with the new data
		yLimitHigh = np.amax(newEnergyHistogram) + 1
		self.axisEnergy.set_ylim(0, yLimitHigh)

	#updateRunningHitRate looks at a window (an array) of the most recent hit count.  It uses this window to calculate the recent hit rate and output it to the user.
	def updateRunningHitRate(self, hitRateRunningWindow):
		#retrieve the current trace index.  This is needed to alter the hit rate calculation for the early portion of the program, when the window is not fully populated.  It seems unnecessary to go through the effort of explicitly passing the index value as an argument, so it is retrieved through handles.
		currentIndex = self.scriptManager_TK_Handle.hitRateWindowIndex
		#calculate the hit rate.  If the program has processed fewer traces than the window size, calculate the rate with that in mind.
		if(currentIndex < len(hitRateRunningWindow)):
			runningAverage = np.sum(hitRateRunningWindow)/currentIndex
		else:
			runningAverage = np.mean(hitRateRunningWindow)
		#format output string to include rate value.  '%.2f' sets float precision to two places after the decimal point.
		stringToDisplay = "current hit rate: %.2f" % runningAverage
		#display the hit rate
		self.windowedHitRate_stringVar.set(stringToDisplay)




	#the command 'updateAxisXLimits' will command the relevant plot axis to update the x-limits to display between.  The actual values for the x limits must be pre-loaded into the GUI's internal variables 'self.plotLimitsXLow' and 'self.plotLimitsXHigh'
	def updateAxisXLimits(self):
		self.axisHistogram.set_xlim(self.plotLimitsXLow, self.plotLimitsXHigh)
		self.axisRawTrace.set_xlim(self.plotLimitsXLow, self.plotLimitsXHigh)

	#the command 'updateAxisELimits' will command the relevant plot axis to update the energy limits to display between.  The actual values for the e limits must be pre-loaded into the GUI's internal variables 'self.plotLimitsELow' and 'self.plotLimitsEHigh'
	def updateAxisELimits(self):
		self.axisEnergy.set_xlim(self.plotLimitsELow, self.plotLimitsEHigh)

	#########################################
	#methods for handling button and checkbox interface widgets
	#########################################
	#create and grid buttons as well as checkboxes.  also dictate which commands they are to execute should they be pressed.
	def buildButtons(self):
		#create a button to update the plots now.  this is needed in case the run loop is having a hard time keeping up with the data acquisition rate
		self.button_updatePlots = tk.Button(self.scriptManager_TK_Handle,text="update plots NOW", command=self.buttonPressed_updatePlots)
		self.button_updatePlots.grid(row=10, column=17)

		#create a button to exit out of the program
		self.button_quit = tk.Button(self.scriptManager_TK_Handle,text="finish the current run", command=self.buttonPressed_quit)
		self.button_quit.grid(row=11, column=17)

		#create a button to save the current histograms as references.
		self.button_saveReference = tk.Button(self.scriptManager_TK_Handle,text="store reference", command=self.buttonPressed_saveReferences)
		self.button_saveReference.grid(row=9, column=5)

		#create a button to clear all previously saved references
		self.button_clearReferences = tk.Button(self.scriptManager_TK_Handle,text="clear references", command=self.buttonPressed_clearPSDReferences)
		self.button_clearReferences.grid(row=10, column=5)

		#create a checkbox to dictate whether the loop auto-updates the GUI while running.  Can disable auto-updates to prioritize data acquisition and analysis.
		self.checkboxAutoPlot_boolVar = tk.BooleanVar()#create a necessary variable
		self.checkboxAutoplot = tk.Checkbutton(self.scriptManager_TK_Handle, text="enable auto-plotting", variable=self.checkboxAutoPlot_boolVar, onvalue=True, offvalue=False, command=self.buttonPressed_autoPlot)
		#grid the autoplot checkbox
		self.checkboxAutoplot.grid(row=8, column=5)
		#default the checkbox to being on at start of run
		self.checkboxAutoplot.select()


	#handle button presses here
	#quit button was pressed
	def buttonPressed_quit(self):
		print("finishing the program loop")
		self.scriptManager_TK_Handle.mainLoopFlag = False

	#manual plot update button was pressed.
	def buttonPressed_updatePlots(self):
		print("plots are being updated.")
		self.updatePlotsMaster(self.scriptManager_TK_Handle.histogramCollected, self.scriptManager_TK_Handle.lastTrace, self.scriptManager_TK_Handle.lastHitIndices, self.scriptManager_TK_Handle.hitRateDistribution, self.scriptManager_TK_Handle.hitRateMonitoringWindow)

	#user asked for current plots to be saved as a references
	def buttonPressed_saveReferences(self):
		#move current handles onto the reference list
		referenceHandle = self.histogramHandle
		self.referencesListHistogram.append(referenceHandle)
		referenceHandle = self.energyHistogramHandle
		self.referencesListEnergy.append(referenceHandle)
		#also store the current ToF Histogram data.  This is important, because when the histogram binning input is altered, it is useful to update the reference traces to match the new binning, and compare to the active trace.
		histogramArray = np.array(self.scriptManager_TK_Handle.histogramCollected)
		self.referencesListHistogramData.append(histogramArray)

		#the reference handles have now been preserved.  overwrite the active handle names with the current plot values.  User can then clear this new plot while keeping the old reference.
		self.histogramHandle, = self.axisHistogram.plot(self.scriptManager_TK_Handle.histogramCollected)
		#this is a bit of a double-call, but also updateHistogram that was just plotted.  This is done in case the ToF histogram binning is not set to 1.  plotting the data will set 
		self.updateHistogram(self.scriptManager_TK_Handle.histogramCollected)
		#note: plotting energy histogram is a bit more taxing.
		#calculate the initial energy histogram
		energyHistogram = np.matmul(self.scriptManager_TK_Handle.overlapMatrix, self.scriptManager_TK_Handle.histogramCollected)
		#plot the histogram
		self.energyHistogramHandle, = self.axisEnergy.plot(energyHistogram)
		#set the y-limits for this axis
		yLimitHigh = np.amax(energyHistogram) + 1
		self.axisEnergy.set_ylim(0, yLimitHigh)

	#user hit the button to clear all previously saved reference PSD's
	def buttonPressed_clearPSDReferences(self):
		numReferences = len(self.referencesListHistogram)
		#go through each individual line object and remove each one.
		for i in range(numReferences):
			#pop off current histogram line to be removed
			lineToRemoveNow = self.referencesListHistogram.pop(0)
			#delete the line object
			lineToRemoveNow.remove()
			#repeat for energy histogram plot outs
			lineToRemoveNow = self.referencesListEnergy.pop(0)
			lineToRemoveNow.remove()

	#the checkbox that represents the auto-plot option was pressed.  change auto update flag status
	def buttonPressed_autoPlot(self):
		if(self.checkboxAutoPlot_boolVar.get()):
			#if the checkbox is clicked on, enable autoplot
			print("enabling plot auto-updates")
			self.scriptManager_TK_Handle.flagAutoPlot = True
		else:
			#checkbox is clicked off.  disable autoplot
			print("disabling plot auto-updates")
			self.scriptManager_TK_Handle.flagAutoPlot = False



#########################################
#methods for handling label and entry interface widgets
#########################################
	def buildEntries(self):
		#create the label and entry for setting the x limits of the display
		#build the lower limit entry field
		self.labelXLow = tk.Label(self.scriptManager_TK_Handle, text = "Lower X Limit: ")
		self.labelXLow.grid(row=9, column=1, sticky="E")
		self.entryXLow = tk.Entry(self.scriptManager_TK_Handle)
		self.entryXLow.grid(row=9, column=2)
		self.entryXLow.bind('<Return>', self.entryChanged_XLowLimit)

		#build the higher limit entry field
		self.labelXHigh = tk.Label(self.scriptManager_TK_Handle, text = "Upper X Limit: ")
		self.labelXHigh.grid(row=10, column=1, sticky="E")
		self.entryXHigh = tk.Entry(self.scriptManager_TK_Handle)
		self.entryXHigh.grid(row=10, column=2)
		self.entryXHigh.bind('<Return>', self.entryChanged_XHighLimit)

		#create the label and entry for setting the energy limits of the display
		#build the lower limit entry field
		self.labelELow = tk.Label(self.scriptManager_TK_Handle, text = "Lower Energy Limit: ")
		self.labelELow.grid(row=11, column=1, sticky="E")
		self.entryELow = tk.Entry(self.scriptManager_TK_Handle)
		self.entryELow.grid(row=11, column=2)
		self.entryELow.bind('<Return>', self.entryChanged_ELowLimit)

		#build the higher limit entry field
		self.labelEHigh = tk.Label(self.scriptManager_TK_Handle, text = "Upper Energy Limit: ")
		self.labelEHigh.grid(row=12, column=1, sticky="E")
		self.entryEHigh = tk.Entry(self.scriptManager_TK_Handle)
		self.entryEHigh.grid(row=12, column=2)
		self.entryEHigh.bind('<Return>', self.entryChanged_EHighLimit)

		#build the label and entry field for the bin width to use on the histogram display
		self.labelHistoBinWidth = tk.Label(self.scriptManager_TK_Handle, text = "bin width for histogram display: ")
		self.labelHistoBinWidth.grid(row=8, column=0, columnspan=2, sticky="E")
		self.entryHistoBinWidth = tk.Entry(self.scriptManager_TK_Handle)
		self.entryHistoBinWidth.grid(row=8, column=2, columnspan=1)
		self.entryHistoBinWidth.bind('<Return>', self.entryChanged_HistoBinWidth)

		#NOT IMPLEMENTED - UNSURE IF IT WILL BE NECESSARY AND NEED TO DO OTHER WORK TASKS
		# #build the label and entry field for controlling the time zero parameter of the ToF to energy conversion
		# self.labelEnergyBins = tk.Label(self.scriptManager_TK_Handle, text = "energy bins: ")
		# self.labelEnergyBins.grid(row=11, column=5, columnspan=2, sticky="E")
		# self.entryEnergyBins = tk.Entry(self.scriptManager_TK_Handle)
		# self.entryEnergyBins.grid(row=11, column=7, columnspan=1)
		# self.entryEnergyBins.bind('<Return>', self.entryChanged_EnergyBins)

		#build the label and entry field to control the number of bins within the energy histogram display
		self.labelTimeZero = tk.Label(self.scriptManager_TK_Handle, text = "time zero: ")
		self.labelTimeZero.grid(row=12, column=5, columnspan=2, sticky="E")
		self.entryTimeZero = tk.Entry(self.scriptManager_TK_Handle)
		self.entryTimeZero.grid(row=12, column=7, columnspan=1)
		self.entryTimeZero.bind('<Return>', self.entryChanged_TimeZero)


		#build label and entry for recent hit rate display
		self.windowedHitRate_stringVar = tk.StringVar()
		self.labelWindowedHitRate = tk.Label(self.scriptManager_TK_Handle, textvariable=self.windowedHitRate_stringVar)
		self.labelWindowedHitRate.grid(row=9, column=15, columnspan=3)

	#command that is executed when the entry field for the lower x limit is updated.
	#I don't understand tkinter and entries particularly well, but the <Return> binding for entries will call the associated method and pass the key press event.  The call errors if keyPressEvent is not passed in; this method is written to receive the keyPressEvent, but does not do anything with it.
	def entryChanged_XLowLimit(self, keyPressEvent):
		#retrieve the new value.  it will be returned as a string.
		newRetrievedValue = self.entryXLow.get()
		#convert the retrieved value from string to float.  make sure user didn't insert a typo.
		try:
			newValue = float(newRetrievedValue)
		except ValueError:
			print("Lower X limit entry is not a float.")
			return

		#only apply new limit if it's an okay value
		if(newValue < self.plotLimitsXHigh):
			#now that the new values have been checked, store them in internal variables
			self.plotLimitsXLow = newValue

			#call command to update the xlimits for the plots.  Values do not need to be parsed with the command, the command will be able to access internal variables and submit the current low X and high X.
			self.updateAxisXLimits()

	#command that is executed when the entry field for the upper x limit is updated.
	#see 'entryChanged_XLowLimit' comment explaining keyPressEvent.
	def entryChanged_XHighLimit(self, keyPressEvent):
		#retrieve the new value.  it will be returned as a string.
		newRetrievedValue = self.entryXHigh.get()
		#convert the retrieved value from string to float.  make sure user didn't insert a typo.
		try:
			newValue = float(newRetrievedValue)
		except ValueError:
			print("Upper X limit entry is not a float.")
			return

		#only apply new limit if it's an okay value
		if(newValue > self.plotLimitsXLow):
			#now that the new values have been checked, store them in internal variables
			self.plotLimitsXHigh = newValue

			#call command to update the xlimits for the plots.  Values do not need to be parsed with the command, the command will be able to access internal variables and submit the current low X and high X.
			self.updateAxisXLimits()

	#command that is executed when the entry field for the lower energy limit is updated.
	#see 'entryChanged_XLowLimit' comment explaining keyPressEvent.
	def entryChanged_ELowLimit(self, keyPressEvent):
		#retrieve the new value.  it will be returned as a string.
		newRetrievedValue = self.entryELow.get()
		#convert the retrieved value from string to float.  make sure user didn't insert a typo.
		try:
			newValue = float(newRetrievedValue)
		except ValueError:
			print("Lower energy limit entry is not a float.")
			return

		#only apply new limit if it's an okay value
		if(newValue < self.plotLimitsEHigh):
			#now that the new values have been checked, store them in internal variables
			self.plotLimitsELow = newValue

			#call command to update the energy limits for the plots.  Values do not need to be parsed with the command, the command will be able to access internal variables and submit the current low E and high E.
			self.updateAxisELimits()

	#command that is executed when the entry field for the upper energy limit is updated.
	#see 'entryChanged_XLowLimit' comment explaining keyPressEvent.
	def entryChanged_EHighLimit(self, keyPressEvent):
		#retrieve the new value.  it will be returned as a string.
		newRetrievedValue = self.entryEHigh.get()
		#convert the retrieved value from string to float.  make sure user didn't insert a typo.
		try:
			newValue = float(newRetrievedValue)
		except ValueError:
			print("Upper energy limit entry is not a float.")
			return

		#only apply new limit if it's an okay value
		if(newValue > self.plotLimitsELow):
			#now that the new values have been checked, store them in internal variables
			self.plotLimitsEHigh = newValue

			#call command to update the energy limits for the plots.  Values do not need to be parsed with the command, the command will be able to access internal variables and submit the current low energy and high energy.
			self.updateAxisELimits()

	#command that is executed when the entry field for histogram bin width is updated.
	#see 'entryChanged_XLowLimit' comment explaining keyPressEvent.
	def entryChanged_HistoBinWidth(self, keyPressEvent):
		#retrieve the new value.  it will be returned as a string.
		newRetrievedValue = self.entryHistoBinWidth.get()
		#convert the retrieved value from string to int.  make sure user didn't insert a typo.
		try:
			newValue = int(newRetrievedValue)
		except ValueError:
			print("Histogram bin width entry is not an integer.")
			return

		#apply quality control on the submitted integer, make sure it's positive and not too large
		if(newValue < 1):
			print("the value submitted to the histogram bin width is not a positive integer.  it has not been applied.  please use positive integers that are smaller than the trace width only.")
			return
		elif(newValue > self.maxHistoBinWidthPossible):
			print("the value submitted to the histogram bin width is too large.  it has not been applied.  the largest acceptable integer value is the length of the trace.")
			return
		else:
			#the submitted value meets criteria.  apply it to be the new histogram bin width.
			self.currentHistoBinWidth = newValue
			#also, replot the saved ToF reference plots to match the new binning.
			self.replotReferenceHistograms()

	#NOT IMPLEMENTED - UNSURE IF IT WILL BE NECESSARY AND NEED TO DO OTHER WORK TASKS
	# #command that is executed when the entry field for the number of energy bins is updated.
	# #see 'entryChanged_XLowLimit' comment explaining keyPressEvent.
	# def entryChanged_EnergyBins(self, keyPressEvent):
	# 	#retrieve the new value.  it will be returned as a string.
	# 	newRetrievedValue = self.entryEnergyBins.get()
	# 	#convert the retrieved value from string to int.  make sure user didn't insert a typo.
	# 	try:
	# 		newValue = int(newRetrievedValue)
	# 	except ValueError:
	# 		print("Energy bin count entry is not an integer.")
	# 		return

	# 	#apply quality control on the submitted integer, make sure it's positive and not too large
	# 	if(newValue < 1):
	# 		print("the value submitted to the energy bin count is not a positive integer.  it has not been applied.  Please use positive integers only - large bin count leads to substantial calculation delays.")
	# 		return
	# 	else:
	# 		#the submitted value meets criteria.  apply it to be the new histogram bin width.
	# 		self.scriptManager_TK_Handle.energyBins = newValue

	# 		#command the MainScriptManager_TK object to update the overlap matrix.  The overlap matrix is a variable associated with the MainScriptManager_TK class in DataAcquisition130, and called subsequently for any ToF to energy conversions.  An updated overlap matrix will alter the conversion to the new parameters as specified by the user.  The overlap matrix is recalculated on the MainScriptManager side, but the logic to initiate a recalculate is done here.
	# 		self.scriptManager_TK_Handle.flagRecalculateOverlapMatrix = True


	#command that is executed whenever the user submits a new time zero value.  note that time zero must be in nanoseconds.
	#see 'entryChanged_XLowLimit' comment explaining keyPressEvent.
	def entryChanged_TimeZero(self, keyPressEvent):
		#retrieve the new value.  it will be returned as a string.
		newRetrievedValue = self.entryTimeZero.get()
		#convert the retrieved value from string to int.  make sure user didn't insert a typo.
		try:
			newValue = float(newRetrievedValue)
		except ValueError:
			print("Energy bin count entry is not a float.")
			return

		#warn user if the submitted value is small.  Make sure they know that the input is intended to be in units of nanoseconds.
		if(abs(newValue) < 1):
			print("WARNING: the time zero value submitted is less than 1.  Time zero is expected to be in units of nanoseconds - your value is valid and applied, but please verify that you intended it to be in units of nanoseconds.")

		#the submitted value meets criteria.  apply it to be the new histogram bin width.
		self.scriptManager_TK_Handle.timeZero = newValue

		#command the MainScriptManager_TK object to update the overlap matrix.  The overlap matrix is a variable associated with the MainScriptManager_TK class in DataAcquisition130, and called subsequently for any ToF to energy conversions.  An updated overlap matrix will alter the conversion to the new parameters as specified by the user.  The overlap matrix is recalculated on the MainScriptManager side, but the logic to initiate a recalculate is done here.
		self.scriptManager_TK_Handle.flagRecalculateOverlapMatrix = True


######################################################
# methods for graphic positioning and construction
######################################################
	#method initFigures makes the figures for the GUI.  it handles all the layout of the figures and creates the axes objects.
	def initFigures(self):
		#layout the axes within the figure.  control axis size and distribution by the variables here.
		#spacing variables
		verticalSeam = 0.5
		horizontalSeam = 0.6
		verticalSpacing = 0.05
		horizontalSpacing = 0.05
		#assign positions to the histogram plot (big axis)
		xMinHist = horizontalSpacing
		widthHist = (horizontalSeam - horizontalSpacing/2) - xMinHist
		yMinHist = verticalSeam + verticalSpacing/2
		heightHist = (1 - verticalSpacing) - yMinHist
		#assign positions to the raw trace plot
		xMinTrace = horizontalSeam + horizontalSpacing/2 
		widthTrace = (1 - horizontalSpacing) - xMinTrace
		yMinTrace = verticalSeam + verticalSpacing/2
		heightTrace = (1 - verticalSpacing) - yMinTrace
		#assign positions for the rate distribution plot
		xMinRateDistribution = horizontalSeam + horizontalSpacing/2 
		widthRateDistribution = (1 - horizontalSpacing) - xMinRateDistribution
		yMinRateDistribution = verticalSpacing
		heightRateDistribution = (verticalSeam - verticalSpacing/2) - yMinRateDistribution
		#assign positions for energy histogram axis
		xMinEnergy = horizontalSpacing
		widthEnergy = (horizontalSeam - horizontalSpacing/2) - xMinEnergy
		yMinEnergy = verticalSpacing
		heightEnergy = (verticalSeam - verticalSpacing/2) - yMinEnergy


		#create the figure and axis, as prescribed by the setup above
		self.figHandle = pyplt.figure(figsize=(8,6))
		self.axisHistogram = self.figHandle.add_axes([xMinHist, yMinHist, widthHist, heightHist])
		self.axisEnergy = self.figHandle.add_axes([xMinEnergy, yMinEnergy, widthEnergy, heightEnergy])
		self.axisRawTrace = self.figHandle.add_axes([xMinTrace, yMinTrace, widthTrace, heightTrace])
		self.axisRateDistribution = self.figHandle.add_axes([xMinRateDistribution, yMinRateDistribution, widthRateDistribution, heightRateDistribution])


	#initialization of DataAcqGUI object.
	def __init__(self, tk_RootObject):
		self.scriptManager_TK_Handle = tk_RootObject
		#turn interactive mode on.  needed for plots to be dynamic.
		pyplt.ion()
		#initialize lists that will hold reference handles, whenever the user asks to store any
		self.referencesListHistogram = []
		self.referencesListEnergy = []
		self.referencesListHistogramData = []


		#initialize the figures and all the axes for the GUI.  The plot structures themselves are created in initFigures, and the plot lines are handled in separate methods later
		self.initFigures()
		#initialize the inidividual plots.  this is done so that line objects are created and future plot updates can be done by changing the y_data without recreating the figure.
		self.plotInitHistogram(self.scriptManager_TK_Handle.histogramCollected)
		#initialize the plot for the raw trace.
		#the internal x limit variables are created and saved as part of 'plotInitRawTrace'
		self.plotInitRawTrace(self.scriptManager_TK_Handle.histogramCollected)
		#initialize the plot of the hit rate distribution
		self.plotInitHitRateDistribution(self.scriptManager_TK_Handle.hitRateDistribution)
		#initialize the plot of the energy histogram distribution
		self.plotInitEnergyHistogram(self.scriptManager_TK_Handle.histogramCollected, self.scriptManager_TK_Handle.overlapMatrix)

		#pack the figure onto the canvas
		self.canvasHandle = FigureCanvasTkAgg(self.figHandle, master=self.scriptManager_TK_Handle)
		#self.canvasHandle.get_tk_widget().pack(side='top', fill='both', expand=1)
		self.canvasHandle.get_tk_widget().grid(row=0, column=0, rowspan=8, columnspan=18)
		
		#method buildButtons creates all the buttons, packs them, and sorts them out as to which command each of them trigger.
		self.buildButtons()

		#method buildEntries creates and packs the entry fields for values supplied by the user
		self.buildEntries()
