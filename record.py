import numpy as np
import cv2
import ROOT

cap = cv2.VideoCapture(0)
#cap.set(cv2.CV_CAP_PROP_FPS,29.97)

# Define the codec and create VideoWriter object
fourcc = cv2.cv.CV_FOURCC('X', 'V', 'I', 'D')
out = cv2.VideoWriter('output.avi',fourcc, 20.0, (640,480))

while(cap.isOpened()):
    ret, frame = cap.read()
    if ret==True:
        frame = cv2.flip(frame,0)

        # write the flipped frame
        out.write(frame)

        cv2.imshow('frame',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

# Release everything if job is finished
cap.release()
out.release()
cv2.destroyAllWindows()
