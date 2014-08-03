#!/usr/bin/python

import numpy as np
import cv2
import ROOT
import sys
import datetime

numframes = 25
xbins = 64
ybins = 48

for arg in sys.argv:
    if arg.startswith("--numframes="):
        numframes = int(arg.split('=')[1])
    if arg.startswith("--xbins="):
        xbins = int(arg.split('=')[1])
    if arg.startswith("--ybins="):
        ybins = int(arg.split('=')[1])
    if arg.startswith("--help" or "-help" ):
	print("=====  OpenCV beam camera analyzer ======")
	print("")
	print("  Usage:")
	print("")
	print("     frame2hist.py [--frames=< # frames to for fitting center = 25> ")
	print("                    --xbins=<64> ")
	print("                    --ybins=<48> ")
	print("")
	print("  Go to window 'Frame' and hit r for remeasure")
	print("")


cap = cv2.VideoCapture(0)

c = ROOT.TCanvas("profile","Beam Profile")
c.Divide(2,2)
hist = ROOT.TH2D("frame","Beam Profile",xbins,0,640,ybins,0,480)
hist.SetXTitle("x")
hist.SetYTitle("y")
hist.SetZTitle("Intensity [a.u.]")
histx = ROOT.TH1D("framex","framex AA",xbins,0,640)
histy = ROOT.TH1D("framey","framey",ybins,0,480)
f2 = ROOT.TF2("f2","xygaus",0 ,640,0,640);
f1 = ROOT.TF1("f1","gaus",0 ,640);

curframe = 0

def PrintKeys():
        print("=====  OpenCV beam camera analyzer ======")
        print("")
        print("  r: remeasure")
        print("  s: save current picture")
        print("  q: quit")
        print("")


# Grab a grayscale video frame as 64bit floats
def GrabFrame():
    ret = False
	#try to read a new frame
    ret, frame = cap.read()
    # convert to grayscale and floats
    return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(float)



PrintKeys()

while(cap.isOpened()):

    ret, frame = GrabFrame()

    if curframe == 0:
        print("")
        print("Accumulating frames...")
        print("")
        ret, buf=GrabFrame()

    if ret==True:
        if curframe < numframes:
            print(1.0 * curframe/numframes)
            # accumulate frames
            buf+=frame

        # show actual frame, converted to 8bit
        cv2.imshow("BEAMCAMERA -- Hit 'r' for remeasure",frame.astype(np.uint8))
    

        curframe = curframe + 1
    else:
	print("Error reading video.")
        break

    # Keyboad Input
    key = cv2.waitKey(1) & 0xFF;
    if(key == ord('q')):
        print("Bye!")
        break
    elif( key == ord('r')):
        hist.Reset()
        curframe = 0
    elif( key == ord('p')):
        i = datetime.datetime.now()
        filename = i.strftime('Beamspot-%Y-%m-%d-%H:%M:%S.png')
        print "Saving camera picture to ",filename
        cv2.imwrite( filename, frame )
    elif( key == ord('s')):
        i = datetime.datetime.now()
        filename = i.strftime('BeamspotFit-%Y-%m-%d-%H:%M:%S.png')
        print "Saving Histograms to ",filename
        c.SetWindowSize(1200,800)
        c.SaveAs(filename)


    if curframe == numframes:
        date = datetime.datetime.now()
        Title = date.strftime('Beam Profole %Y-%m-%d %H:%M:%S')
        hist.SetTitle(Title)

	print("Filling Histogram...")

        size=buf.shape

        # this is SLOOOOOW
        for x in range(size[1]):
            for y in range(size[0]):
                 hist.Fill(x,y, frame[y][x])

	print("Projecting...")
        histx = hist.ProjectionX()
	histx.SetTitle("X-Projection")
        histy = hist.ProjectionY()
        histy.SetTitle("Y-Projection")
        print("")

        print("Fitting...")
        c.cd(1)
        hist.Draw("colz")
        c.cd(2)
        hist.Fit("f2","Q")
        hist.Draw("")
        c.cd(3)
        histx.Fit("f1","Q")

        histx.Draw("")
        c.cd(4)
        histy.Fit("f1","Q")
        histy.Draw("")
        c.Update()
        print("Done")

        PrintKeys()


# Release everything if job is finished
cap.release()
cv2.destroyAllWindows()
