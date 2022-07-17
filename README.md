# BrightBoy
 The Auto-Tracking Smart Flashlight

# Summary
BrightBoy is a flashlight that points wherever you tell him to. He's the next best thing to having someone standing next to you holding a flashlight. You simply boot him up, then tell him what to do using voice commands. Later versions will support active IR or computer vision tracking so he can autonomously and intelligently point the flashlight.
## Software
A Python script handles audio processing, offline speech recognition via Vosk, controlling the pan-tilt servos, and turning the flashlight LEDs on/off. Includes emulator for testing without actual hardware and simple pantilt HAT test script.

## Hardware 
V1 is built using a Raspberry Pi B+, the Adafruit Voice Bonnet, an Adafruit WS2812 RGBW LED ring, and the Pimoroni Pan-Tilt HAT.
## Desired Features for V1:
- Control with voice
	- On/off
	- Up/down
	- Left/right
	- Amount of movement adjustable via modifier words
		- "Move left 3 degrees"
		- "Move just a smidge to the right"
- All in one package
- Bright [how bright?]
- Battery-powered for 3 hrs
- No internet connection needed
- Quick startup (<=5 seconds) http://himeshp.blogspot.com/2018/08/fast-boot-with-raspberry-pi.html
- Can stand on its own base
- Magnetically attach to metal surfaces
