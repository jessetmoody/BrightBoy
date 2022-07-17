# BrightBoy 2020
# Jesse Moody

# Portions of code taken from test_microphone.py in Vosk's Python examples

import sounddevice as sd
import vosk
import sys
import threading
import queue
import re
import time
import os
import platform
try:
    import pantilthat as pth
except:
    import pantilthatEmulator
    pth = pantilthatEmulator.Pantilthat() # instantiate Pantilthat object (class)
killThreads = False

q = queue.Queue()  # stores streaming audio data from sounddevice
wordQueue = queue.Queue() # stores speech to text words from recognizeWords()
endProgram = False # recognizeWords() thread sets to True if model folder doesn't exist

currentLEDcolor = 'off' # store current LED color

# Taken from Vosk test_microphone.py example
def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# Allows spoken command to be translated into servo command
def servoDo(command, modifier=22): # modifier defaults to 22 if none was given, which is about 1/4 of 90  
    # get current angles
    currentPanAngle = pth.get_pan()
    currentTiltAngle = pth.get_tilt()
    
    if command == "center" or command == "Center":
        pth.pan(0)
        pth.tilt(0)
    elif command == "down":
        newAngle = currentTiltAngle + modifier
        if newAngle > 90:
            newAngle = 90 # pth.tilt() constrained to +/-90
        pth.tilt(newAngle)
    elif command == "up":
        newAngle = currentTiltAngle - modifier
        if newAngle < -90:
            newAngle = -90
        pth.tilt(newAngle)
    elif command == "left":
        newAngle = currentPanAngle + modifier
        if newAngle > 90:
            newAngle = 90
        pth.pan(newAngle)
    elif command == "right":
        newAngle = currentPanAngle - modifier
        if newAngle < -90:
            newAngle = -90
        pth.pan(newAngle)
    elif command == "on":
        ledSet('white')
    elif command == "off":
        ledSet('off')
    elif command == "power down":
        if 'raspberrypi' in str(platform.uname()): # check if running on RasPi
            ledSet('off') # turn off LEDs
            os.system("sudo shutdown -h now") # issue shutdown command to system
        else:
            print("Not running on RasPi. Aborting shutdown.") # don't power down if running on Windows (debugging)
    elif command == "restart": # restart the systemctl brightboy.service
        if 'raspberrypi' in str(platform.uname()): # check if running on RasPi
            ledSet('off') # turn off LEDs
            os.system("sudo systemctl restart brightboy.service") # issue command to systemctl to restart service
            print("Issuing sudo systemctl restart brightboy.service")
        else:
            print("Not running on RasPi. Aborting restart.") # don't restart service if running on Windows (debugging)
    elif command == "stop": # stop the systemctl brightboy.service
        ledSet('off') # turn off LEDs
        if 'raspberrypi' in str(platform.uname()): # check if running on RasPi
            print("Stopping brightboy.service")
            os.system("sudo systemctl stop brightboy.service") # issue command to systemctl to stop service
        else:
            print("Not running on RasPi. Executing via sys.exit().") # end Python script on Windows
            os._exit(1) # exit Python program

    # print angles
    print(f'newPanAngle = {pth.get_pan()}')
    print(f'newTiltAngle = {pth.get_tilt()}')

# Convert audio stream from microphone into text
def recognizeWords():
    try:
        if not os.path.exists("model"):
            print ("Please download a model for your language from https://alphacephei.com/vosk/models")
            print ("and unpack as 'model' in the current folder.")
            global endProgram # access global var previously defined
            endProgram = True # signal to main thread to end program
            return
        model = vosk.Model("model")
        myDevice = sd.default.device
        input_device_info = sd.query_devices(None, 'input') # When device arg (1st arg) is None, 
                                                            # dictionary of default input device info is returned
        
        # soundfile expects an int, sounddevice provides a float:
        samplerate = int(input_device_info['default_samplerate'])
            
        dump_fn = None # Normally used for storing rec, but not needed for BB (see test_microphone.py in vosk Python examples)

        # TODO: Pass sd.RawInputStream() the Adafruit Voice Bonnet mic as the device arg
        with sd.RawInputStream(samplerate, blocksize = 8000, device=myDevice, dtype='int16',
                                channels=1, callback=callback):
            rec = vosk.KaldiRecognizer(model, samplerate)
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    # words = re.findall(r'(?<=\"text\" : \")(.+)(?=\")', rec.Result()): # use regex to trim unneeded characters (old method)
                    words = rec.Result() # grab string of recognized text (contains leading and trailing characters)
                    words = words[14:-3] # trim leading and trailing characters from string returned by rec.Result()
                    if words and words != "huh" and words != "what": # if not empty or not any of the words usually heard when it's silent.
                                                                     # Necessary bc otherwise rec.Result() returns empty list every 20s
                                                                     # regardless of whether or not any words were heard.
                        wordQueue.put(words) # put string of heard words into queue as new item
    except Exception as e:
        print(e)

