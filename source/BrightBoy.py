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
import logging
try:
    import pantilthat as pth
except:
    import pantilthatEmulator
    pth = pantilthatEmulator.Pantilthat() # instantiate Pantilthat object (class)

logging.basicConfig(level=logging.INFO, format='%(message)s') # Setup logging (debugging print statements)
# TODO Fix log messages so they're using message categories correctly
killThreads = False # Used for catching Keyboard Interrupts

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
            logging.info("Not running on RasPi. Aborting shutdown.") # don't power down if running on Windows (debugging)
    elif command == "restart": # restart the systemctl brightboy.service
        if 'raspberrypi' in str(platform.uname()): # check if running on RasPi
            ledSet('off') # turn off LEDs
            os.system("sudo systemctl restart brightboy.service") # issue command to systemctl to restart service
            logging.info("Issuing sudo systemctl restart brightboy.service")
        else:
            logging.info("Not running on RasPi. Aborting restart.") # don't restart service if running on Windows (debugging)
    elif command == "stop": # stop the systemctl brightboy.service
        ledSet('off') # turn off LEDs
        if 'raspberrypi' in str(platform.uname()): # check if running on RasPi
            logging.info("Stopping brightboy.service")
            os.system("sudo systemctl stop brightboy.service") # issue command to systemctl to stop service
        else:
            logging.info("Not running on RasPi. Executing via sys.exit().") # end Python script on Windows
            os._exit(1) # exit Python program

    # print angles
    logging.info(f'newPanAngle = {pth.get_pan()}')
    logging.info(f'newTiltAngle = {pth.get_tilt()}')

# Convert audio stream from microphone into text
def recognizeWords():
    prevWords = [] # list for storing previous partial result 

    try:
        if not os.path.exists("model"):
            logging.info ("Please download a model for your language from https://alphacephei.com/vosk/models")
            logging.info ("and unpack as 'model' in the current folder.")
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
            ledBlink('white') # indicate recognizeWords is ready to go
            while True:
                data = q.get() # get audio data from sound device (via queue)
                if rec.AcceptWaveform(data): # pass audio data to recognizer and check if final result exists
                    rec.Result() # call this merely to clear the partial result and start afresh
                    prevWords = [] # clear out the prevWords whenever silence timeout
                    words = [] # clear out words whenever silence timeout
                else:
                    words = rec.PartialResult() # grab string of recognized text (contains leading and trailing characters)
                    words = words[17:-3] # trim leading and trailing characters from string returned by rec.PartialResult()
                if words and words != "huh" and words != "what": # if not empty and not any of the words usually heard when it's silent.
                                                                    # Necessary bc rec.PartialResult() returns empty string whether or
                                                                    # not any words were heard.
                    words = words.split() # split into list of strings
                    logging.debug(f'rec.PartialResult() = {words}')
                    if len(words) > len(prevWords): # if a new word has been heard. TODO: Check spelling of each, not just length
                        logging.debug(f'PartialResult() > prevWords\nprevWords = {prevWords}')
                        newWords = words[-(len(words)-(len(prevWords))):] # keep only new words. Use negative indexing.
                        logging.debug(f'newWords = {newWords}')
                        for word in newWords: # split in case multiple words were received (this sometimes happens)
                            wordQueue.put(word) # place each word into queue as new individual items
                            logging.debug(f'putting word "{word}" in wordQueue')
                    prevWords = words # replace old sentence with new one
                    logging.debug(f'setting prevWords = {prevWords}]\n\n-----------------------')
    except Exception as e:
        logging.info(e)

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
            pth.set_all(20,40,0,0)
            pth.show()
            currentLEDcolor = color
            return
        if color == 'darkyellow':
            pth.set_all(2,5,0,0)
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
        logging.info("Error: ledSet invalid color")

# Momentarily change color of LED to new color or turn current color on then off
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

# Poll wordQueue and check each new word(s) for wake word(s)
def heardWakeWord():
    if not wordQueue.empty(): # check if wordQueue has any words in it
        word = wordQueue.get()
        logging.info(f'word from queue={word}')
        if word in compoundWakeWords: # if word is any of the possible compound wake words
            logging.info("heard compound wake word")
            return True # return to main as True
        elif word in wakeWords1: # if word is any of the possible 1st wake words
            logging.info(f'heard 1st wake word') 
            startTime = time.perf_counter() # get the current time
            while(time.perf_counter() - startTime < 1.5): # allow for 2nd word to be spoken after 1.5s (wait for it)
                if not wordQueue.empty(): # make sure there's another word available before checking wordQueue
                    word2 = wordQueue.get() # get next word in wordQueue
                    if word2 in wakeWords2: # if word2 is any of the possible 2nd wake words
                        logging.info(f'heard 2nd wake word (therefore full wake word)')
                        return True # a full wake word was heard, return to main as True
                    else:
                        break # word2 was not a valid 2nd wake word
    return False # will only reach here if wordQueue was empty or no wake words were found


if __name__ == "__main__":
    compoundWakeWords = ["brightboy", "brightpoint", "breakpoint", "breitbart"] # compound wake words (+homonyms)
    wakeWords1 = ["bright", "right", "bribe", "white", "brake", "why"] # first part of two word wake words (+homonyms)
    wakeWords2 = ["boy", "oy"] # second part of two part wake words
    commands = ["center", "Center", "up", "down", "right", "left", "on", "off", "power down", "restart", "stop"]
    modifiers = {"little":11, "bit":11, "tad":5, "smidge":2, "hair":1}

    modifierToApply = '' # used to store command modifier applied to subsequent commands

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
                ledSet('darkyellow') # indicate "listening for words"
            if heardWakeWord():
                startTime = time.perf_counter() # get the current time
                while(time.perf_counter() - startTime < 3.5): # while 3.5s hasn't elapsed (after last command)
                    if currentLEDcolor != 'white': # don't turn off the flashlight if it's on
                        ledSet('green') # indicate "heard wake word, listening for commands"
                    if not wordQueue.empty():
                        word = wordQueue.get()
                        logging.info(f'got word from wordQueue = {word}')
                        if word in commands:
                            logging.info(f'foundCommand={word}')
                            if modifierToApply: # if a modifier to apply exists (previously heard)
                                logging.info(f'sending {word} command to servoDo with {modifierToApply} modifier')
                                servoDo(word, modifierToApply) # send command with modifier
                            else:
                                servoDo(word) # send command with no modifier
                            startTime = time.perf_counter() # reset the 3.5s timer after each command/modifier
                        elif word in modifiers:
                            logging.info(f'foundModifier={word}')
                            modifierToApply = word # save modifier for applying to next command
                            startTime = time.perf_counter() # reset the 3.5s timer after each command/modifier
                        
    except KeyboardInterrupt:
        ledSet('off') # turn off LEDs
        killThreads = True
        logging.info("Exiting module")
        sys.exit(0)