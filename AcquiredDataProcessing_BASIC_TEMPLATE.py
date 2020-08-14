import re
import numpy as np
import matplotlib.pyplot as plt

#denote the byte size of the native data structure that the data is formatted in.  For example, if binary data represents float64, set the variable 'savedDataTypeSizeInBytes' to '8'
savedDataTypeSizeInBytes = 8
#denote the data type to interpret the binary data with.  Should be float64, unless trace files are worked with.  for .trc files, float32 seems to be expected.
dt = np.dtype("float64")

#write in data file names
dataFileName = "2020_08_08_18_54_00"
headerFileName = dataFileName + "_HEADER.txt"
#write in directory that contains data files.  please keep the slash at the end to indicate being inside the folder.
folderName = "C:/Users/andre/Desktop/100V_lowGas_tightIris/"







#################
#LOAD IN DATA
#################
#this section loads in the raw data and prepares everything necessary for data extraction.  USER MUST WRITE IN FILE AND FOLDER NAMES IN THE BLOCK ABOVE THIS COMMENT.

#set up to load binary data in.  use "rb" to indicate read only from binary for data file
dataFile = open(folderName + dataFileName, "rb")
#set up read only for ascii format header file.
headerFile = open(folderName + headerFileName, "r")

#extract the individual trace size from the header.  Done using imported library re (regular expressions)
for line in headerFile:
	match = re.search("The size of an individual bit of binary data is: (\d+)", line)
	if match:
		#code has found where the trace size is saved in the header, and extracts that value.
		traceDataSize = int(match.group(1))

# #block of code for debugging
# segmentNowStart = 0
# dataFile.seek(segmentNowStart)
# segmentNow = dataFile.read(traceDataSize)
# traceNow = np.frombuffer(segmentNow, dtype=dt)
# plt.plot(traceNow)
# plt.show()
# print(segmentNowStart)

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
		#a normal, complete trace has been extracted.  This section may be used to process traces as desired by user.  New traces will be fed into this region until they are exhausted.  The variable for the current new trace is 'traceNow'.  Please note that this is within a loop, so it may be good to save to variables, and access the variables after the present while loop is exhausted.


		pass



#################
#SECTION TO CLOSE OUT THE RUN AND CLEAN UP
#################
#close out files
headerFile.close()
dataFile.close()