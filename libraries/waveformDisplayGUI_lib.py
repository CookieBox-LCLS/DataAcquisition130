##########
#Description
##########
#WaveformAnalysisGUI is the GUI class structure to be used in conjuction with WaveformSpectralAnalyzer130.py.  It produces and shows spectral information for the wave waveforms produced by the MCP and amplifiers.

import matplotlib.pyplot as pyplt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import numpy as np



class WaveformAnalysisGUI:
######################################################
# methods for plot updating
######################################################
	
	#main method that gets called to update plots when new data has been processed.  It is compartmentalized to update each unique plot individually by calling sub-functions to manage unique plots.
	def updatePlots(self):
		#call the individual plot update functions
		#update new full trace plot
		self.updateFullTrace(self.scriptManager_TK_Handle.lastTraceFull, self.scriptManager_TK_Handle.lastTraceHits)
		#update the PSD display for the current full trace
		self.updateFourierSpectrumCurrent(self.scriptManager_TK_Handle.lastTracePSD)
		#update the incoherently summed up PSD for the current run
		self.updateFourierSpectrumSummed(self.scriptManager_TK_Handle.summedPSD)
		#plot the new zoomed in window.  Note that the lastZoomIndices supplied represent the indices of the window found.  They do not represent the trace values, but can be used to extract the trace values.  both the new trace and the new window indices are supplied to the method to do this.
		self.updateZoomedTrace(self.scriptManager_TK_Handle.lastTraceFull, self.scriptManager_TK_Handle.lastZoomIndices, self.scriptManager_TK_Handle.lastTraceHits)
		#update the PSD of the zoomed in window to match the new zoomed in region being displayed
		self.updateZoomedFFT(self.scriptManager_TK_Handle.zoomedRegionPSD)

		#scale the frequency plots' y-axis to best image the individual FFT plots.  This is done with 'setNewYLimits', which will update the y-scale for the FFT of the windowed region based on a supplied boolean argument.  This plot's y-scale should not be udpated if there are no hits within it, since that would only tell the y-scale to zoom in on noise.
		if(len(self.scriptManager_TK_Handle.lastTraceHits) > 0):
			#there is a new hit in windowed region's FFT.  update this plot's y-scale with the otehrs
			self.setNewYLimits(updateScaleForWindowedFFT=True)
		else:
			#there can't be a hit within the windowed region's FFT.  do NOT update that plot's y-axis, you will only amplify noise.
			self.setNewYLimits(updateScaleForWindowedFFT=False)

		#all plot lines are updated.  now redraw the plots and update tkinter
		self.canvasHandle.draw()
		self.scriptManager_TK_Handle.update()

	#update the plot that shows the last full raw trace
	def updateFullTrace(self, newTrace, newTraceHitIndices):
		self.fullTraceHandle.set_ydata(newTrace)

		#remove the previous scatter plot markers that denote the location of the unique hits
		self.axisFullTrace.collections[0].remove()
		#plot the scatter points for the current trace.  first have to find the x-value of the hit locations to correctly use the scatter plot.
		timeAxis = self.scriptManager_TK_Handle.timeValuesFull
		newTraceHitTimes = timeAxis[newTraceHitIndices]
		#then find the y-values of the scatter plot
		traceHitValues = newTrace[newTraceHitIndices]
		#overlay the scatter dots onto the trace plot
		self.axisFullTrace.scatter(newTraceHitTimes, traceHitValues, c='r')

	#update the plot that shows the power spectral distribution of the last full trace
	def updateFourierSpectrumCurrent(self, newPSD):
		#normalize the PSD before plotting it, and then plot it.
		normedPSD = self.normalizeArray(newPSD)
		self.fourierSpectrumCurrentHandle.set_ydata(normedPSD)

	#update the incoherently summed up fourier PSD of the run with the updated value
	def updateFourierSpectrumSummed(self, newSum):
		#normalize the PSD before plotting it, and then plot it.
		normedPSD = self.normalizeArray(newSum)
		self.fourierSpectrumSummedHandle.set_ydata(normedPSD)

	#update the zoomed in window with the new trace being looked into
	def updateZoomedTrace(self, newTrace, newWindowIndices, hitIndices):
		timeAxisFull = self.scriptManager_TK_Handle.timeValuesFull

		#use the full trace with the zoomed window indices to find the x & y-values for the zoomed window
		timeAxisTrace = timeAxisFull[newWindowIndices]
		zoomedTraceValues = newTrace[newWindowIndices]
		#plot the new data into the existing line object
		self.zoomedTraceHandle.set_xdata(timeAxisTrace)
		self.zoomedTraceHandle.set_ydata(zoomedTraceValues)

		#update the zoomed trace to also show hit markers.  start by clearing the last scatter markers
		self.axisZoomedTrace.collections[0].remove()
		#find the appropriate x and y values for the scatter markers
		scatTimes = timeAxisFull[hitIndices]
		scatVals = newTrace[hitIndices]
		#plot the new scat times
		self.axisZoomedTrace.scatter(scatTimes, scatVals, c='r')

		#set the limits to reflect the window
		self.axisZoomedTrace.set_xlim(timeAxisTrace[0], timeAxisTrace[-1])

	#update the PSD of the zoomed in window with the new zoomed in PSD values
	def updateZoomedFFT(self, newPSD):
		#do NOT normalize for this plot.  When there is a plot of a zero-hit region's FFT, normalizing it will cause the noise to blow up.  Rather, just plot the values and trust the method 'setNewYLimits' to set appropriate y-values for cases of zero-hit regions.
		##normalize the PSD before plotting it, and then plot it.
		#normedPSD = self.normalizeArray(newPSD)
		self.zoomedFFTHandle.set_ydata(newPSD)

	#the command 'updateAxisFreqLimits' will command the relevant plot axis to update the x-limits to display between.  The actual values for the x limits must be pre-loaded into the GUI's internal variables 'self.freqLimitsLow' and 'self.freqLimitsHigh'.  This method is called after a change in the entry fields for frequency limits has been input by the user.
	def updateAxisFreqLimits(self):
		self.axisZoomedFFT.set_xlim(self.freqLimitsLow, self.freqLimitsHigh)
		self.axisFourierSpectrumSummed.set_xlim(self.freqLimitsLow, self.freqLimitsHigh)
		self.axisFourierSpectrumCurrent.set_xlim(self.freqLimitsLow, self.freqLimitsHigh)
		#It helps to scale the y-limits to be useful for the region between the new freqLimits.  This is done by calling method 'setNewYLimits' in method 'updatePlots'.  The method 'setNewYLimits' requires updated cutoff indices.  the indices are updated with 'findNewIndexLimits'.
		self.findNewIndexLimits()

	#'findNewIndexLimits' is called when new frequency plotting limits are supplied by the user.  this method takes the new cutoff frequencies, and uses them to compute the corresponding cutoff indies.
	def findNewIndexLimits(self):
		#load the frequency axis from the WaveformAnalyzer_TK object.  The user will probably supply the frequency units that are on display in the plots.  Divide by self.frequencyUnits, the units that frequencies are plotted in, to match with what the user will (probably) supply.
		freqAxisFull = self.scriptManager_TK_Handle.frequencyAxisNondegenerate/self.frequencyUnits
		#load the frequency values set by the user.
		valLow = self.freqLimitsLow
		valHigh = self.freqLimitsHigh
		#find and store indices corresponding to user-set limits
		self.indexLimitLow = np.searchsorted(freqAxisFull, valLow, side='right')
		self.indexLimitHigh = np.searchsorted(freqAxisFull, valHigh, side='left')

		#this process must be done separately for the windowed region's FFT plot.  this is because that plot has fewer points, and hence a different list size/index-frequency mapping.
		freqAxisZoomedFFT = self.scriptManager_TK_Handle.freqAxisZoomedRegion/self.frequencyUnits
		self.indexLimitLowZoomedFFT = np.searchsorted(freqAxisZoomedFFT, valLow, side='right')
		self.indexLimitHighZoomedFFT = np.searchsorted(freqAxisZoomedFFT, valHigh, side='left')


	#setNewYLimits applies scaled y-limits onto the frequency graphs of this GUI to improve display quality.  This method loads the y-data within the plotted range, and scales the maximum of the y-axis to be just above the maximal present y-data.
	def setNewYLimits(self, updateScaleForWindowedFFT=True):
		#First, handle the axisFourierSpectrumSummed, which is the axis for the cummulative Fourier spectrum.
		#get the y-data.  Note that data should already be normalized before being plotted.  Hence, retrieving the data from the plotted line should already be normalized
		PSDFull = self.fourierSpectrumSummedHandle.get_ydata()
		#narrow y-data to be within plotted range
		PSDWithinRange = PSDFull[self.indexLimitLow:self.indexLimitHigh]
		#find the maximum within the plotted range, and set that as the new upper y limit.
		yLimitHigh = 1.05*np.amax(PSDWithinRange)
		if(self.plotScale == "linear"):
			#if the plots are set to linear scaling, can use zero for minimum value
			self.axisFourierSpectrumSummed.set_ylim(0, yLimitHigh)
		elif(self.plotScale == "logarithmic"):
			#if the plots are set to logarithmic scaling, cannot use zero for a bottom value - log(0) is -infinity and using that on a y-scale is not defined.  Need to find low-bound for y-scale.
			yLimitLow = 0.95*np.amin(PSDWithinRange)
			self.axisFourierSpectrumSummed.set_ylim(yLimitLow, yLimitHigh)


		#repeat for single-trade PSD axis
		#get the y-data.  Note that data should already be normalized before being plotted.  Hence, retrieving the data from the plotted line should already be normalized
		PSDFull = self.fourierSpectrumCurrentHandle.get_ydata()
		#narrow y-data to be within plotted range
		PSDWithinRange = PSDFull[self.indexLimitLow:self.indexLimitHigh]
		#find the maximum within the plotted range, and set that as the new upper y limit.
		yLimitHigh = 1.05*np.amax(PSDWithinRange)
		if(self.plotScale == "linear"):
			#if the plots are set to linear scaling, can use zero for minimum value
			self.axisFourierSpectrumCurrent.set_ylim(0, yLimitHigh)
		elif(self.plotScale == "logarithmic"):
			#if the plots are set to logarithmic scaling, cannot use zero for a bottom value - log(0) is -infinity and using that on a y-scale is not defined.  Need to find low-bound for y-scale.
			yLimitLow = 0.95*np.amin(PSDWithinRange)
			self.axisFourierSpectrumCurrent.set_ylim(yLimitLow, yLimitHigh)

		#repeat for the FFT plot of the zoomed in region.  This axis is special - the y-limits should only be updated if a hit was detected.  If there were no hits detected, then the zoomed in FFT plot will be just noise.  zooming the y-scale in on noise will produce an undesirable plot, so this should not be done.  To avoid this, an 'if' statement decides whether the y-limits are updated or not.  The method that calls 'setNewYLimits' is expected to supply a boolean statement on whether this axis's scale should be udpated or not.
		if(updateScaleForWindowedFFT):
			#get the y-data.  This line object's plotted y-data is NOT normalized.
			PSDFull = self.zoomedFFTHandle.get_ydata()
			#narrow y-data to be within plotted range
			PSDWithinRange = PSDFull[self.indexLimitLowZoomedFFT:self.indexLimitHighZoomedFFT]
			#find the maximum within the plotted range, and set that as the new upper y limit.
			yLimitHigh = 1.05*np.amax(PSDWithinRange)
			if(self.plotScale == "linear"):
				#if the plots are set to linear scaling, can use zero for minimum value
				self.axisZoomedFFT.set_ylim(0, yLimitHigh)
			elif(self.plotScale == "logarithmic"):
				#if the plots are set to logarithmic scaling, cannot use zero for a bottom value - log(0) is -infinity and using that on a y-scale is not defined.  Need to find low-bound for y-scale.
				yLimitLow = 0.95*np.amin(PSDWithinRange)
				self.axisZoomedFFT.set_ylim(yLimitLow, yLimitHigh)



