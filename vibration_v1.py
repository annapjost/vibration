from ij import IJ, ImagePlus, ImageStack
from ij import WindowManager as WM
from ij.gui import Plot as Plot
from ij.gui import PlotWindow as PlotWindow
from ij.io import OpenDialog
from ij.measure import ResultsTable
from fiji.util.gui import GenericDialogPlus
from ij.gui import GenericDialog
from os import path
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
    
#how big is it?  set whether to use slices or frames for looping, because sometimes
# these stacks are frames and sometimes slices.  
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
        
def findApproveMaxima(imp):
    """set appropriate noise tolerance for Find Maxima by trial and error"""
    gd = GenericDialogPlus('noise tolerance')
    gd.addStringField('starting noise tolerance: ', None)
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
     

# define some necessary math functions 

def average(x):
    average = sum(x)*1.0/len(x)
    return average

def stdev(s):
    avg = sum(s)*1.0/len(s)
    variance = map(lambda x: (x-avg)**2, s)
    return math.sqrt(average(variance))
    

#noise = getNoiseTolerance()

imp = IJ.getImage()

scale = getCal(imp)
if scale == False:
    gd = GenericDialogPlus('enter calibration')
    gd.addStringField('pixel size (nm): ', None)
    gd.showDialog()
    scale = gd.getNextString()

noise = findApproveMaxima(imp)
if noise == False:
    IJ.log("User clicked cancel!")
else:
    xtimepoints, ytimepoints, numpoints = findAndFit(noise, scale)
    

    x = []
    y = []

    # plot all points
    for i in xtimepoints:
    	for j in range(numpoints):
    		x.append(i[j])
    
    for k in ytimepoints:
	    for l in range(numpoints):
		    y.append(k[l])

    plot = Plot("summary", "xc", "yc", [], [])
    
    #plot.setColor(Color.BLACK)
    plot.addPoints(x, y, Plot.CIRCLE)
    plot_window = plot.show()
    
    
    #subtract first position, then average each point
     # (this part needs a lot of work!  not ready yet!)
    #xtimepointsnorm = []
    #initialx = xtimepoints[0]
    #norm = []
    
    #for t in range(len(xtimepoints)):
     #   norm = map(lambda a,b: a-b, [xtimepoints[t],xtimepoints[0]])
      #  xtimepointsnorm.append(norm)
    
    
    #xpointavg = []
    #for i in range(len(xtimepoints)):
     #   xpoint = average(xtimepoints[i])
      #  xpointavg.append(xpoint)
        
    #plot = Plot("X positions averaged", "timepoint", "position (nm)", [], [])
    #plot.addPoints(range(len(xpointavg)), xpointavg, Plot.LINE)
    #plot_window = plot.show()

    # reorganize the lists:

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

    plotPoint(allpointsx, "x", 3)
    plotPoint(allpointsy, "y", 3)
    plotPoint(allpointsx, "x", 5)
    plotPoint(allpointsy, "y", 5)
    


#now, allpoints is a list of points.  each entry contains every timepoint for that point.

# do this a sort of crappy way for now - stdev in x and in y separately. 
    xstdevs = []
    ystdevs = [] 

    for point in range(numpoints):
    	std = stdev(allpointsx[point])
    	xstdevs.append(std)

    for point in range(numpoints):
    	std = stdev(allpointsy[point])
    	ystdevs.append(std)


    avgxstdev = average(xstdevs)
    avgystdev = average(ystdevs)
    # the stdevs reported here are an average of all points!
    IJ.log("x standard deviation (avg of beads): " + str(avgxstdev))
    IJ.log("y standard deviation (avg of beads): " + str(avgystdev))
    
    plot = Plot("bead X stdevs", "bead", "stdev (nm)", [], [])
    plot.setLimits(0, numpoints, 0, 50)
    plot.addPoints(range(1,numpoints+1), xstdevs, Plot.CIRCLE)
    plot_window = plot.show()
    
    for point in range(numpoints):
        IJ.log("x standard deviation for bead " + str(point+1) + ": " + str(xstdevs[point]))
        IJ.log("y standard deviation for bead " + str(point+1) + ": " + str(ystdevs[point]))


#trying to make this work to measure distances from the centroid for each point over time...
'''
def distanceFromCentroid(x, y):
    centroid = [average(x), average(y)]
    xy = [ (b,c) for b in x for c in y]
    xdiffs = [ (b**2) for b in x ]
    ydiffs = [ (c**2) for c in y ]
    sums = [ (b**2 + c**2) for b in xdiffs for c in ydiffs ] 
    distances = [ sqrt(d) for d in sums ]
    distance = average(distances)
    return distance
        


averages = []

for point in range(numpoints):
    distances = []
    distance = distanceFromCentroid(allpointsx[point], allpointsy[point])
    distances.append(distance)
    avg = average(distance)
    averages.append(avg)
    
print averages
    
'''
    
    
    