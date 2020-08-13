import re
import numpy as np
import matplotlib.pyplot as plt
import sys
#add library subfolder
sys.path.append("C:/Users/andre/Documents/GitHub/DataAcquisition130/libraries")
#import functions in library subfolder
from generalPurposeProcessing_lib import returnWaveformAndHits as onTheFlyProcessing
from generalPurposeProcessing_lib import writeOutRawData as writeOut
from generalPurposeProcessing_lib import generateNewFileAndHeader as generateNewFileAndHeader
from generalPurposeProcessing_lib import initializeHistogram
from generalPurposeProcessing_lib import addHitsToHistogram
from generalPurposeProcessing_lib import addToHitRateDistribution
from generalPurposeProcessing_lib import updateHitRateRunningWindow
from TOFtoEnergyConversion_lib import calculateOverlapMatrixTOFtoEnergy

#denote the byte size of the native data structure that the data is formatted in.  For example, if binary data represents float64, set the variable 'savedDataTypeSizeInBytes' to '8'
savedDataTypeSizeInBytes = 8
#denote the data type to interpret the binary data with.  Should be float64, unless trace files are worked with.  for .trc files, float32 seems to be expected.
dt = np.dtype("float64")

#write in directory that contains data files.  please keep the slash at the end to indicate being inside the folder.
#also write in the actual data file name.  Header file is inferred from data file name.

# #40V data
#folderName = "C:/Andrei/ScopeCollect/toKeep/ATI_at_40V/"
#dataFileName = "2020_08_08_17_19_34"

# #60V data
#folderName = "C:/Andrei/ScopeCollect/toKeep/60V/"
#dataFileName = "2020_08_08_17_30_13"

# #100V data
#folderName = "C:/Users/andre/Desktop/100V_lowGas_tightIris/"
#dataFileName = "2020_08_08_18_54_00"

 #pre-Beam movement walkway
folderName = "C:/Andrei/ScopeCollect/pre_movement/walkwaySide/"
dataFileName = "2020_08_08_20_17_27"

 #pre-Beam movement tableside
#folderName = "C:/Andrei/ScopeCollect/pre_movement/tableSide/"
#dataFileName = "2020_08_08_20_08_30"

 #low pressure table side measurement
#folderName = "C:/Andrei/ScopeCollect/lowPressureTableSide/"
#dataFileName = "2020_08_08_20_53_59"

 #post movement 1
#folderName = "C:/Andrei/ScopeCollect/post_movement/tableSideTof/"
#dataFileName = "2020_08_08_21_29_27"

# #post movement 2
#folderName = "C:/Andrei/ScopeCollect/post_movement2/tableToF/"
#dataFileName = "2020_08_08_21_49_11"

# #post movement 2
#folderName = "C:/Andrei/ScopeCollect/post_movement2/walkwaySide/"
#dataFileName = "2020_08_08_21_40_42"


headerFileName = dataFileName + "_HEADER.txt"



#################
#HELPER METHODS SECTION
#################

#bin a raw histogram into the bin width specified by the user.  return a plot line's y-values to resemble histogram blocks, but be of the same length as the input variable 'rawHistogram'
def calculateBinnedHistogramTrace(rawHistogram, binWidth):
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

#make a binned histogram plot, between the select x-limits
def singleBinnedPlot(fullHistogram, binWidth, xLimLow, xLimHigh):
	binnedHistogram = calculateBinnedHistogramTrace(fullHistogram, binWidth)
	#make the plot
	plt.figure(figsize=(14,10))
	plt.plot(binnedHistogram)
	plt.xlim(xLimLow, xLimHigh)
	maxHeight = 1.05*np.amax(binnedHistogram)
	plt.ylim(0, maxHeight)
	plt.title("Histogram Binned with Width %d" % (binWidth), fontsize=26)
	plt.show()