#########################################
#methods for handling button and checkbox interface widgets
#########################################
#create and grid buttons as well as checkboxes.  also dictate which commands they are to execute should they be pressed.
	def buildButtons(self):
		#create a button to update the plots now.  this is needed in case the run loop is having a hard time keeping up with the data acquisition rate
		self.button_updatePlots = tk.Button(self.scriptManager_TK_Handle,text="single plot update", command=self.buttonPressed_updatePlots)
		self.button_updatePlots.grid(row=18, column=0)

		#create a button to clear the values of the incoherently summed PSD, and reset the array to zero (start accumulating a new one)
		self.button_clearCurrentPSD = tk.Button(self.scriptManager_TK_Handle,text="clear summed PSD", command=self.buttonPressed_clearSummedPSD)
		self.button_clearCurrentPSD.grid(row=20, column=0)

		#create a button to exit out of the program
		self.button_quit = tk.Button(self.scriptManager_TK_Handle,text="finish the current run", command=self.buttonPressed_quit)
		self.button_quit.grid(row=21, column=0)

		#create a button to save the current PSD as a reference.
		self.button_saveReference = tk.Button(self.scriptManager_TK_Handle,text="save PSD as reference", command=self.buttonPressed_savePSDReference)
		self.button_saveReference.grid(row=20, column=5)

		#create a button to clear all previously saved references
		self.button_clearReferences = tk.Button(self.scriptManager_TK_Handle,text="clear reference PSD's", command=self.buttonPressed_clearPSDReferences)
		self.button_clearReferences.grid(row=21, column=5)

		#create a set of radiobuttons for controlling whether frequencies are plotted linearly or logarithmically
		self.freqScaleRadioButton_intVar = tk.IntVar()
		tk.Radiobutton(self.scriptManager_TK_Handle, text="linear", variable=self.freqScaleRadioButton_intVar, value=1, command=self.radioButtonPressed_linear).grid(row=20, column=9)
		tk.Radiobutton(self.scriptManager_TK_Handle, text="logarithmic", variable=self.freqScaleRadioButton_intVar, value=2, command=self.radioButtonPressed_logarithmic).grid(row=21, column=9)
		#initialize the value and which button is depressed
		self.freqScaleRadioButton_intVar.set(1)

		#create a checkbox to dictate whether the loop auto-updates the GUI while running.  Can disable auto-updates to prioritize data acquisition and analysis.
		self.checkboxAutoPlot_boolVar = tk.BooleanVar()#create a necessary variable
		self.checkboxAutoplot = tk.Checkbutton(self.scriptManager_TK_Handle, text="enable auto-plotting", variable=self.checkboxAutoPlot_boolVar, onvalue=True, offvalue=False, command=self.buttonPressed_autoPlot)
		#grid the autoplot checkbox
		self.checkboxAutoplot.grid(row=18, column=5)
		#default the checkbox to being either on or off at start of run, depending on how initialization is set in waveformAnalyzerSpecificInitialization (in main script file)
		if(self.scriptManager_TK_Handle.flagAutoPlot):
			self.checkboxAutoplot.select()
		else:
			self.checkboxAutoplot.deselect()


	#handle button presses here
	#quit button was pressed
	def buttonPressed_quit(self):
		print("finishing the program loop")
		self.scriptManager_TK_Handle.mainLoopFlag = False

	#user asked the current PSD to be saved as a reference
	def buttonPressed_savePSDReference(self):
		#change the current summedPSD handle into a reference and move it into the reference list
		referencePSD = self.fourierSpectrumSummedHandle
		self.referencesList.append(referencePSD)
		#the reference handle has now been preserved.  overwrite the active handle name with the current PSD.  User can then clear this new plot while keeping the old reference.
		self.fourierSpectrumSummedHandle, = self.axisFourierSpectrumSummed.plot(self.scriptManager_TK_Handle.frequencyAxisNondegenerate/self.frequencyUnits, self.scriptManager_TK_Handle.summedPSD)

	#user hit the button to clear all previously saved reference PSD's
	def buttonPressed_clearPSDReferences(self):
		numReferences = len(self.referencesList)
		#go through each individual line object and remove each one.
		for i in range(numReferences):
			#remove the current line to be removed from the list
			lineToRemoveNow = self.referencesList.pop(0)
			#delete the line object
			lineToRemoveNow.remove()

	#the button to clear the incoherently summed PSD was pressed.
	def buttonPressed_clearSummedPSD(self):
		print("clearing the incoherently summed Power Spectral Density")
		#get a copy of the old summedPSD, and use it to create a zero-array of the same size.  Use that zero's array to replace the old array
		oldPSD = self.scriptManager_TK_Handle.summedPSD
		self.scriptManager_TK_Handle.summedPSD = np.zeros_like(oldPSD)


	#manual plot update button was pressed.
	def buttonPressed_updatePlots(self):
		print("plots are being updated.")
		self.scriptManager_TK_Handle.flagPlotOnce = True

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


	def radioButtonPressed_linear(self):
		print("setting frequency plot y-scales to linear")
		self.axisZoomedFFT.set_yscale("linear")
		self.axisFourierSpectrumSummed.set_yscale("linear")
		self.axisFourierSpectrumCurrent.set_yscale("linear")
		self.plotScale = "linear"

	def radioButtonPressed_logarithmic(self):
		print("setting frequency plot y-scales to logarithmic")
		self.axisZoomedFFT.set_yscale("log")
		self.axisFourierSpectrumSummed.set_yscale("log")
		self.axisFourierSpectrumCurrent.set_yscale("log")
		self.plotScale = "logarithmic"



