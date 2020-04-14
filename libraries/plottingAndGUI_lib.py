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
		self.rawTraceHandle, = self.axisRawTrace.plot(histogramSample)
		self.axisRawTrace.set_ylim(0, 0.1)

#########################################################
#functions for updating the GUI
#########################################################

	#updatePlotsMaster is a function that update the plots individually.  this is done as a separate method to help prevent the main loop from getting too long to read on it's own, and to help keep the code well organized
	def updatePlotsMaster(self, histogramToPlot, newTrace):
		#update the histogram
		self.updateHistogram(histogramToPlot)
		#update the trace that is on display with a new trace
		self.updateTrace(newTrace)

		#allow plots to be updated
		self.canvasHandle.draw()
		self.scriptManager_TK_Handle.update()

		return

	#update the histogram plot with new data that is provided
	def updateHistogram(self, newHistogram):
		self.histogramHandle.set_ydata(newHistogram)
		yLimitHigh = np.amax(newHistogram) + 1
		self.axisHistogram.set_ylim(0, yLimitHigh)

	def updateTrace(self, newTrace):
		self.rawTraceHandle.set_ydata(newTrace)

	#########################################
	#methods for handling interface widgets (buttons, entries, etc)
	#########################################
	#create and pack buttons.  also dictate which commands they are to execute should they be pressed.
	def packButtons(self):
		#create a dummy button for demo purposes for now.
		self.button_left = tk.Button(self.frame,text="finish the current run", command=self.buttonPressed_quit)
		self.button_left.pack(side="left")


		#handle button presses here
	def buttonPressed_quit(self):
		print("finishing the program loop")
		self.scriptManager_TK_Handle.mainLoopFlag = False


	def packEntries(self):
		breakpoint()
		self.entryXLow = tk.Entry(self.scriptManager_TK_Handle)
		self.entryXHigh = tk.Entry(self.scriptManager_TK_Handle)
		self.entryXLow.pack(side="right")
		self.entryXHigh.pack(side="right")

######################################################
# methods for graphic positioning and construction
######################################################
	#method initFigures makes the figures for the GUI.  it handles all the layout of the figures and creates teh axes objects.
	def initFigures(self):
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


	#initialization of DataAcqGUI object.
	def __init__(self, tk_RootObject):
		self.scriptManager_TK_Handle = tk_RootObject
		#turn interactive mode on.  needed for plots to be dynamic.
		pyplt.ion()
		#construct a GUI frame linked to the tk master object
		self.frame = tk.Frame(self.scriptManager_TK_Handle)
		#initialize the figures and all the axes for the GUI.
		self.initFigures()
		#initialize the inidividual plots.  this is done so that line objects are created and future plot updates can be done by changing the y_data without recreating the figure.
		self.plotInitHistogram(self.scriptManager_TK_Handle.histogramCollected)
		self.plotInitRawTrace(self.scriptManager_TK_Handle.histogramCollected)

		#pack the figure onto the canvas
		self.canvasHandle = FigureCanvasTkAgg(self.figHandle, master=self.scriptManager_TK_Handle)
		self.canvasHandle.get_tk_widget().pack(side='top', fill='both', expand=1)
		
		#method packButtons creates all the buttons, packs them, and sorts them out as to which command each of them trigger.
		self.packButtons()

		#method packEntries creates and packs the entry fields for values supplied by the user
		#self.packEntries()

		#pack the created frame onto the tkinter object (linked to root via frame's constructor, linked to current class for convenient access)
		self.frame.pack()