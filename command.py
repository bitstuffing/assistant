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

    numbers = ["una","dos","tres","cuatro","cinco","seis","siete","ocho","nueve","diez"]

    request = jsonCommand["request"]
    response = jsonCommand["response"]

    if len(request)>0 and " " in request:
        words = getWords(request)
        #TODO remove the word please
        logging.debug("verb is %s"%words[0])
        if words[0] in ["enciende","encender","pon","poner","activa","activar","reanudar","reanuda","pausar","pausa"]:
            logging.debug("'turn on' detected, activating second word")
            if words[1] in ["caldera","calefacci\\303\\263n"]:
                text = "Caldera encendida"
                turnOnHeater()
                play(text)
                status = True
            elif words[1] in ["termostato","termo"]:
                text = "Termostato encendido"
                turnOnTermo()
                play(text)
                status = True
            elif words[1] in ["kodi","peli","serie"]:
                kodiPauseResume()
                play("pausa kodi")
                status = True
        elif words[0] in ["apaga","apagar","para","parar","quita","quitar"]:
            if words[1] in ["caldera","calefacci\\303\\263n"]:
                text = "Caldera apagada"
                turnOffHeater()
                play(text)
                status = True
            elif words[1] in ["termostato","termo"]:
                text = "Termostato apagado"
                turnOffTermo()
                play(text)
                status = True
            elif words[1] in ["kodi","peli","serie"]:
                kodiStop()
                status = True
        elif words[0] in ["temperatura"]:
            if words[1] in ["casa","sal\\303\\263n"]:
                temperature = getCurrentTemperature()
                text = "Unos%s grados"%temperature
                play(text)
                status = True
        elif words[0] in ["sube","subir","arriba"]:
            if words[1] in ["kodi"]:
                kodiSendUp()
                status = True
            elif (words[1] in numbers or words[1].isdigit()) and len(words)>2 and words[2] in ["veces"]:
                #now get index and launch command many times in a loop
                times = 0
                if words[1].isdigit():
                    times = int(words[1])
                else:
                    times = numbers.index(words[1])+1
                for i in range(0,times):
                    if words[3] in ["kodi"]:
                        kodiSendUp()
                        status = True
        elif words[0] in ["baja","bajar","abajo"]:
            if words[1] in ["kodi"]:
                kodiSendDown()
                status = True
            elif (words[1] in numbers or words[1].isdigit()) and len(words)>3 and words[2] in ["veces"]:
                #now get index and launch command many times in a loop
                times = 0
                if words[1].isdigit():
                    times = int(words[1])
                else:
                    times = numbers.index(words[1])+1
                for i in range(0,times):
                    if words[3] in ["kodi"]:
                        kodiSendDown()
                        status = True
        elif words[0] in ["entra","entrar","enter"]:
            if words[1] in ["kodi"]:
                kodiSendEnter()
                status = True
        elif words[0] in ["atr\\303\\241s","retroceder","back"]:
            if words[1] in ["kodi"]:
                kodiSendBack()
                status = True
        elif words[0] in ["izquierda"]:
            if words[1] in ["kodi"]:
                kodiSendLeft()
                status = True
        elif words[0] in ["derecha"]:
            if words[1] in ["kodi"]:
                kodiSendRight()
                status = True
        elif words[0] in ["casa"]:
            if words[1] in ["kodi"]:
                kodiSendHome()
                status = True
        elif words[0] in ["env\\303\\255a","enviar","escribe","escribir"]:
            size = len(words)
            if words[size-1] in ["kodi"]:
                text = ''
                i=0
                for word in words:
                    logging.debug("word %s, text %s"%(word,text))
                    if i != 0 and i!=len(words)-1:
                        text += word
                        if i != size-2:
                            text += " "
                    i+=1
                logging.debug("text is %s"%(text))
                kodiSendMessage(title='buscar',message=text)
                kodiSendText(text)
                status = True
        elif words[0] in ["mutea","mute","silenciar","silencia","silencio","desmutea","voz"]:
            if words[1] in ["kodi"]:
                kodiMuteUnmute()
                status = True

    return status

