#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, urllib2
from urllib2 import urlopen, Request
import logging
import json
import time
import os
from subprocess import call

logPath = "/home/pi/assistant"
fileName = "logfile"

#logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
#logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)

#fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
#fileHandler.setFormatter(logFormatter)
#logger.addHandler(fileHandler)

#consoleHandler = logging.StreamHandler()
#consoleHandler.setFormatter(logFormatter)
#logger.addHandler(consoleHandler)


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
                #TODO, remove crontab and turn on with ssh > heater.json
                text = "ahora enciendo la caldera"
                play(text)
                status = True
        elif words[0] in ["apaga","apagar"]:
            if words[1] in ["caldera","calefacci\\303\\263n"]:
                #TODO, remove crontab and turn on with ssh > heater.json
                text = "ahora apago la caldera"
                play(text)
                status = True
        elif words[0] in ["temperatura"]:
            if words[1] in ["casa","sal\\303\\263n"]:
                #TODO curl to 192.168.1.20 with termometer
                text = "pues unos 23.50 grados"
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
    call(["mpg123", fileName])
    os.remove(fileName)