#########################################
#methods for handling label and entry interface widgets
#########################################
	def buildEntries(self):
		#create the label and entry for setting the x limits of the display
		#build the lower limit entry field
		self.labelFreqLow = tk.Label(self.scriptManager_TK_Handle, text = "Lower Frequency Limit: ")
		self.labelFreqLow.grid(row=18, column=8, sticky="E")
		self.entryFreqLow = tk.Entry(self.scriptManager_TK_Handle)
		self.entryFreqLow.grid(row=18, column=9)
		self.entryFreqLow.bind('<Return>', self.entryChanged_FreqLowLimit)

		#build the higher limit entry field
		self.labelFreqHigh = tk.Label(self.scriptManager_TK_Handle, text = "Upper Frequency Limit: ")
		self.labelFreqHigh.grid(row=19, column=8, sticky="E")
		self.entryFreqHigh = tk.Entry(self.scriptManager_TK_Handle)
		self.entryFreqHigh.grid(row=19, column=9)
		self.entryFreqHigh.bind('<Return>', self.entryChanged_FreqHighLimit)

		#label the radiobuttons for plotting amplitude either linearly or logarithmically
		self.labelRadioButtons = tk.Label(self.scriptManager_TK_Handle, text="plot frequency amplitudes:")
		self.labelRadioButtons.grid(row=20, column=8)

	#command that is executed when the entry field for the lower x limit is updated.
	#I don't understand tkinter and entries particularly well, but the <Return> binding for entries will call the associated method and pass the key press event.  The call errors if keyPressEvent is not passed in; this method is written to receive the keyPressEvent, but does not do anything with it.
	def entryChanged_FreqLowLimit(self, keyPressEvent):
		#retrieve the new value.  it will be returned as a string.
		newRetrievedValue = self.entryFreqLow.get()
		#convert the retrieved value from string to float.  make sure user didn't insert a typo.
		try:
			newValue = float(newRetrievedValue)
		except ValueError:
			print("Lower frequency limit entry is not a float.")
			return

		#only apply new limit if it's an okay value
		if(newValue < self.freqLimitsHigh):
			#now that the new values have been checked, store them in internal variables
			self.freqLimitsLow = newValue

			#call command to update the xlimits for the plots.  Values do not need to be parsed with the command, the command will be able to access internal variables and submit the current low X and high X.
			self.updateAxisFreqLimits()

	#command that is executed when the entry field for the upper x limit is updated.
	#see 'entryChanged_XLowLimit' comment explaining keyPressEvent.
	def entryChanged_FreqHighLimit(self, keyPressEvent):
		#retrieve the new value.  it will be returned as a string.
		newRetrievedValue = self.entryFreqHigh.get()
		#convert the retrieved value from string to float.  make sure user didn't insert a typo.
		try:
			newValue = float(newRetrievedValue)
		except ValueError:
			print("Upper frequency limit entry is not a float.")
			return

		#only apply new limit if it's an okay value
		if(newValue > self.freqLimitsLow):
			#now that the new values have been checked, store them in internal variables
			self.freqLimitsHigh = newValue

			#call command to update the xlimits for the plots.  Values do not need to be parsed with the command, the command will be able to access internal variables and submit the current low X and high X.
			self.updateAxisFreqLimits()


