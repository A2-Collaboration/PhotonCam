#!/bin/bash

. /opt/root/bin/thisroot.sh
. /opt/epics/thisEPICS.sh
export PYEPICS_LIBCA=/opt/epics/base/lib/$EPICS_HOST_ARCH/libca.so

#exec /usr/bin/python /home/a2cb/beamcontrols/PhotonCam/frame2hist.py --numframes=150 --mm2pix=0.13 --pix2bin=10
exec /usr/bin/python /home/a2cb/beamcontrols/PhotonCam/frame2hist.py --numframes=150 --mm2pix=1 --pix2bin=5
