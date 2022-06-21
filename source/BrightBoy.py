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
try:
    import pantilthat
except:
    import pantilthatEmulator
    pantilthat = pantilthatEmulator.Pantilthat() # instantiate Pantilthat object (class)
killThreads = False

q = queue.Queue()  # stores streaming audio data from sounddevice
wordQueue = queue.Queue() # stores speech to text words from recognizeWords()
endProgram = False # recognizeWords() thread sets to True if model folder doesn't exist

# Taken from Vosk test_microphone.py example
def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# Allows spoken command to be translated into servo command
def servoDo(command, modifier=22): # modifier defaults to 22 if none was given, which is about 1/4 of 90  
    # get current angles
    currentPanAngle = pantilthat.get_pan()
    currentTiltAngle = pantilthat.get_tilt()
    
    if command == "center" or command == "Center":
        pantilthat.pan(0)
        pantilthat.tilt(0)
    elif command == "down":
        newAngle = currentTiltAngle + modifier
        if newAngle > 90:
            newAngle = 90 # pantilthat.tilt() constrained to +/-90
        pantilthat.tilt(newAngle)
    elif command == "up":
        newAngle = currentTiltAngle - modifier
        if newAngle < -90:
            newAngle = -90
        pantilthat.tilt(newAngle)
    elif command == "left":
        newAngle = currentPanAngle + modifier
        if newAngle > 90:
            newAngle = 90
        pantilthat.pan(newAngle)
    elif command == "right":
        newAngle = currentPanAngle - modifier
        if newAngle < -90:
            newAngle = -90
        pantilthat.pan(newAngle)
    elif command == "on":
        pantilthat.set_all(0, 0, 0, 255)
        pantilthat.show()
    elif command == "off":
        pantilthat.set_all(0, 0, 0, 0)
        pantilthat.show()
    elif command == "power down":
        if 'pi' in str(os.uname()):
            pantilthat.set_all(0, 0, 0, 0)
            pantilthat.show()
            os.system("sudo shutdown -h now")
        else:
            print("Not running on RasPi. Aborting shutdown.")

    # print angles
    print(f'newPanAngle = {pantilthat.get_pan()}')
    print(f'newTiltAngle = {pantilthat.get_tilt()}')

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
                    wordQueue.put(rec.Result())
    except Exception as e:
        print(e)

if __name__ == "__main__":
    wakeWords = ["bright boy ", "right boy ", "Bright boy ", "Brightboy ", "bribe oy ",
                 "right boy ", "brightpoint", "white boy", "breakpoint", "brake boy"] # wake word and homonyms
    commands = ["center", "Center", "up", "down", "right", "left", "on", "off", "power down"]
    modifiers = {"little":11, "bit":11, "tad":5, "smidge":2, "hair":1}

    # Center servos and setup NeoPixel ring
    pantilthat.pan(0)
    pantilthat.tilt(0)
    pantilthat.light_mode(pantilthat.WS2812)
    pantilthat.light_type(pantilthat.GRBW)

    try:
        # Start speech recognition thread to constantly listen for new commands
        listenerThread = threading.Thread(target=recognizeWords)
        listenerThread.daemon = True
        listenerThread.start()

        while endProgram == False: # endProgram var is controlled by recognizeWords() thread
            if not wordQueue.empty():
                words = wordQueue.get()
                print(f'words from queue={words}')
                if any(x in words for x in wakeWords): # if any wakewords appear in recognized words
                    print("heard wake word")
                    splitWords = re.split(r'|'.join(wakeWords), words)
                    afterWakeWord = splitWords[1]
                    foundCommands = re.findall(r'|'.join(commands), afterWakeWord)
                    foundModifiers = re.findall(r'|'.join(modifiers), afterWakeWord)
                    print(f'foundCommands={foundCommands}')
                    print(f'foundModifiers={foundModifiers}')
                    for idx, c in enumerate(foundCommands):
                        try:
                            print(f'sending {c} command to servoDo with {foundModifiers[idx]} modifier')
                            servoDo(c, modifiers[foundModifiers[idx]]) # TODO add modifier support
                        except:
                            print(f'sending {c} command to servoDo with no modifier')
                            servoDo(c) # TODO add modifier support
                        #TODO add light with on/off commands

    except KeyboardInterrupt:
        killThreads = True
        print("Exiting module")
        sys.exit(0)