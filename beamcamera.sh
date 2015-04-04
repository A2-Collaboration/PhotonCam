#!/bin/bash

. /opt/root/bin/thisroot.sh
. /opt/epics/thisEPICS.sh
export PYEPICS_LIBCA=/opt/epics/base/lib/$EPICS_HOST_ARCH/libca.so

exec /usr/bin/python /home/a2cb/beamcontrols/PhotonCam/frame2hist.py --numframes=75

