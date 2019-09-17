import snowboydecoder

detector = snowboydecoder.HotwordDetector('/home/pi/assistant/resources/alexa.umdl',sensitivity=[0.5])

detector.start()
