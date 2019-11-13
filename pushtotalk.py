# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sample that implements a gRPC client for the Google Assistant API."""

import concurrent.futures
import json
import logging
import os
import os.path
import pathlib2 as pathlib
import sys
import time
import uuid

import click
import grpc
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)
from tenacity import retry, stop_after_attempt, retry_if_exception

import assistant_helpers
import audio_helpers
import browser_helpers
import device_helpers
import time

ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
END_OF_UTTERANCE = embedded_assistant_pb2.AssistResponse.END_OF_UTTERANCE
DIALOG_FOLLOW_ON = embedded_assistant_pb2.DialogStateOut.DIALOG_FOLLOW_ON
CLOSE_MICROPHONE = embedded_assistant_pb2.DialogStateOut.CLOSE_MICROPHONE
PLAYING = embedded_assistant_pb2.ScreenOutConfig.PLAYING
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5

response = {}

class SampleAssistant(object):

    def __init__(self, language_code, device_model_id, device_id,
                 conversation_stream, display,
                 channel, deadline_sec, device_handler):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id
        self.conversation_stream = conversation_stream
        self.display = display
        self.requestText = ""
        self.responseText = ""

        self.conversation_state = None

        self.is_new_conversation = True

        self.assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(channel)
        self.deadline = deadline_sec

        self.device_handler = device_handler

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if e:
            return False
        self.conversation_stream.close()

    def assist(self):

        continue_conversation = False
        device_actions_futures = []

        self.conversation_stream.start_recording()
        logging.debug('Recording audio request.')
        def iter_log_assist_requests():
             for c in self.gen_assist_requests():
                 assistant_helpers.log_assist_request_without_audio(c)
                 logging.debug("yield...")
                 yield c
             logging.debug('Reached end of AssistRequest iteration.')

        for resp in self.assistant.Assist(iter_log_assist_requests(),
                                          self.deadline):
            #logging.debug("resp: %s"%str(resp))
            responseCopy = assistant_helpers.log_assist_response_without_audio(resp)
            if responseCopy is not None:
                responseCopy = str(responseCopy)
                logging.debug("responseCopy: %s"%responseCopy)
                #classify response
                if 'transcript: "' in responseCopy:
                   requestText = responseCopy[responseCopy.find('transcript: "')+len('transcript: "'):]
                   requestText = requestText[:requestText.find('"')]
                   self.requestText = requestText
                elif 'supplemental_display_text: "' in responseCopy:
                   responseText = responseCopy[responseCopy.find('supplemental_display_text: "')+len('supplemental_display_text: "'):]
                   responseText = responseText[:responseText.find('"')]
                   self.responseText = responseText
                self.lastResponse = responseCopy
            if resp.event_type == END_OF_UTTERANCE:
                logging.info('End of audio request detected.')
                logging.info('Stopping recording.')
                self.conversation_stream.stop_recording()
            if resp.speech_results:
                textResult = ' '.join(r.transcript for r in resp.speech_results)
                logging.info('Transcript of user request: "%s".',textResult)
            if len(resp.audio_out.audio_data) > 0:
                if not self.conversation_stream.playing:
                    self.conversation_stream.stop_recording()
                    self.conversation_stream.start_playback()
                    logging.info('Playing assistant response.')
                self.conversation_stream.write(resp.audio_out.audio_data)
            if resp.dialog_state_out.conversation_state:
                conversation_state = resp.dialog_state_out.conversation_state
                logging.debug('Updating conversation state.')
                self.conversation_state = conversation_state
            if resp.dialog_state_out.volume_percentage != 0:
                volume_percentage = resp.dialog_state_out.volume_percentage
                logging.info('Setting volume to %s%%', volume_percentage)
                self.conversation_stream.volume_percentage = volume_percentage
            if resp.dialog_state_out.microphone_mode == DIALOG_FOLLOW_ON:
                continue_conversation = True
                logging.info('Expecting follow-on query from user.')
            elif resp.dialog_state_out.microphone_mode == CLOSE_MICROPHONE:
                continue_conversation = False
            if resp.device_action.device_request_json:
                device_request = json.loads(
                    resp.device_action.device_request_json
                )
                fs = self.device_handler(device_request)
                if fs:
                    device_actions_futures.extend(fs)
            if self.display and resp.screen_out.data:
                system_browser = browser_helpers.system_browser
                system_browser.display(resp.screen_out.data)

        if len(device_actions_futures):
            logging.info('Waiting for device executions to complete.')
            concurrent.futures.wait(device_actions_futures)

        logging.info('Finished playing assistant response.')
        self.conversation_stream.stop_playback()
        #return self.conversation_stream

    def gen_assist_requests(self):

        config = embedded_assistant_pb2.AssistConfig(
            audio_in_config=embedded_assistant_pb2.AudioInConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
            ),
            audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
                volume_percentage=self.conversation_stream.volume_percentage,
            ),
            dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                language_code=self.language_code,
                conversation_state=self.conversation_state,
                is_new_conversation=self.is_new_conversation,
            ),
            device_config=embedded_assistant_pb2.DeviceConfig(
                device_id=self.device_id,
                device_model_id=self.device_model_id,
            )
        )
        if self.display:
            config.screen_out_config.screen_mode = PLAYING
        # Continue current conversation with later requests.
        self.is_new_conversation = False
        # The first AssistRequest must contain the AssistConfig
        # and no audio data.
        yield embedded_assistant_pb2.AssistRequest(config=config)
        for data in self.conversation_stream:
            # Subsequent requests need audio data, but not config.
            yield embedded_assistant_pb2.AssistRequest(audio_in=data)

