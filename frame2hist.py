#!/usr/bin/python

import numpy as np
import cv2
import ROOT
from epics import *
import sys
import os
import datetime

###### Default Settings #########
numframes = 25
xbins = 64
ybins = 48
automode = True
epicson = True
windowsize = (1200,800)
average_factor = 0.1

def PrintKeys():
        print("Keys:")
        print("")
        print("  a: Toggle auto mode")
        print("  r: remeasure")
        print("  s: save histograms as png")
        print("  p: save camera picture as png")
        print("  e: generate an entry for Elog")
        print("  q: quit")
        print("")

### Parse Command Line ###
for arg in sys.argv:
    if arg.startswith("--numframes="):
        numframes = int(arg.split('=')[1])
    if arg.startswith("--xbins="):
        xbins = int(arg.split('=')[1])
    if arg.startswith("--ybins="):
        ybins = int(arg.split('=')[1])
    if arg.startswith("--noauto"):
        automode=False
    if arg.startswith("--help" or "-help" ):
	print "=====  OpenCV beam camera analyzer ======"
	print ""
	print "  Usage:"
	print ""
	print "     ",sys.argv[0]," [--numframes=< # frames to for fitting center = 25> "
	print "                    --xbins=<64> "
	print "                    --ybins=<48> "
	print "                    --noauto  turn of auto mode"
	print ""
        PrintKeys()
	print ""


### Init ###

# Init Video Capture
cap = cv2.VideoCapture(0)

# Set up ROOT

# Canvas
c = ROOT.TCanvas("profile","Beam Profile")
c.Divide(2,2)
c.SetWindowSize(windowsize[0], windowsize[1])

# 2D profile histogram
hist = ROOT.TH2D("frame","Beam Profile",xbins,0,640,ybins,0,480)
hist.SetXTitle("x")
hist.SetYTitle("y")
hist.SetZTitle("Intensity [a.u.]")
histx = ROOT.TH1D()
histx.SetTitle("X-Projection")
histy = ROOT.TH1D()
histy.SetTitle("Y-Projection")

# Fit functions
f2 = ROOT.TF2("f2","xygaus",0 ,640,0,640);
f1 = ROOT.TF1("f1","gaus",0 ,640);

curframe = 0
last_p = 0



# Grab a grayscale video frame as 64bit floats
def GrabFrame():
    ret, frame = cap.read()
    # convert to grayscale and floats
    return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(float)


PrintKeys()

def ToEpics():
    caput("BEAM:PhotonCam:CenterX",hist.GetFunction("f2").GetParameter(1))
    caput("BEAM:PhotonCam:CenterY",hist.GetFunction("f2").GetParameter(3))
    caput("BEAM:PhotonCam:WidthX",hist.GetFunction("f2").GetParameter(2))
    caput("BEAM:PhotonCam:WidthY",hist.GetFunction("f2").GetParameter(4))


def GenerateElog():
        filename1 = "BeamspotFit.png"
        filename2 = "Beamspot.png"
	os.system("rm " + filename1 + " " + filename2)
        c.SetWindowSize(windowsize[0], windowsize[1])
        c.SaveAs(filename1)
        cv2.imwrite( filename2, frame )


        date = datetime.datetime.now()
	elog_cmd = "echo 'Beamspot Pictures from " + date.strftime("%Y-%m-%d-%H:%M:%S") + "' | "
        elog_cmd = elog_cmd + "/opt/elog/bin/elog -h elog.office.a2.kph -u a2online a2messung "
        elog_cmd = elog_cmd + "-l 'Main Group Logbook' -a Experiment='2014-07_EPT_Prod' "
        elog_cmd = elog_cmd + "-a Author='PLEASE FILL IN' -a Type=Routine "
        elog_cmd = elog_cmd + "-a Subject='Photon beam profile' "
        elog_cmd = elog_cmd + "-f " + filename1 + " ";
        elog_cmd = elog_cmd + "-f " + filename2 + " ";


        print("Uploading beamspot-images...")
        if os.system(elog_cmd) == 0:
                print("Elog entry generated, please edit and add your name!")
        else:
                print("Error generating Elog entry!")
	
	

def SaveHistograms():
        date = datetime.datetime.now()
        filename = date.strftime('BeamspotFit-%Y-%m-%d-%H:%M:%S.png')
        print "Saving Histograms to ",filename
        c.SetWindowSize(windowsize[0], windowsize[1])
        c.SaveAs(filename)

def SaveCamera():
        date = datetime.datetime.now()
        filename = date.strftime('Beamspot-%Y-%m-%d-%H:%M:%S.png')
        print "Saving Camera Picture to ",filename
        cv2.imwrite( filename, frame )

def StartMeasurement():
    global last_p
    global curframe
    curframe = 0
    last_p = 0

def Analyse():
        hist.Reset()

        date = datetime.datetime.now()
        Title = date.strftime('Beam Profile %Y-%m-%d %H:%M:%S')
        hist.SetTitle(Title)
	#print("Filling Histogram...")

        size=buf.shape

        # this is SLOOOOOW
        for x in range(size[1]):
            for y in range(size[0]):
                 hist.Fill(x,y, frame[y][x])

        histx = hist.ProjectionX()
        histy = hist.ProjectionY()

        #print("Fitting...")
        c.cd(1)
        hist.Fit("f2","Q")
        hist.Draw("colz")
        c.cd(2)
        hist.GetFunction("f2").SetBit(ROOT.TF2.kNotDraw);
        hist.Draw("ARR")
	c.cd(1)
	f2.Draw("same")
	
        c.cd(3)
        histx.Fit("f1","Q")

        histx.Draw("")
        c.cd(4)
        histy.Fit("f1","Q")
        histy.Draw("")
        c.Update()
        #print("Done")

        PrintKeys()

        if(epicson):
            ToEpics()

        if(automode):
            StartMeasurement()


if( cap.isOpened()):
    ret, sumbuf = GrabFrame()

print "Size:", sumbuf.shape

while(cap.isOpened()):

    ret, frame = GrabFrame()

    if curframe == 0:
        #print ""
        #print "Accumulating ",numframes," frames..."
        sys.stdout.write("Accumulating " + str(numframes) + " frames...")
        buf=frame

    if ret==True:
        sumbuf = cv2.addWeighted(sumbuf, 1-average_factor, frame, average_factor, 0)
        
        if curframe < numframes:
            p = round(1.0 * curframe/numframes*10)
            if( p > last_p):
                sys.stdout.write('#')
                sys.stdout.flush()
                last_p = p
            # accumulate frames
            buf+=frame

        # show actual frame, converted to 8bit
        cv2.imshow("BEAMCAMERA", frame.astype(np.uint8))
        cv2.imshow("BEAMCAMERA - Averaged", sumbuf.astype(np.uint8))

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
        StartMeasurement()

    elif( key == ord('p')):
        SaveCamera()

    elif( key == ord('s')):
        SaveHistograms()

    elif( key == ord('e')):
        GenerateElog()

    elif( key == ord('t')):
        epicson ^= True;
        print "Epics on: ", epicson

    elif( key == ord('a')):
        automode ^= True;
        print "Automode: ", automode
        if(automode):
           StartMeasurement()


    if curframe == numframes:
        print ""
        Analyse()


# Release everything if job is finished
cap.release()
cv2.destroyAllWindows()
