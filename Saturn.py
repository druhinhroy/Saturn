from tkinter import *
import time
from threading import *
import datetime
import wikipedia
import webbrowser
import os
import subprocess
from subprocess import call
import json
import requests
import IP2Location
import geocoder
import geopy
from geopy.geocoders import Nominatim
import csv
from pyowm import OWM
import random
import threading
import pyttsx3
import urllib.request
import re
from gtts import gTTS
import playsound
from sys import platform
import wave
import pyaudio
import sys
import argparse
import os
import queue
import sounddevice as sd
import vosk
import sys
from tkinter import ttk

def wake():
    q = queue.Queue()

    def int_or_str(text):
        try:
            return int(text)
        except ValueError:
            return text

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-l', '--list-devices', action='store_true',
        help= 'show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser])
    parser.add_argument(
        '-f', '--filename', type=str, metavar='FILENAME',
        help='audio file to store recording to')
    parser.add_argument(
        '-m', '--model', type=str, metavar='MODEL_PATH',
        help='Path to the model')
    parser.add_argument(
        '-d', '--device', type=int_or_str,
        help='input device (numeric ID or substring)')
    parser.add_argument(
        '-r', '--samplerate', type=int, help='sampling rate')
    args = parser.parse_args(remaining)

    try:
        if args.model is None:
            args.model = "model"

        if args.samplerate is None:
            device_info = sd.query_devices(args.device, 'input')
            args.samplerate = int(device_info['default_samplerate'])

        model = vosk.Model(args.model)

        if args.filename:
            dump_fn = open(args.filename, "wb")
        else:
            dump_fn = None

        with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device, dtype='int16',
                                channels=1, callback=callback):
                print('#' * 80)
                print('Press Ctrl+C to stop the recording')
                print('#' * 80)

                rec = vosk.KaldiRecognizer(model, args.samplerate)
                while True:
                    data = q.get()
                    if rec.AcceptWaveform(data):
                        text = getCleanResult(rec.Result())
                        print(text)
                        if "saturn" in text:
                            while True:
                                newData = q.get()
                                if rec.AcceptWaveform(newData):
                                    newText = getCleanResult(rec.Result())
                                    print(newText)
                                    checkValidAndRunCommand(newText)
                                    break
                                else:
                                    pass

                                if dump_fn is not None:
                                    dump_fn.write(newData)
                    else:
                        pass

    except KeyboardInterrupt:
        print('\nDone')
        parser.exit(0)
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))


def getCleanResult(string):
    string = string[13:]
    string = (string.split('"'))[1].split('"')[0]
    return string

def checkValidAndRunCommand(string):
    if "weather" in string:
        weather()
    elif "temperature" in string:
        weather()
    elif "time" in string:
        checkTime()
    elif "news" in string:
        news()
    elif "search" in string:
        search(string)
    elif "play" in string:
        youtube(string)
    elif "what is" in string:
        search(string)
    elif "who" in string:
        search(string)

    wake()

def speak(string):
    tts = gTTS(string, lang="en", tld = "com")
    audioFile = "voice.mp3"
    tts.save(audioFile)
    playsound.playsound(audioFile)

def weather():
    time.sleep(3)

    coords = geocoder.ip('me')
    coordinates = coords.latlng

    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(str(coordinates[0]) + "," + str(coordinates[1]))
    address = location.raw['address']
    city = address.get('city', '')
    country = address.get('country', '')

    dic = {}
    with open("wikipedia-iso-country-codes.csv") as f:
        file= csv.DictReader(f, delimiter=',')
        for line in file:
            dic[line['English short name lower case']] = line['Alpha-2 code']

    tempLocation = str(city + "," + dic[country])

    owm = OWM("badf1283550290ee7df242fc027dc795")
    weatherMGR = owm.weather_manager()
    observation = weatherMGR.weather_at_place(tempLocation)
    w = observation.weather
    temp = w.temperature('fahrenheit')

    speak("It is currently " + str(round(temp["temp"])) + " degrees and it feels like " + str(round(temp["feels_like"])) + " degrees, with a high of " + str(round(temp["temp_max"])) + " and a low of " + str(round(temp["temp_min"])) + " degrees")

def checkTime():
    time.sleep(3)

    now = datetime.datetime.now()
    preHour = int(now.strftime("%H"))
    preMin = now.strftime("%M")

    if preHour > 12:
        hour = str(preHour - 12)
    else:
        hour = str(preHour)

    if preHour >= 12:
        AMOrPM = "P M"
    else:
        AMOrPM = "A M"

    if preMin == "00":
        min = ""
    elif "0" in preMin:
        oList = list(preMin)

        if "0" == oList[0]:
            min = "O " + str(oList[1])
        else:
            min = str(preMin)
    else:
        min = str(preMin)

    if min == "":
        speak("The time is " + hour + " o'clock " + AMOrPM)
    else:
        speak("The time is " + hour + " " + min + AMOrPM)

def jokes():
    time.sleep(3)
    preSplit = random.choice(allJokes)
    split = preSplit.split(" | ")

    partOne = split[0]
    partTwo = split[1]

    speak(partOne)
    time.sleep(1)
    speak(partTwo)

def search(statement):
    statement = statement.replace("what is ", "")
    statement = statement.replace("who is ", "")
    statement = statement.replace("search ", "")
    url = "https://www.google.com/search?q={}".format(statement)
    webbrowser.open_new_tab(url)

def youtube(statement):
    statement = statement.replace("play ", "")
    statement = statement.replace(" ", "+")
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + statement)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    webbrowser.open('https://www.youtube.com/watch?v=' + video_ids[0])

def threading():
    t1 = Thread(target = wake)
    t1.daemon = True
    t1.start()
    awaken.configure(text = "I'm listening!", state = DISABLED)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

root = Tk()
root.title("Saturn")
root.geometry("400x150")
root.resizable(False, False)

title = Label(root, text = "Saturn", font = ("Helvectica", 24, "bold"))
title.pack(pady = (15, 0))

greeting = Label(root, text = "Hello, I am Saturn, your personal voice assistant.")
greeting.pack(pady = 5)

awaken = Button(root, text = "Awaken Me!", command = threading)
awaken.pack(pady = 5)

root.mainloop()
