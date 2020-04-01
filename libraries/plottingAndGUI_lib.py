import matplotlib.pyplot as pyplt


#initializeGUI is here to produce the figure and axes on which plots will be handled witht he GUI
def initializeGUI():
	figure, axis = pyplt.subplots()
	return figure, axis

#updatePlotsMaster is a function that update the plots individually.  this is done as a separate method to help prevent the main loop from getting too long to read on it's own, and to help keep the code well organized
def updatePlotsMaster(figureIn, axesIn):
	#for each axes
	pyplt.sca(axesIn)
	