def getWords(request):
    words = request.split(" ")
    i=0
    for word in words[:]:
        words[i] = word.lower()
        if word in ['el','la','los','las','por','favor','qu\\303\\251','hace','en','hay','puedes','a','ante','cabe','con','contra','de','desde','entre','a','hacia','sin','son','sobre','tras','vuelve']: #'para'
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
    return exit[0]

def turnOnTermo():
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

def turnOffTermo():
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

def turnOnHeater():
    command = "echo \"{\\\"heater\\\":\\\"on\\\"}\" | ssh pi@192.168.1.11 -T \"cat > /var/www/html/arduino/heater.json\""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
    exit, err = process.communicate()
    logging.debug("current crontab is: %s"%exit)

def turnOffHeater():
    command = "echo \"{\\\"heater\\\":\\\"off\\\"}\" | ssh pi@192.168.1.11 -T \"cat > /var/www/html/arduino/heater.json\""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
    exit, err = process.communicate()
    logging.debug("current crontab is: %s"%exit)

def kodiPauseResume():
    command = '{"jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1}'
    playerJSON = sendCmdToKodi(command,text=True)
    logging.debug(playerJSON)
    playerId = json.loads(playerJSON)["result"][0]["playerid"]
    logging.debug(playerId)
    command = '{"jsonrpc": "2.0", "method": "Player.PlayPause", "params": { "playerid": %s }, "id": 1}'%str(playerId)
    logging.debug(command)
    sendCmdToKodi(command,text=True)

def kodiStop():
    command = '{"jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1}'
    playerJSON = sendCmdToKodi(command,text=True)
    logging.debug(playerJSON)
    playerId = json.loads(playerJSON)["result"][0]["playerid"]
    command = '{"jsonrpc": "2.0", "method": "Player.Stop", "params": { "playerid": %s }, "id": 1}'%str(playerId)
    logging.debug(command)
    sendCmdToKodi(command,text=True)

def kodiSendText(text):
    command = '{"jsonrpc":"2.0","method":"Input.SendText","params":{"text":"%s","done":false},"id":0}'%text
    logging.debug(command)
    sendCmdToKodi(command,text=True)
    kodiSendEnter()

def kodiSendUp():
    command = '{"jsonrpc":"2.0","method":"Input.Up","id":0}' 
    sendCmdToKodi(command,text=True)

def kodiSendDown():
    command = '{"jsonrpc":"2.0","method":"Input.Down","id":0}' 
    sendCmdToKodi(command,text=True)

def kodiSendEnter():
    command = '{"jsonrpc":"2.0","method":"Input.Select","id":0}' 
    sendCmdToKodi(command,text=True)

def kodiSendBack():
    command = '{"jsonrpc":"2.0","method":"Input.Back","id":0}' 
    sendCmdToKodi(command,text=True)

def kodiSendLeft():
    command = '{"jsonrpc":"2.0","method":"Input.Left","id":0}' 
    sendCmdToKodi(command,text=True)

def kodiSendRight():
    command = '{"jsonrpc":"2.0","method":"Input.Right","id":0}' 
    sendCmdToKodi(command,text=True)

def kodiSendMessage(title='',message='',image='DefaultAddonTvInfo.png'):
    command = '{"jsonrpc":"2.0","method":"GUI.ShowNotification","params":{"title":"%s","message":"%s","image":"%s"},"id":1}'%(title,message,image)
    sendCmdToKodi(command,text=True)

def kodiSendHome():
    command = '{"jsonrpc":"2.0","method":"Input.Home","id":0}' 
    sendCmdToKodi(command,text=True)

def kodiMuteUnmute():
    command = '{"jsonrpc":"2.0","id":1,"method":"Application.SetMute","params": { "mute": "toggle" }}'
    sendCmdToKodi(command,text=True)


def sendCmdToKodi(cmd,text=False):
    req = urllib2.Request('http://192.168.1.15:8080/jsonrpc')
    req.add_header('Content-Type', 'application/json')
    if not text:
        response = urllib2.urlopen(req, json.dumps(cmd))
    else:
        response = urllib2.urlopen(req, cmd)
    return response.read()