######################################################
# general utility methods
######################################################
	
	#function to perform normalization of an array.  The input is an array to normalize, the returned value is the array after normalization.
	def normalizeArray(self, arrayToNormalize):
		#use built-in function norm to return the pythagorean length of a n-dimensional array.  What I mean by this, is each component is squared, summed up, and the value returned is the square root of the sum.
		normalizationValue = np.linalg.norm(arrayToNormalize)
		#check that the array isn't empty.
		if normalizationValue == 0:
			#if the array norm is zero, do not divide by it. 
			normedArray = arrayToNormalize
		else:
			#else, divide array to normalize it.
			normedArray = arrayToNormalize/normalizationValue
		#return value
		return normedArray



######################################################
# methods for graphic positioning and construction
######################################################
	
	#method initFigures initializes the figures for the GUI.
	def initFigures(self):
		#initiate the values that will be used as limits in the trace plot outs.
		self.yLimTracesLower = -0.01
		self.yLimTracesUpper = 0.05

		#layout the axes within the figure.  control axis size and distribution by the variables here.
		#spacing variables.  For this method, 'horizontal seam' is a vertical line that spaces two plots across the horizontal axis.  the 'horizontal' in 'horizontalSeam' denotes the horizontal position of the vertical seam.  Likewise, a 'vertical seam' is a horizontal separation that separates the vertical axis.
		horizontalSeamLeft = 0.34
		horizontalSeamRight = 0.66
		verticalSeam = 0.5
		horizontalSpacing = 0.08
		verticalSpacing = 0.08
		##assign positions to individual plots
		#zoomed in trace
		xMinZoomedTrace = horizontalSpacing
		widthZoomedTrace = (horizontalSeamLeft - horizontalSpacing/2) - xMinZoomedTrace
		yMinZoomedTrace =  verticalSeam + verticalSpacing/2
		heightZoomedTrace = (1 - verticalSpacing/2) - yMinZoomedTrace
		#full scale trace
		xMinFullTrace = horizontalSeamLeft + horizontalSpacing/2
		widthFullTrace = (horizontalSeamRight - horizontalSpacing/2) - xMinFullTrace
		yMinFullTrace =  verticalSeam + verticalSpacing/2
		heightFullTrace = (1 - verticalSpacing/2) - yMinFullTrace
		#FFT of zoomed in region
		xMinZoomedFFT = horizontalSpacing
		widthZoomedFFT = (horizontalSeamLeft - horizontalSpacing/2) - xMinZoomedFFT
		yMinZoomedFFT = verticalSpacing
		heightZoomedFFT = (verticalSeam - verticalSpacing/2) - yMinZoomedFFT
		#distribution of rise times
		xMinDistRiseTimes = horizontalSeamRight + horizontalSpacing/2
		widthDistRiseTimes = (1 - horizontalSpacing/2) - xMinDistRiseTimes
		yMinDistRiseTimes = verticalSeam + verticalSpacing/2
		heightDistRiseTimes = (1 - verticalSpacing/2) - yMinDistRiseTimes
		#power spectrum of this current trace
		xMinFourierSpectrumCurrent = horizontalSeamLeft + horizontalSpacing/2
		widthFourierSpectrumCurrent = (horizontalSeamRight - horizontalSpacing/2) - xMinFourierSpectrumCurrent
		yMinFourierSpectrumCurrent = verticalSpacing
		heightFourierSpectrumCurrent = (verticalSeam - verticalSpacing/2) - yMinFourierSpectrumCurrent
		#combined power spectrum
		xMinFourierSpectrumSummed = horizontalSeamRight + horizontalSpacing/2
		widthFourierSpectrumSummed = (1 - horizontalSpacing/2) - xMinFourierSpectrumSummed
		yMinFourierSpectrumSummed = verticalSpacing
		heightFourierSpectrumSummed = (verticalSeam - verticalSpacing/2) - yMinFourierSpectrumSummed

		#create the figure and axis, as prescribed by the position distributions above
		self.figHandle = pyplt.figure(figsize=(9,6))
		self.axisZoomedTrace = self.figHandle.add_axes([xMinZoomedTrace, yMinZoomedTrace, widthZoomedTrace, heightZoomedTrace])
		self.axisFullTrace = self.figHandle.add_axes([xMinFullTrace, yMinFullTrace, widthFullTrace, heightFullTrace])
		self.axisZoomedFFT = self.figHandle.add_axes([xMinZoomedFFT, yMinZoomedFFT, widthZoomedFFT, heightZoomedFFT])
		self.axisDistRiseTimes = self.figHandle.add_axes([xMinDistRiseTimes, yMinDistRiseTimes, widthDistRiseTimes, heightDistRiseTimes])
		self.axisFourierSpectrumCurrent = self.figHandle.add_axes([xMinFourierSpectrumCurrent, yMinFourierSpectrumCurrent, widthFourierSpectrumCurrent, heightFourierSpectrumCurrent])
		self.axisFourierSpectrumSummed = self.figHandle.add_axes([xMinFourierSpectrumSummed, yMinFourierSpectrumSummed, widthFourierSpectrumSummed, heightFourierSpectrumSummed])