def main(project_id=None,
         device_model_id=None, 
         device_id=None, 
         input_audio_file=None, 
         output_audio_file=None,
         device_config=os.path.join(click.get_app_dir('googlesamples-assistant'),'device_config.json'),
         lang='en-US', 
         display=False, 
         verbose=False,
         api_endpoint=ASSISTANT_API_ENDPOINT,
         credentials=os.path.join(click.get_app_dir('google-oauthlib-tool'),'credentials.json'), 
         audio_sample_rate=audio_helpers.DEFAULT_AUDIO_SAMPLE_RATE, 
         audio_sample_width=audio_helpers.DEFAULT_AUDIO_SAMPLE_WIDTH,
         audio_iter_size=audio_helpers.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE, 
         audio_block_size=audio_helpers.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE, 
         audio_flush_size=audio_helpers.DEFAULT_AUDIO_DEVICE_FLUSH_SIZE,
         grpc_deadline=DEFAULT_GRPC_DEADLINE, 
         once=False):

    # Load OAuth 2.0 credentials.
    try:
        with open(credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))
            http_request = google.auth.transport.requests.Request()
            credentials.refresh(http_request)
    except Exception as e:
        logging.error('Error loading credentials: %s', e)
        logging.error('Run google-oauthlib-tool to initialize '
                      'new OAuth 2.0 credentials.')
        sys.exit(-1)

    # Create an authorized gRPC channel.
    grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
        credentials, http_request, api_endpoint)
    logging.info('Connecting to %s', api_endpoint)

    # Configure audio source and sink.
    audio_device = None
    if input_audio_file:
        audio_source = audio_helpers.WaveSource(
            open(input_audio_file, 'rb'),
            sample_rate=audio_sample_rate,
            sample_width=audio_sample_width
        )
    else:
        audio_source = audio_device = (
            audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=audio_sample_rate,
                sample_width=audio_sample_width,
                block_size=audio_block_size,
                flush_size=audio_flush_size
            )
        )
    fileName = "audio%s.wav"%str(time.time()).replace(".","")
    audio_sink = audio_helpers.WaveSink(
        open(fileName, 'wb'),
        sample_rate=audio_sample_rate,
        sample_width=audio_sample_width
    )

    # Create conversation stream with the given audio source and sink.
    conversation_stream = audio_helpers.ConversationStream(
        source=audio_source,
        sink=audio_sink,
        iter_size=audio_iter_size,
        sample_width=audio_sample_width,
    )

    if not device_id or not device_model_id:
        try:
            with open(device_config) as f:
                device = json.load(f)
                device_id = device['id']
                device_model_id = device['model_id']
                logging.info("Using device model %s and device id %s",
                             device_model_id,
                             device_id)
        except Exception as e:
            logging.warning('Device config not found: %s' % e)
            logging.info('Registering device')
            device_base_url = (
                'https://%s/v1alpha2/projects/%s/devices' % (api_endpoint,
                                                             project_id)
            )
            device_id = str(uuid.uuid1())
            payload = {
                'id': device_id,
                'model_id': device_model_id,
                'client_type': 'SDK_SERVICE'
            }
            session = google.auth.transport.requests.AuthorizedSession(
                credentials
            )
            r = session.post(device_base_url, data=json.dumps(payload))
            if r.status_code != 200:
                logging.error('Failed to register device: %s', r.text)
                sys.exit(-1)
            logging.info('Device registered: %s', device_id)
            pathlib.Path(os.path.dirname(device_config)).mkdir(exist_ok=True)
            with open(device_config, 'w') as f:
                json.dump(payload, f)
            logging.debug("finished main")


    device_handler = device_helpers.DeviceRequestHandler(device_id)
    logging.debug("starting sample assistant...")
    element = {}
    with SampleAssistant(lang, device_model_id, device_id,
                         conversation_stream, display,
                         grpc_channel, grpc_deadline,
                         device_handler) as assistant:
        logging.debug("assistant starts...")
        assistant.assist()
        logging.debug("assistant finishes....")
        element["request"] = assistant.requestText
        element["response"] = assistant.responseText
        element["audio"] = fileName
        response = element
    return element


if __name__ == '__main__':
    logging.debug("start main pushtotalk")
    element = main()
    logging.debug("finished main")
    logging.debug(str(element))
