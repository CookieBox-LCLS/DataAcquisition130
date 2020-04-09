import matplotlib.pyplot as pyplt
import numpy as np	

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


#########################################################
#functions for updating the GUI
#########################################################

#updatePlotsMaster is a function that update the plots individually.  this is done as a separate method to help prevent the main loop from getting too long to read on it's own, and to help keep the code well organized
def updatePlotsMaster(GUIHandle, histogramToPlot, newTrace):
	#update the histogram
	GUIHandle.updateHistogram(histogramToPlot)
	#update the trace that is on display with a new trace
	GUIHandle.updateTrace(newTrace)

	#allow plots to be updated
	pyplt.pause(0.000001)
	pyplt.show()

	return




#initializeGUI is here to produce the figure and axes on which plots will be handled witht he GUI
def initializeGUI(histogramSample):
	#enable interactive mode.  this is needed to make the plot figure more dynamic
	pyplt.ion()

	#create the GUI class object.  the GUI figure is handled as a class to more cleanly wrap up the methods and variables needed to run the GUI.
	GUIHandle = GUI_Class()
	#pass in a sample histogram.  this is needed so that the initial plotting can be done.  Future plotting is made faster by changing out the data within the figure, but not re-creating the figure itself.
	GUIHandle.plotInitHistogram(histogramSample)
	GUIHandle.plotInitRawTrace(histogramSample)

	return GUIHandle



##################################################
#GUI CLASS
##################################################
class GUI_Class():

	#use plotInitHistogram to initialize the histogram plot.  this is done only at startup.  future histograms are plotted by changing the data of the plotted trace, which is created once with this method.
	def plotInitHistogram(self, histogramSample):
		self.histogramHandle, = self.axisHistogram.plot(histogramSample)

	def plotInitRawTrace(self, histogramSample):
		self.rawTraceHandle, = self.axisRawTrace.plot(histogramSample)
		self.axisRawTrace.set_ylim(0, 0.1)

	#update the histogram plot with new data that is provided
	def updateHistogram(self, newHistogram):
		self.histogramHandle.set_ydata(newHistogram)
		yLimitHigh = np.amax(newHistogram) + 1
		self.axisHistogram.set_ylim(0, yLimitHigh)

	def updateTrace(self, newTrace):
		self.rawTraceHandle.set_ydata(newTrace)

	#initialization of GUI_Class object.
	def __init__(self):
		#layout the axes within the figure.  controlled via these variables
		#spacing variables
		verticalSpacing = 0.05
		horizontalSpacing = 0.05
		#assign positions to the histogram plot
		xMinHist = 0.05
		widthHist = 0.7
		yMinHist = 0.5
		heightHist = 0.95 - yMinHist
		#assign positions to the raw trace plot
		xMinTrace = xMinHist
		widthTrace = widthHist
		yMinTrace = 0.1
		heightTrace = yMinHist - yMinTrace - verticalSpacing

		self.figHandle = pyplt.figure(figsize=(12,9))
		self.axisHistogram = self.figHandle.add_axes([xMinHist, yMinHist, widthHist, heightHist])
		self.axisRawTrace = self.figHandle.add_axes([xMinTrace, yMinTrace, widthTrace, heightTrace])