#Once the axis are created, they must each be populated with a sample waveform.  Having a special method to initialize each axis with the first waveform is helpful for creating line objects that can then be updated for future waveforms.  Each axis initialization is similar but may be handled slightly differently, depending on the value being plotted.
	def plotInitZoomedTrace(self, zoomedTraceIndices, timeAxisFull, hitIndices):
		#the indices for the zoomed region are supplied.  use them to get the y-values for the zoomed in trace
		fullTrace = self.scriptManager_TK_Handle.lastTraceFull
		zoomedWindowValues = fullTrace[zoomedTraceIndices]
		#get the x-values for full trace
		timeAxisZoom = timeAxisFull[zoomedTraceIndices]
		#get the x-values for the hits
		timeOfHits = timeAxisFull[hitIndices]
		#plot the line and save the line handle object
		self.zoomedTraceHandle, = self.axisZoomedTrace.plot(timeAxisZoom, zoomedWindowValues)
		#initialize the scatter plot collections object
		self.zoomedHitsScatterMarkerHandle = self.axisZoomedTrace.scatter([],[])

		#initiate the plot with the y limit that is set in initFigures()
		self.axisFullTrace.set_ylim(self.yLimTracesLower, self.yLimTracesUpper)

#Once the axis are created, they must each be populated with a sample waveform.  Having a special method to initialize each axis with the first waveform is helpful for creating line objects that can then be updated for future waveforms.  Each axis initialization is similar but may be handled slightly differently, depending on the value being plotted.
	def plotInitFullTrace(self, fullTrace, timeAxis, hitIndices):
		#plot the first full trace, and save the handle for the line object.  future traces will be shown by changing the y-data for the created line object fullTraceHandle
		self.fullTraceHandle, = self.axisFullTrace.plot(timeAxis, fullTrace)
		#initialize the scatter plot object used to indicate where hits were found for a specific trace.
		self.traceHitsScatterMarkerHandle = self.axisFullTrace.scatter([],[])

		#initiate the plot with the y limit that is set in initFigures()
		self.axisFullTrace.set_ylim(self.yLimTracesLower, self.yLimTracesUpper)

