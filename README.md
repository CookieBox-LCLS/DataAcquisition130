# DataAcquisition130
this repository is for software developed to acquire eToF data using the prototype setup in laser lab 130.

The goal of this repository is to create a program that acquires data from the prototyping hardware in lab 130, saves it, and provides feedback via GUI to the user performing the acquisition.  The vision for the program is to have a master loop which directs the workings of the code by calling methods.  The methods are to be imported from individual libraries associated with different hardware, such that the method names within the main loop do not change, but the functions that are imported in their names are swapped out as the acquisition hardware evolves.

The code uses the python library tkinter to create and manage a GUI while the data acquisition is active.  There are two class objects that interact with each other to make the program functional.  Class 'MainScriptManager_TK' is a class inherited from 'tkinter.Tk' - it inherits all of tkinter's structure that enables it to update a visual box while also running a loop.

# installation and setup
1) go into 'DataAcquisition130.py and look at the block of code near the top between 'import sys' and 'import numpy as np'.  If the code is being installed on the oscilloscope, set 'runningOnScope' to 'True'.  If being installed on a laptop to simulate data acquisition, set 'runningOnScope' to 'False'.
2) Note that for either option, there are some directories that need to be set.  Note that regardless of operating system, slashes in directory names ought to be either '/' (recommended) or '\\'.  '\' which is used on windows machines, is a native character in python and messes thigns up.  Python uses '\\' as a recognized alternate.
-'saveToDirectory' represents the directory to which data will be saved out.  note that this is the only directory name that needs to end in a slash
-the directory that houses the libraries for this code must be added to the system path using the 'sys.path.append(...)' command.
-if simulating from .trc files that are already on the host machine, the used must go into 'simulatingWithCollectedData_lib.py' and set the directory variable 'dataFolderDirectory' to reflect the directory that has the .trc source files.
3) At the top of generalPurposeProcessing_lib.py, the line:
from CFD_lib import ______ as CFD
can be used to select which CFD method to use.  the ______ should be a method that exists in CFD_lib.py


# File descriptions
# DataAcquisition130.py 
The main script for the program.  It contains the class 'MainScriptManager_TK' which is needed to manage tkinter's functionality.  The class needs to be instantiated through it's inherited Main() constructor - otherwise the tkinter features will fail to work correctly.  A secondary initialization command is called shortly after creation, 'postConstructionClassInitialization', which initiates most of the program-specific needs.  During initialization, an object of class 'DataAcqGUI' is created and interacted with heavily.  After initialization, class 'MainScriptManager_TK' enters its main loop program which focuses on data acquisition and processing.  Data presentation and GUI handling is controlled by class 'DataAcqGUI' in plottingAndGUI_lib.

# plottingAndGUI_lib.py
this library describes and manages the class 'DataAcqGUI', which handles all the user input and graphical presentation of the data as it is accumulated, through the tkinted library.  An object of this class is constructed at secondary initialization of 'MainScriptManager_TK' in DataAcqiusition130.py, and has direct access to all the variables of the 'MainScriptManager_TK' object.  The object of 'DataAcqGUI' thus has access to all variables that have been accumulated by the main program loop and will often call on the main program variables directly.  The object also uses the object version of 'MainScriptManager_TK' to use tkinter's capabilities.

# generalPurposeProcessing_lib
this library has a lot of the functions that handle signal processing to help find hits within a raw trace.  it imports a CFD method from CFD_lib.  The user can select which method from CFD_lib is imported as CFD, thereby selecting a version of CFD to use.

# CFD_lib
this library hosts the unique CFD methods that can be imported in generalPurposeProcessing_lib.

# lecroyLiveAcquisition_lib
Hosts methods that are used to acquire data with the use of the teledyne lecroy setup.

# simulatingWithCollectedData_lib
contains methods that are needed to run the GUI acquisition program on .trc files that were previously acquired.  If the user uses these, they must specify the directory that has all the .trc files in this library.

if the user wishes to run this GUI on .trc files acquired from previous runs
