# Pan-tilt test, Jesse Moody, 11/26/2020

import pantilthat
import time

# Reset to middle position
pantilthat.pan(0)
pantilthat.tilt(0)

while True:
    pantilthat.pan(-45)
    time.sleep(1)
    pantilthat.tilt(0)
    time.sleep(1)
    pantilthat.tilt(45)
    time.sleep(1)
    pantilthat.pan(0)
    time.sleep(1)
    pantilthat.pan(45)
    time.sleep(1)
    pantilthat.tilt(0)
    time.sleep(1)
    pantilthat.tilt(-45)
    time.sleep(1)