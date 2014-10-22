#!/usr/bin/python

import numpy as np
import cv2
import ROOT
from epics import caput, caget
import sys
import os
import datetime
#import thread

###### Default Settings #########
numframes = 25
xbins = 64
ybins = 48
automode = True
epicson = True
windowsize = (1200,800)
average_factor = 0.01
dumpdata = False
fits=True
videostandard = "0x00000400"
v4l2settings = os.environ['HOME'] + "/.v4l2-default-optimized"
if not os.path.isfile(v4l2settings):
    print("Optimized v4l2-configuration doesn't exist yet!!")
    print("    1.) Optimize using v4l2ucp.")
    print("    2.) Store:         v4l2ctrl -s " + v4l2settings)

def PrintKeys():
        print("======= Beam Camera =====================")
        print("")
        print("Keys (in camera windows):")
        print("")
        print("  Options:")
        print("    a: toggle auto mode      < " + str(automode) + " >")
        print("    e: toggle EPICS logging  < " + str(epicson)  + " >")
        print("    f: toggle fitting        < " + str(fits)     + " >")
        print("  Actions:")
        print("    r: remeasure")
        print("    s: save histograms as png")
        print("    p: save camera picture as png")
        print("    l: generate an entry for Elog")
        print("    q: quit")
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
    if arg.startswith("--v4l2-settings="):
        v4l2settings = arg.split('=')[1];
        if not os.path.isfile(v4l2settings):
            print(" Error loading v4l2-config-file: " + v4l2settings + " doesn't exist!")
            sys.exit(128)
    if arg.startswith("--dump-data"):
        dumpdata = True;
            
    if arg.startswith("--help" or "-help" ):
	print "=====  OpenCV beam camera analyzer ======"
	print ""
	print "  Usage:"
	print ""
	print "     ",sys.argv[0]," [--numframes=< # frames to for fitting center = 25> "
	print "                    --xbins=<64> "
	print "                    --ybins=<48> "
	print "                    --noauto  turn of auto mode"
	print "                    --v4l2-settings=<user-settings-file>"
	print ""
        PrintKeys()
	print ""


### Init ###

# Init v4l2-driver:

os.system("v4l2-ctl --set-standard=" + videostandard)

if os.system("v4l2ctrl -l " + v4l2settings):
    print("Error loading v4l2-config-file!")

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

if dumpdata:
    datafile = open("beam.dat","w")


# Grab a grayscale video frame as 64bit floats
def GrabFrame():
    ret, frame = cap.read()
    # convert to grayscale and floats
    return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(float)


def Clear():
    sys.stderr.write("\x1b[2J\x1b[H")

def CheckBeam():
    #listhistx = [ histx.GetBinContent(i+1) for i in range(histx.GetNbinsX()) ]
    hsum = hist.GetSum()
    hasbeam = caget("BEAM:IonChamber") > 500
    return hasbeam, hsum

def ToEpics():
    beam, hsum = CheckBeam()
    if beam:
        caput("BEAM:PhotonCam:CenterX.A",hist.GetFunction("f2").GetParameter(1))
        caput("BEAM:PhotonCam:CenterY.A",hist.GetFunction("f2").GetParameter(3))
        caput("BEAM:PhotonCam:WidthX.A",hist.GetFunction("f2").GetParameter(2))
        caput("BEAM:PhotonCam:WidthY.A",hist.GetFunction("f2").GetParameter(4))
        caput("BEAM:PhotonCam:Sum.A",hsum)
    else:
        caput("BEAM:PhotonCam:CenterX.A",float('nan'))
        caput("BEAM:PhotonCam:CenterY.A",float('nan'))
        caput("BEAM:PhotonCam:WidthX.A",float('nan'))
        caput("BEAM:PhotonCam:WidthY.A",float('nan'))
        caput("BEAM:PhotonCam:Sum.A",hsum)
        