def ledSet(color):
    global currentLEDcolor
    if color != currentLEDcolor: # only proceed if we're changing the color, else do nothing
        if color == 'red':
            pth.set_all(50,0,0,0)
            pth.show()
            currentLEDcolor = color # I don't like how this repeats in this fn, but it's necessary
                                    # in order to use RETURN and skip other IF statements
            return
        if color == 'green':
            pth.set_all(0,50,0,0)
            pth.show()
            currentLEDcolor = color
            return
        if color == 'blue':
            pth.set_all(0,0,50,0)
            pth.show()
            currentLEDcolor = color
            return
        if color == 'yellow':
            pth.set_all(10,40,0,0)
            pth.show()
            currentLEDcolor = color
            return
        if color == 'white':
            pth.set_all(0,0,0,255)
            pth.show()
            currentLEDcolor = color
            return
        if color == 'off':
            pth.set_all(0,0,0,0)
            pth.show()
            currentLEDcolor = color
            return
        print("Error: ledSet invalid color")

def ledBlink(color): # TODO: Change to non-blocking via threading. This is currently slowing everything down!!
    global currentLEDcolor
    if color != currentLEDcolor: # if color is different than current LED color
        origColor = currentLEDcolor # currentLEDcolor is cleared by ledSet, therefore save it here
        ledSet(color) # change color temporarily
        time.sleep(0.1) # wait 200ms
        ledSet(origColor) # change color back to original color
    else: # just blink current color
        ledSet('off') # turn off LEDs
        time.sleep(0.1) # wait 200ms
        ledSet(color) # turn original color back on (color = currentLEDcolor)

if __name__ == "__main__":
    wakeWords = ["bright boy ", "right boy ", "Bright boy ", "Brightboy ", "bribe oy ",
                 "right boy ", "brightpoint", "white boy", "breakpoint", "brake boy"] # wake word and homonyms
    commands = ["center", "Center", "up", "down", "right", "left", "on", "off", "power down", "restart", "stop"]
    modifiers = {"little":11, "bit":11, "tad":5, "smidge":2, "hair":1}

    # Center servos and setup NeoPixel ring
    pth.pan(0)
    pth.tilt(0)
    pth.light_mode(pth.WS2812)
    pth.light_type(pth.GRBW)

    try:
        # Start speech recognition thread to constantly listen for new commands
        listenerThread = threading.Thread(target=recognizeWords)
        listenerThread.daemon = True
        listenerThread.start()

        while endProgram == False: # endProgram var is controlled by recognizeWords() thread
            if currentLEDcolor != 'white':
                ledSet('green') # indicate "listening for words"
            if not wordQueue.empty():
                ledBlink('yellow') # indicate heard words or "words added to queue
                words = wordQueue.get()
                print(f'words from queue={words}')
                if any(x in words for x in wakeWords): # if any wakewords appear in recognized words
                    print("heard wake word")
                    ledBlink('red') # indicate "processing"
                    splitWords = re.split(r'|'.join(wakeWords), words) # split words into list. bar symbol (|) is used to
                                                                       # join words in wakeWords list into a regex "OR" string
                    afterWakeWord = splitWords[1] # save list as new list starting after wake word
                    foundCommands = re.findall(r'|'.join(commands), afterWakeWord) # regex OR pattern example: r'word1|word2|word3'
                    foundModifiers = re.findall(r'|'.join(modifiers), afterWakeWord) # same approach as prev line
                    print(f'foundCommands={foundCommands}')
                    print(f'foundModifiers={foundModifiers}')
                    for idx, c in enumerate(foundCommands): # using "idx, c" to allow for indexing through modifiers as well as commands
                        try:
                            print(f'sending {c} command to servoDo with {foundModifiers[idx]} modifier')
                            servoDo(c, modifiers[foundModifiers[idx]]) # pass command (c) and value from modifiers dictionary using idx
                        except:
                            print(f'sending {c} command to servoDo with no modifier')
                            servoDo(c) # if no modifiers, just send command

    except KeyboardInterrupt:
        ledSet('off') # turn off LEDs
        killThreads = True
        print("Exiting module")
        sys.exit(0)