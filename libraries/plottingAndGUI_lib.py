import matplotlib.pyplot as pyplt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np	
import tkinter as tk
import time

#initialize histogram is used to create an array for the collected histogram.  at initialization, it is an array of zero's, the same size as a raw data trace
def initializeHistogram(rawData):
	histogram = np.zeros(len(rawData), dtype=int)
	return histogram


#addHitsToHistogram takes the indexes listed in 'newHits', and increments the respective bins in the array 'histogram'.  the method returns the updated version of 'histogram'
def addHitsToHistogram(newHits, histogram):
	#for each of the new hits in the array 'newHits',
	for ind in range(len(newHits)):
		#isolate the hit index
		hitIndexNow = newHits[ind].item()
		#and increment the respective bin in 'histogram'
		histogram[hitIndexNow] += 1

	return histogram




##################################################
#GUI CLASS
##################################################
class DataAcqGUI:

	#use plotInitHistogram to initialize the histogram plot.  this is done only at startup.  future histograms are plotted by changing the data of the plotted trace, which is created once with this method.
	def plotInitHistogram(self, histogramSample):
		self.histogramHandle, = self.axisHistogram.plot(histogramSample)

	def plotInitRawTrace(self, histogramSample):
		#initialize the raw trace
		self.rawTraceHandle, = self.axisRawTrace.plot(histogramSample)
		self.axisRawTrace.set_ylim(0, 0.1)
		#initialize the scatter plot object used to indicate where hits were found for a specific trace.
		self.traceHitsScatterMarkerHandle = self.axisRawTrace.scatter([],[])

		#initialize the internal variables that store the x limits.
		self.plotLimitsXLow, self.plotLimitsXHigh = self.axisRawTrace.get_xlim()


#########################################################
#functions for updating the GUI
#########################################################

	#updatePlotsMaster is a function that update the plots individually.  this is done as a separate method to help prevent the main loop from getting too long to read on it's own, and to help keep the code well organized
	def updatePlotsMaster(self, histogramToPlot, newTrace, traceHitIndices):
		#update the histogram
		self.updateHistogram(histogramToPlot)
		#update the trace that is on display with a new trace
		self.updateTrace(newTrace, traceHitIndices)

		#allow plots to be updated
		self.canvasHandle.draw()
		self.scriptManager_TK_Handle.update()

		return

	#update the histogram plot with new data that is provided
	def updateHistogram(self, newHistogram):
		self.histogramHandle.set_ydata(newHistogram)
		yLimitHigh = np.amax(newHistogram) + 1
		self.axisHistogram.set_ylim(0, yLimitHigh)

	#update the raw trace plot with latest trace provided by the execution loop
	def updateTrace(self, newTrace, traceHitIndices):
		self.rawTraceHandle.set_ydata(newTrace)
		#traceHitIndices is fed in as a awkward structure.  re-format it into a simple list
		traceHitIndicesListFormat = [x[0] for x in traceHitIndices]
		#get the y-values for the hits
		traceHitValues = newTrace[traceHitIndicesListFormat]
		#remove the previous scatter plot
		self.axisRawTrace.collections[0].remove()
		#plot the scatter points for the current trace
		self.axisRawTrace.scatter(traceHitIndicesListFormat, traceHitValues)


	#the command 'updateAxisXLimits' will command the relevant plot axis to update the x-limits to display between.  The actual values for the x limits must be pre-loaded into the GUI's internal variables 'self.plotLimitsXLow' and 'self.plotLimitsXHigh'
	def updateAxisXLimits(self):
		self.axisHistogram.set_xlim(self.plotLimitsXLow, self.plotLimitsXHigh)
		self.axisRawTrace.set_xlim(self.plotLimitsXLow, self.plotLimitsXHigh)

	#########################################
	#methods for handling button interface widgets
	#########################################
	#create and grid buttons.  also dictate which commands they are to execute should they be pressed.
	def buildButtons(self):
		#create a button to update the plots now.  this is needed in case the run loop is having a hard time keeping up with the data acquisition rate
		self.button_updatePlots = tk.Button(self.scriptManager_TK_Handle,text="update plots NOW", command=self.buttonPressed_updatePlots)
		self.button_updatePlots.grid(row=8, column=17)

		#create a button to exit out of the program
		self.button_quit = tk.Button(self.scriptManager_TK_Handle,text="finish the current run", command=self.buttonPressed_quit)
		self.button_quit.grid(row=9, column=17)


	#handle button presses here
	#quit button was pressed
	def buttonPressed_quit(self):
		print("finishing the program loop")
		self.scriptManager_TK_Handle.mainLoopFlag = False

	#manual plot update button was pressed.
	def buttonPressed_updatePlots(self):
		print("plots are being updated.")
		self.updatePlotsMaster(self.scriptManager_TK_Handle.histogramCollected, self.scriptManager_TK_Handle.lastTrace)