#simpleMethod to generate some simple plots.  xlimits expected in index
def makeHistogramPlotsSimple(fullHistogram, binWidth, xLimLow, xLimHigh):
	binnedHistogram = calculateBinnedHistogramTrace(fullHistogram, binWidth)

	#make plot of full scale histogram, no binning
	plt.figure(figsize=(14,10))
	plt.plot(fullHistogram)
	plt.xlim(0, len(fullHistogram))
	maxHeight = 1 + np.amax(fullHistogram)
	plt.ylim(0, maxHeight)
	plt.title("Unbinned histogram", fontsize=30)
	plt.show()
	#plot the full scale histogram, with binning
	singleBinnedPlot(fullHistogram, binWidth, 0, len(fullHistogram))
	#make the zoomed in plot for the unbinned plot
	plt.figure(figsize=(14,10))
	plt.plot(fullHistogram)
	plt.xlim(xLimLow, xLimHigh)
	maxHeight = 1 + np.amax(fullHistogram[xLimLow:xLimHigh])
	plt.ylim(0, maxHeight)
	plt.title("Unbinned histogram, zoomed in", fontsize=30)
	plt.show()
	#make the zoomed in plot for the binned plot
	singleBinnedPlot(fullHistogram, binWidth, xLimLow, xLimHigh)



#################
#START OF SCRIPT
#################


#################
#LOAD IN DATA
#################
#this section loads in the raw data and prepares everything necessary for data extraction.  USER MUST WRITE IN FILE AND FOLDER NAMES IN THE APPROPRIATE BLOCK SOMEWHERE IN THE HEADER

#set up to load binary data in.  use "rb" to indicate read only from binary for data file
dataFile = open(folderName + dataFileName, "rb")
#set up read only for ascii format header file.
headerFile = open(folderName + headerFileName, "r")

#extract the individual trace size from the header.  Done using imported library re (regular expressions)
for line in headerFile:
	match = re.search("The size of an individual bit of binary data is: (\d+)", line)
	if match:
		#WARNING!!!  Andrei had a misunderstanding of file saving when the data acquisition code was written.  As a result, the value in the header is 96 bytes larger than the true trace size.  The line below compensates for this mistake, the 96 subtraction is critical for correct data readout.
		traceDataSize = (int(match.group(1)) - 96)

#################
#PROCESS SAVED RAW DATA
#################
#setup variables that are useful for each run
tracesProcessed = 0
#default the reading loop condition to true
moreToRead = True
#loop through each trace
while moreToRead:
	#try reading in data.  
	segmentNow = dataFile.read(traceDataSize)
	#convert binary segment into a numpy array of appropriate data type
	traceNow = np.frombuffer(segmentNow, dtype=dt)


	if(len(traceNow) == 0):
		moreToRead = False
		print("The end of file was reached, with 0 bytes in the final read")
	elif(len(traceNow) < traceDataSize/savedDataTypeSizeInBytes):
		print("A trace was read in with a byte size that is not equal to the size prescribed in the header file.")
	else:
		#a normal, complete trace has been extracted.  This section may be used to process traces as desired by user.

		#perform processing similar to that done on the o-scope
		rawData, hitIndices = onTheFlyProcessing(traceNow)

		#if this is the first trace, set up some variables for the first time
		if(tracesProcessed == 0):
			histogramCollected = initializeHistogram(rawData)

		#add hits found in this trace to the histogram
		histogramCollected = addHitsToHistogram(hitIndices, histogramCollected)


		tracesProcessed = tracesProcessed + 1
		pass



#################
#SECTION TO MAKE PLOTS FROM PROCESSED DATA
#################
binWidthForPlot = 5
xLimLow = 2000
xLimHigh = 5000

makeHistogramPlotsSimple(histogramCollected, binWidthForPlot, xLimLow, xLimHigh)

#singleBinnedPlot(histogramCollected, 5, 2000, 3500)


#################
#SECTION TO CLOSE OUT THE RUN AND CLEAN UP
#################
#close out files
headerFile.close()
dataFile.close()