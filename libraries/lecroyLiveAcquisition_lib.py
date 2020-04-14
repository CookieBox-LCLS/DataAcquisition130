import win32com.client
app = win32com.client.Dispatch("LeCroy.XStreamDSO")

#dataIsReadyForReadout returns boolean True or False 
def dataIsReadyForReadout():
	waveformReady = app.Acquisition.Acquire(1, False)
	return waveformReady

def readInDataFromScope_c1():
	newWaveform = app.Acquisition.C1.Out.Result.DataArray
	return newWaveform