#########################################
#methods for handling entry interface widgets
#########################################
	def buildEntries(self):
		#create the label and entry for setting the x limits of the display
		#build the lower limit entry field
		self.labelXLow = tk.Label(self.scriptManager_TK_Handle, text = "Lower X Limit: ")
		self.labelXLow.grid(row=8, column=0)
		self.entryXLow = tk.Entry(self.scriptManager_TK_Handle)
		self.entryXLow.grid(row=8, column=1)
		self.entryXLow.bind('<Return>', self.entryChanged_XLowLimit)

		#build the higher limit entry field
		self.labelXHigh = tk.Label(self.scriptManager_TK_Handle, text = "Upper X Limit: ")
		self.labelXHigh.grid(row=9, column=0)
		self.entryXHigh = tk.Entry(self.scriptManager_TK_Handle)
		self.entryXHigh.grid(row=9, column=1)
		self.entryXHigh.bind('<Return>', self.entryChanged_XHighLimit)

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
		yMinHist = verticalSpacing
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

		#create the figure and axis, as prescribed by the setup above
		self.figHandle = pyplt.figure(figsize=(12,9))
		self.axisHistogram = self.figHandle.add_axes([xMinHist, yMinHist, widthHist, heightHist])
		self.axisRawTrace = self.figHandle.add_axes([xMinTrace, yMinTrace, widthTrace, heightTrace])
		self.axisRateDistribution = self.figHandle.add_axes([xMinRateDistribution, yMinRateDistribution, widthRateDistribution, heightRateDistribution])


	#initialization of DataAcqGUI object.
	def __init__(self, tk_RootObject):
		self.scriptManager_TK_Handle = tk_RootObject
		#turn interactive mode on.  needed for plots to be dynamic.
		pyplt.ion()

		#initialize the figures and all the axes for the GUI.  The plot structures themselves are created in initFigures, and the plot lines are handled in separate methods later
		self.initFigures()
		#initialize the inidividual plots.  this is done so that line objects are created and future plot updates can be done by changing the y_data without recreating the figure.
		self.plotInitHistogram(self.scriptManager_TK_Handle.histogramCollected)
		#initialize the plot for the raw trace.
		#the internal x limit variables are created and saved as part of 'plotInitRawTrace'
		self.plotInitRawTrace(self.scriptManager_TK_Handle.histogramCollected)

		#pack the figure onto the canvas
		self.canvasHandle = FigureCanvasTkAgg(self.figHandle, master=self.scriptManager_TK_Handle)
		#self.canvasHandle.get_tk_widget().pack(side='top', fill='both', expand=1)
		self.canvasHandle.get_tk_widget().grid(row=0, column=0, rowspan=8, columnspan=18)
		
		#method buildButtons creates all the buttons, packs them, and sorts them out as to which command each of them trigger.
		self.buildButtons()

		#method buildEntries creates and packs the entry fields for values supplied by the user
		self.buildEntries()
