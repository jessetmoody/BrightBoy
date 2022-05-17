# BrightBoy 2020
# Jesse Moody

import speech_recognition as sr
import sys
import threading
import queue
import re
import time
try:
    import pantilthat
except:
    import pantilthatEmulator
    pantilthat = pantilthatEmulator.Pantilthat() # instantiate Pantilthat object (class)
killThreads = False

def recognizeWords(r, mic, wordQueue):
    global killThreads
    with mic as source:
        r.adjust_for_ambient_noise(source)
    while killThreads == False: # keeps thread alive
        with mic as source:
            print("Listening for command")
            audio = r.listen(source)
        try:
            words = r.recognize_google(audio)
            print(words)
            wordQueue.put(words)
        except:
            print("Say what? (Couldn't recognize speech)")

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

    # print angles
    print(f'newPanAngle = {pantilthat.get_pan()}')
    print(f'newTiltAngle = {pantilthat.get_tilt()}')

if __name__ == "__main__":
    wordQueue = queue.Queue()
    wakeWords = ["bright boy ", "right boy ", "Bright boy ", "Brightboy ", "bribe oy ",
                 "right boy ", "brightpoint", "white boy", "breakpoint", "brake boy"] # wake word and homonyms
    commands = ["center", "Center", "up", "down", "right", "left", "on", "off"]
    modifiers = {"little":11, "bit":11, "smidge":5, "tad":2, "hair":1}

    # center servos and setup NeoPixel ring
    pantilthat.pan(0)
    pantilthat.tilt(0)
    pantilthat.light_mode(pantilthat.WS2812)
    pantilthat.light_type(pantilthat.GRBW)

    try:
        r = sr.Recognizer()
        mic = sr.Microphone(device_index=0) # adafruit voice bonnet device index = 0

        listenerThread = threading.Thread(target=recognizeWords, args=(r, mic, wordQueue)) # constantly listen for new commands
        listenerThread.daemon = True
        listenerThread.start()

        lastTime = 0
        while True:
            #timeInt = int(time.time())
            #if timeInt % 2 == 0 and timeInt != lastTime:
            #    print("wordQueue is empty")
            #    lastTime = timeInt
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