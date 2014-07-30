import numpy as np
import cv2
from matplotlib import pyplot as plt

average_factor = 0.01

# Grab a video frame
def GrabFrame():
    ret = False
	#try to read a new frame
    while(ret != True):
        ret, frame = cap.read()
    # convert to grayscale and floats
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(float)


# open a video from file
cap = cv2.VideoCapture('output.avi')

# open the webcam
#cap = cv2.VideoCapture('output.avi')

# grab the first frame
buf2 = GrabFrame()

# Print some stats
print(buf2.shape)
print(buf2.dtype)

while(True):
    # Our operations on the frame come here
    gray = GrabFrame()

    # Display the resulting frame
    buf2 = cv2.addWeighted(buf2,1-average_factor,gray,average_factor,0)
    #buf2 += gray
    
	show = gray

    cv2.imshow('Live',gray.astype(np.uint8))
    cv2.imshow('Sum',cv2.convertScaleAbs(buf2))
    key = cv2.waitKey(1) & 0xFF;
    if(key == ord('q')):
        break
    elif( key == ord('r')):
        buf2 = gray

# close video input
cap.release()
cv2.destroyAllWindows()

# show the last accumulated picture in a plot window
plt.imshow(buf2,'gray'),plt.title('ORIGINAL')
plt.show()


