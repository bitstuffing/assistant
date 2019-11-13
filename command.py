#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, urllib2
from urllib2 import urlopen, Request
import logging
import json
import time
import os
import subprocess


def execute(jsonCommand):
    status = False

    request = jsonCommand["request"]
    response = jsonCommand["response"]

    if len(request)>0 and " " in request:
        words = getWords(request)
        #TODO remove the word please
        logging.debug("verb is %s"%words[0])
        if words[0] in ["enciende","encender","pon","activa","activar"]:
            logging.debug("'turn on' detected, activating second word")
            if words[1] in ["caldera","calefacci\\303\\263n"]:
                text = "caldera encendida"
                turnOnHeater()
                play(text)
                status = True
            if words[1] in ["termostato","termo"]:
                text = "termostato encendido"
                turnOnTermo()
                play(text)
                status = True
        elif words[0] in ["apaga","apagar"]:
            if words[1] in ["caldera","calefacci\\303\\263n"]:
                text = "caldera apagada"
                turnOffHeater()
                play(text)
                status = True
            if words[1] in ["termostato","termo"]:
                text = "termostato apagado"
                turnOffTermo()
                play(text)
                status = True
        elif words[0] in ["temperatura"]:
            if words[1] in ["casa","sal\\303\\263n"]:
                getCurrentTemperature()
                play(text)
                status = True

    return status

def getWords(request):
    words = request.split(" ")
    i=0
    for word in words[:]:
        words[i] = word.lower()
        if word in ['el','la','los','las','por','favor','qu\\303\\251','hace','en','hay','puedes']:
            words.pop(i)
            i-=1 #continue
        i+=1
    return words

def play(text):
    lang = 'es'
    urlText = urllib.quote_plus(text)
    url = 'https://translate.google.com/translate_tts?client=tw-ob&ie=UTF-8&idx=0&total=1&textlen=%s&tl=%s&q=%s'%(len(text),lang,urlText)
    logging.debug(url)
    pwd = os.getcwd()+"/"
    fileName = pwd+"audio%s.mp3"%str(time.time()).replace(".","")
    req = Request(url)
    req.add_header('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5')
    f = urlopen(req)
    with open(os.path.basename(fileName), "wb") as local_file:
        local_file.write(f.read())
    logging.debug("done, play audio time")
    subprocess.call(["mpg123", fileName])
    os.remove(fileName)

def getCurrentTemperature():
    command = "curl -s http://192.168.1.20 | grep -i \"Temperature = \" |  cut -d '=' -f 5"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
    exit = process.communicate()
    logging.debug("returned: '%s'"%exit[0])
    text = "pues unos%s grados"%exit[0]

def turnOnHeater():
    command = "ssh pi@192.168.1.11 crontab -l"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
    exit, err = process.communicate()
    logging.debug("current crontab is: %s"%exit)
    if '#* * * * * python2 /opt/scripts/thermostat.py' in exit:
        exit = exit.replace('#* * * * * python2 /opt/scripts/thermostat.py','* * * * * python2 /opt/scripts/thermostat.py')
        command = "echo \"%s\" | ssh pi@192.168.1.11 crontab "%exit
        logging.debug("command is: %s"%command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
        exit, err = process.communicate()
        logging.debug("turned on")

def turnOffHeater():
    command = "ssh pi@192.168.1.11 crontab -l"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
    exit, err = process.communicate()
    logging.debug("current crontab is: %s"%exit)
    if '#* * * * * python2 /opt/scripts/thermostat.py' not in exit and '* * * * * python2 /opt/scripts/thermostat.py' in exit:
        exit = exit.replace('* * * * * python2 /opt/scripts/thermostat.py','#* * * * * python2 /opt/scripts/thermostat.py')
        command = "echo \"%s\" | ssh pi@192.168.1.11 crontab "%exit
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
        exit, err = process.communicate()
        logging.debug("turned off")

def turnOnTermo():
    command = "echo \"{\\\"heater\\\":\\\"on\\\"}\" | ssh pi@192.168.1.11 -T \"cat > /var/www/html/arduino/heater.json\""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
    exit, err = process.communicate()
    logging.debug("current crontab is: %s"%exit)

def turnOffTermo():
    command = "echo \"{\\\"heater\\\":\\\"off\\\"}\" | ssh pi@192.168.1.11 -T \"cat > /var/www/html/arduino/heater.json\""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
    exit, err = process.communicate()
    logging.debug("current crontab is: %s"%exit)