def GenerateElog():
        filename1 = SaveHistograms()
        filename2 = SaveCamera()

        date = datetime.datetime.now()
        elog_cmd = "echo 'Beamspot Pictures from " + date.strftime("%Y-%m-%d-%H:%M:%S") + "\\n\\n"
        elog_cmd = elog_cmd + "Center is at:  x = " + str(caget("BEAM:PhotonCam:CenterX")) + " , "
        elog_cmd = elog_cmd + "               y = " + str(caget("BEAM:PhotonCam:CenterY")) + "\\n"
        elog_cmd = elog_cmd + "Ratio: Ladder/p2 = " + str(caget("TAGG:EPT:LadderP2Ratio")) + "' | "
        elog_cmd = elog_cmd + "/opt/elog/bin/elog -h elog.office.a2.kph -u a2online a2messung "
        elog_cmd = elog_cmd + "-l 'Main Group Logbook' -a Experiment='2014-10_EPT_Prod' "
        elog_cmd = elog_cmd + "-a Author='PLEASE FILL IN' -a Type=Routine "
        elog_cmd = elog_cmd + "-a Subject='Photon beam profile' "
        elog_cmd = elog_cmd + "-f " + filename1 + " ";
        elog_cmd = elog_cmd + "-f " + filename2;


        print("Uploading beamspot-images...")
        if os.system(elog_cmd) == 0:
                print("Elog entry generated, please edit and add your name!")
        else:
                print("Error generating Elog entry!")

        os.remove(filename1)
        os.remove(filename2)
	

def SaveHistograms():
        date = datetime.datetime.now()
        filename = date.strftime('BeamspotFit-%Y-%m-%d_%H-%M-%S.png')
        print "Saving Histograms to ",filename
        c.SetWindowSize(windowsize[0], windowsize[1])
        c.Update()
        c.SaveAs(filename)
        return filename

def SaveCamera():
        date = datetime.datetime.now()
        filename = date.strftime('Beamspot-%Y-%m-%d_%H-%M-%S.png')
        print "Saving Camera Picture to ",filename
        cv2.imwrite( filename, sumbuf )
        return filename

def StartMeasurement():
    global last_p
    global curframe
    curframe = 0
    last_p = 0

def Analyse():
        global buf
        hist.Reset()

        date = datetime.datetime.now()
        Title = date.strftime('Beam Profile %Y-%m-%d %H:%M:%S')
        hist.SetTitle(Title)
	#print("Filling Histogram...")
        buf /= numframes
        size=buf.shape

        # this is SLOOOOOW
        for x in range(size[1]):
            for y in range(size[0]):
                 hist.Fill(x,y, buf[size[0] - y - 1][x])

        histx = hist.ProjectionX()
        histy = hist.ProjectionY()

        #print("Fitting...")
        c.cd(1)
        if fits:
            hist.Fit("f2","Q")
        if dumpdata:
            datafile.write(str(f2.GetChisquare()) + "    " )
        hist.Draw("ARR")
        c.cd(2)
        if fits:
            hist.GetFunction("f2").SetBit(ROOT.TF2.kNotDraw);
        hist.Draw("cont")
	c.cd(1)
        if fits:
            f2.Draw("same")
	
        c.cd(3)
        if fits:
            histx.Fit("f1","Q")
        if dumpdata:
            datafile.write(str(f1.GetChisquare()) + "    " )

        histx.Draw("")
        c.cd(4)
        if fits:
            histy.Fit("f1","Q")
        if dumpdata:
            datafile.write(str(f1.GetChisquare()) + "    ")
            datafile.write(str(f2.GetParameter(1)) + "    " + str(f2.GetParameter(3)) + "    ")
            datafile.write(str(caget("TAGG:EPT:LadderP2Ratio")))
            datafile.write("\n" )
        histy.Draw("")
        c.Update()
        #print("Done")

        #PrintKeys()

        if(epicson):
            ToEpics()

        if(automode):
            StartMeasurement()


if( cap.isOpened()):
    ret, sumbuf = GrabFrame()
    buf = sumbuf

print "Size:", sumbuf.shape

while(cap.isOpened()):

    ret, frame = GrabFrame()

    if curframe == 0:
        Clear()
        PrintKeys()
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

    elif( key == ord('l')):
        GenerateElog()

    elif( key == ord('e')):
        epicson ^= True;
        print "Epics on: ", epicson

    elif( key == ord('a')):
        automode ^= True;
        print "Automode: ", automode
        if(automode):
           StartMeasurement()
    elif( key == ord('f')):
	fits ^= True;
        print "Fits: ", fits


    if (curframe == numframes):
        Analyse()


# Release everything if job is finished
cap.release()
cv2.destroyAllWindows()
if dumpdata:
    datafile.close()
