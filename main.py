import snowboydecoder
import pushtotalk
import json
import google

import sys
import signal

interrupted = False

def _load_credentials(credentials_path):
    migrate = False
    with open(credentials_path, 'r') as f:
        credentials_data = json.load(f)
        if 'access_token' in credentials_data:
            migrate = True
            del credentials_data['access_token']
            credentials_data['scopes'] = [_ASSISTANT_OAUTH_SCOPE]
    if migrate:
        with open(credentials_path, 'w') as f:
            json.dump(credentials_data, f)
    credentials = google.oauth2.credentials.Credentials(token=None,**credentials_data)
    http_request = google.auth.transport.requests.Request()
    credentials.refresh(http_request)
    return credentials

credentials = _load_credentials("/home/pi/.config/google-oauthlib-tool/credentials.json")
http_request = google.auth.transport.requests.Request()
api_endpoint = 'embeddedassistant.googleapis.com'

grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
            credentials, http_request, api_endpoint)

#pushtotalk.main()

detector = snowboydecoder.HotwordDetector('/home/pi/assistant/resources/alexa.umdl',sensitivity=[0.5])

def signal_handler(signal, frame):
    global interrupted
    print("has been detected the ctrl+c signal")
    interrupted = True

def interrupt_callback():
    global interrupted
    if interrupted:
        print("state is %s "%str(interrupted))
    return interrupted

def detect_callback():
    detector.terminate()
    snowboydecoder.play_audio_file(snowboydecoder.DETECT_DING)
    pushtotalk.main()
    snowboydecoder.play_audio_file(snowboydecoder.DETECT_DONG)
    detector.start(detected_callback=detect_callback, interrupt_check=interrupt_callback, sleep_time=0.03)

signal.signal(signal.SIGINT, signal_handler)

print('Listening... Press Ctrl+C to exit')

detector.start(detected_callback=detect_callback,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

detector.terminate()
