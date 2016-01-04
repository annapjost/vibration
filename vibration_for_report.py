from ij import IJ, ImagePlus, ImageStack
from ij import WindowManager as WM
from ij.io import OpenDialog
from ij.measure import ResultsTable
from fiji.util.gui import GenericDialogPlus
from ij.gui import GenericDialog
import os
import math

def plotPoint(allpointslist, xory, point):
    plot = Plot(xory + " bead " + str(point), "timepoint", "position (nm)", [], [])
    plot.addPoints(range(len(allpointslist[point])), allpointslist[point], Plot.LINE)
    plot_window = plot.show() 
    
def getResultsXCsYCs():
    '''grabs the XC and YC columns from the results table output from gaussfit_onspot plugin'''
    #grab the results table:
    rt = ResultsTable.getResultsTable()
    #initialize the lists for xcs and ycs:
    XCs = []
    YCs = []
    size = rt.size()
    # now loop through each row in the results table 
    for row in range(size):
        xc = rt.getValue("XC", row)
        yc = rt.getValue("YC", row)
        XCs.append(xc)
        YCs.append(yc)
    return (XCs, YCs, size)

def isFrames(imp):
    """Determine whether the stack has >1 slices or >1 frames"""
    NSlices = imp.getNSlices()
    NFrames = imp.getNFrames()
    if NSlices == 1 and NFrames != 1:
        return True
    elif NSlices != 1 and NFrames == 1:
        return False
    else:
        IJ.log("stack dimension error!")

def getCal(imp):
    """Get pixel size calibration (in nm) from image unless it is uncalibrated"""
    imp = IJ.getImage()
    cal = imp.getCalibration()
    if cal.unit == 'pixel':
        return False
    else:
        scale = cal.pixelWidth*1000
        return scale            
        
def findApproveMaxima(imp, start):
    """set appropriate noise tolerance for Find Maxima by trial and error"""
    gd = GenericDialogPlus('noise tolerance')
    gd.addStringField('starting noise tolerance: ', start)
    gd.showDialog()
    noise = gd.getNextString()
    IJ.run("Find Maxima...", "noise=" + str(noise) + " output=[Point Selection] exclude")
    approved = False
    while True:
        gd = GenericDialog('confirm noise tolerance')
        gd.addMessage('are you happy with maxima?')
        gd.enableYesNoCancel()
        gd.showDialog()
        if gd.wasOKed():
            return noise
            approved = True
        elif gd.wasCanceled():
            return False
        else:
            gd = GenericDialogPlus('enter new noise tolerance')
            gd.addStringField('new noise tolerance: ', str(noise))
            gd.showDialog()
            noise = gd.getNextString()
            IJ.run("Find Maxima...", "noise=" + str(noise) + " output=[Point Selection] exclude")

def findAndFit(noise, scale):      #might not be a bad idea to have optional inputs here as tags...
    """Given a noise tolerance for Find Maxima and a pixel size scale for GaussFit OnSpot, 
    does a Gaussian fit for each maxima and reports coordinates in nm"""
    imp = IJ.getImage()
    stack = imp.getImageStack()
    IJ.run("Find Maxima...", "noise=" + str(noise) + " output=[Point Selection] exclude")
    #add something here for the user to review the maxima? make interactive?
    # could also do some looping to make sure there are the right number of beads in 
    # the FOV (would have to add instructions for users to crop appropriately)
    if isFrames(imp):
        stacksize = imp.getNFrames()
    else:
        stacksize = imp.getNSlices()

    xtimepoints = []
    ytimepoints = []
    
    
    for slice in range(stacksize):
        #set working slice
        imp.setSlice(slice)
        #do the fit for the working slice
        IJ.run("GaussFit OnSpot", "shape=Circle fitmode=[Levenberg Marquard] rectangle=4 pixel=" + str(scale) + " max=500 cpcf=1 base=100")
        # use the function that will loop through the results table and grab all the values
        #values are returned as lists.  
        (XCs, YCs, numpoints) = getResultsXCsYCs()
        #now, we add the list of point values to the timepoint lists.  each of these lists
        # will contain an entry for each timepoint, containing a list of X or Y values
        # for each point.
        xtimepoints.append(XCs)
        ytimepoints.append(YCs)
        
    return xtimepoints, ytimepoints, numpoints

def average(x):
    average = sum(x)*1.0/len(x)
    return average

def stdev(s):
    avg = sum(s)*1.0/len(s)
    variance = map(lambda x: (x-avg)**2, s)
    return math.sqrt(average(variance))

def vibration(startnoise):
    imp = IJ.getImage()
    
    scale = getCal(imp)
    if scale == False:
        gd = GenericDialogPlus('enter calibration')
        gd.addStringField('pixel size (nm): ', None)
        gd.showDialog()
        scale = gd.getNextString()
    
    
    noise = findApproveMaxima(imp, str(startnoise))
    
    xtimepoints, ytimepoints, numpoints = findAndFit(noise, scale)
    
    allpointsx = []
    for point in range(numpoints):
    	points = []
    	for time in range(len(xtimepoints)):
    		current = xtimepoints[time]
    		points.append(current[point])   
    	allpointsx.append(points)
    
    allpointsy = []
    for point in range(numpoints):
    	points = []
    	for time in range(len(ytimepoints)):
    		current = ytimepoints[time]
    		points.append(current[point])   
    	allpointsy.append(points)    
    
    #now, allpoints is a list of points.  each entry contains every timepoint for that point.
    
    # generate stdevs in x and y separately 
    xstdevs = []
    ystdevs = [] 
    
    for point in range(numpoints):
    	std = stdev(allpointsx[point])
    	xstdevs.append(std)
    
    for point in range(numpoints):
    	std = stdev(allpointsy[point])
    	ystdevs.append(std)
    
    return average(xstdevs), average(ystdevs)
    #avgxstdev = average(xstdevs)
    #avgystdev = average(ystdevs)
    # the stdevs reported here are an average of all points!

def run():
	"""Runs vibration function on the contents of a directory.  Needs work to be generalizable.
		Designed based on this: 
		http://fiji.sc/Scripting_toolbox#Opening.2C_processing.2C_and_saving_a_sequence_of_files_in_a_folder"""
    srcDir = IJ.getDirectory("Input_directory")
    if not srcDir:
        return
    ext = ".tif"
    # get scale - assumes same scale for all files in folder
    gd = GenericDialogPlus('enter calibration')
    gd.addStringField('pixel size (nm): ', None)
    gd.showDialog()
    scale = float(gd.getNextString())/1000.0
    #open an image to get starting noise tolerance
    dirs = os.listdir(srcDir)
    file = dirs[1]
    IJ.open(os.path.join(srcDir, file))
    imp = IJ.getImage()
    startnoise = str(findApproveMaxima(imp, "10"))
    imp.close()
    for root, directories, filenames in os.walk(srcDir):
        for filename in filenames:
            # Check for file extension
            if not filename.endswith(ext):
                continue
            x, y = process(srcDir, root, filename, scale, startnoise)
            IJ.log(filename)
            IJ.log(str(x))
            IJ.log(str(y))
            
            
def process(srcDir, currentDir, filename, scale, startnoise):
    # Open the image
    IJ.open(os.path.join(currentDir, filename))
    imp = IJ.getImage()
    IJ.run("Set Scale...", "distance=1 known=" + str(scale) + " unit=micron")
    # run the vibration analysis!  
    x, y = vibration(startnoise)  
    imp.close()     
    return x, y 
      
run()