#Once the axis are created, they must each be populated with a sample waveform.  Having a special method to initialize each axis with the first waveform is helpful for creating line objects that can then be updated for future waveforms.  Each axis initialization is similar but may be handled slightly differently, depending on the value being plotted.
	def plotInitZoomedFFT(self, zoomedFFT, frequencyAxis):
		self.zoomedFFTHandle, = self.axisZoomedFFT.plot(frequencyAxis/self.frequencyUnits, zoomedFFT)

#Once the axis are created, they must each be populated with a sample waveform.  Having a special method to initialize each axis with the first waveform is helpful for creating line objects that can then be updated for future waveforms.  Each axis initialization is similar but may be handled slightly differently, depending on the value being plotted.
	def plotInitDistRiseTimes(self, distRiseTimes):
		#the line below is temporary and incorrect (5/20/20).  the array distRiseTimes expects to be treated as a histogram.  the current line was hacked together for time conservation while proto-testing
		self.distRiseTimesHandle, = self.axisDistRiseTimes.plot(distRiseTimes)

#Once the axis are created, they must each be populated with a sample waveform.  Having a special method to initialize each axis with the first waveform is helpful for creating line objects that can then be updated for future waveforms.  Each axis initialization is similar but may be handled slightly differently, depending on the value being plotted.
	def plotInitFourierSpectrumCurrent(self, fourierSpectrumCurrent, frequencyAxis):
		self.fourierSpectrumCurrentHandle, = self.axisFourierSpectrumCurrent.plot(frequencyAxis/self.frequencyUnits, fourierSpectrumCurrent)

