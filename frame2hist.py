#!/usr/bin/python

import numpy as np
import cv2
import ROOT
import sys

numframes = 10
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
	print("     frame2hist.py [--frames=< # frames to for fitting center = 10> ")
	print("                    --xbins=<64> ")
	print("                    --ybins=<48> ")
	print("")
	print("  Go to window 'Frame' and hit r for remeasure")
	print("")


cap = cv2.VideoCapture(0)

c = ROOT.TCanvas("profile","Beam Profile")
c.Divide(2,2)
hist = ROOT.TH2D("frame","frame",xbins,0,640,ybins,0,480)
histx = ROOT.TH1D("framex","framex",xbins,0,640)
histy = ROOT.TH1D("framey","framey",ybins,0,480)
f2 = ROOT.TF2("f2","xygaus",0 ,640,0,640);
f1 = ROOT.TF1("f1","gaus",0 ,640);

curframe = 0

print("=====  OpenCV beam camera analyzer ======")
print("")
print("  r for remeasure")
print("")

while(cap.isOpened()):
    ret, frame = cap.read()
    if curframe == 0:
        print("")
        print("Filling histogram.")
        print("")

    if ret==True:
        if curframe < numframes:
            print(1.0 * curframe/numframes)
            for x in range(640): 
                for y in range(480):
                    for color in frame[y][x]:
                        hist.Fill(x,y,color)
        else:
            cv2.imshow("BEAMCAMERA -- Hit 'r' for remeasure",frame)

        if cv2.waitKey(1) & 0xFF == ord('r'):
            curframe = 0
            hist.Reset()

        curframe = curframe + 1
    else:
        break

    if curframe == numframes:
        histx = hist.ProjectionX()
        histy = hist.ProjectionY()
        print("")
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
        print("")
        print("  r for remeasure")
        print("")



# Release everything if job is finished
cap.release()
cv2.destroyAllWindows()