#Once the axis are created, they must each be populated with a sample waveform.  Having a special method to initialize each axis with the first waveform is helpful for creating line objects that can then be updated for future waveforms.  Each axis initialization is similar but may be handled slightly differently, depending on the value being plotted.
	def plotInitFourierSpectrumSummed(self, fourierSpectrumSummed, frequencyAxis):
		self.fourierSpectrumSummedHandle, = self.axisFourierSpectrumSummed.plot(frequencyAxis/self.frequencyUnits, fourierSpectrumSummed)

		#initialize the internal variables that store the x limits.  These values may be updated later by the user, but need a starting value to reference in the updating methods.
		self.freqLimitsLow, self.freqLimitsHigh = self.axisFourierSpectrumSummed.get_xlim()
		#also initiate the cutoff indices.  These values are the indices corresponding to the set frequency cutoffs.  They can be calculated with the method 'findNewIndexLimits' once freqLimitsLow and freqLimitsHigh are set.
		self.findNewIndexLimits()


	#initialization of WaveformAnalysisGUI's object.
	def __init__(self, tk_RootObject):
		self.scriptManager_TK_Handle = tk_RootObject
		#turn on interactive mode.  needed for dynamic plots
		pyplt.ion()
		#save a constant value that frequency axis will be divided by.  for example, by storing 1e9 in frequencyUnits, all frequencies will be plotted in units of GHz
		self.frequencyUnits = 1e9#the 2pi factor is there to convert from angular frequency to real frequency
		#set the starting scale for FFT plots ("linear" or "logarithmic").
		self.plotScale = "linear"
		#initialize a list that will be used to store plot line handles for references.
		self.referencesList = []

		#initialize the figure and axis positions for the GUI plots.  The axes objects are saved to the self. construct and called later as needed.  actual plotting is handled later.
		self.initFigures()
		######plot initial lines.  Future trace updates will change the data values of line objects constructed within the plotInit methods below
		self.plotInitZoomedTrace(self.scriptManager_TK_Handle.lastZoomIndices, self.scriptManager_TK_Handle.timeValuesFull, self.scriptManager_TK_Handle.lastTraceHits)
		self.plotInitFullTrace(self.scriptManager_TK_Handle.lastTraceFull, self.scriptManager_TK_Handle.timeValuesFull, self.scriptManager_TK_Handle.lastTraceHits)
		self.plotInitZoomedFFT(self.scriptManager_TK_Handle.zoomedRegionPSD, self.scriptManager_TK_Handle.freqAxisZoomedRegion)
		self.plotInitDistRiseTimes(self.scriptManager_TK_Handle.arrayOfRiseTimes)
		self.plotInitFourierSpectrumCurrent(self.scriptManager_TK_Handle.lastTracePSD, self.scriptManager_TK_Handle.frequencyAxisNondegenerate)
		self.plotInitFourierSpectrumSummed(self.scriptManager_TK_Handle.summedPSD, self.scriptManager_TK_Handle.frequencyAxisNondegenerate)

		#pack the figure onto the canvas
		self.canvasHandle = FigureCanvasTkAgg(self.figHandle, master=self.scriptManager_TK_Handle)
		self.canvasHandle.get_tk_widget().grid(row=0, column=0, rowspan=18, columnspan=12)

		#method buildButtons creates all the buttons, packs them, and sorts them out as to which command each of them trigger.
		self.buildButtons()

		#method buildEntries creates and packs the entry fields for values supplied by the user
		self.buildEntries()