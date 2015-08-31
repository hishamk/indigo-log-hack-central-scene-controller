"""
The MIT License (MIT)

Copyright (c) 2015 Hisham Khalifa <hisham@saikel.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from tail import tail

import time
import os
import requests

LOG_PATH = r"/Library/Application Support/Perceptive Automation/Indigo 6/Logs/indigo_log.txt"

received_events = []
controllers = {}

# Credentials
user = 'admin'
password = 'password'
host = '127.0.0.1'
port = 8176

class CommandType:
    SINGLE_CLICK = '00'
    DOUBLE_CLICK = '03'
    HOLD = '02'
    RELEASE = '01'


class ZWaveRCVDLogEvent:
    def __init__(self, bytes):
        self.bytes = bytes

        self.controller_id = None
        self.button_id = None
        self.press_type = None
        self.level = None

        self.valid_event = True

        self.parse()

    def parse(self):
        try:
            if self.bytes is not None:
                self.controller_id = self.bytes[5]
                self.button_id = self.bytes[11]
                self.level = self.bytes[9]
                press_type = self.bytes[10]
                if press_type == '00':
                    self.press_type = CommandType.SINGLE_CLICK
                elif press_type == '03':
                    self.press_type = CommandType.DOUBLE_CLICK
                elif press_type == '02':
                    self.press_type = CommandType.HOLD
                elif press_type == '01':
                    self.press_type = CommandType.RELEASE
        except:
            self.valid_event = False

    def __str__(self):
        return "Central Scene Command: Controller {}, Button {}, Type {}, Level {}, Valid {}".format(self.controller_id,
                                                                                                     self.button_id,
                                                                                                     self.press_type,
                                                                                                     self.level,
                                                                                                     self.valid_event)


class EightButtonController:
    def __init__(self, id):
        self.room = None
        self.id = id
        self.single_click_action_mappings = {}
        self.double_click_action_mappings = {}
        self.hold_button_dimmer_mappings = {}
        self.discard_next_event = False

    def addSingleClickActionMapping(self, button_id, action_group):
        self.single_click_action_mappings[button_id] = action_group

    def addDoubleClickActionMapping(self, button_id, action_group):
        self.double_click_action_mappings[button_id] = action_group

    def addHoldButtonDimmerMapping(self, button_id, device_id, down=False):
        self.hold_button_dimmer_mappings[button_id] = device_id

    def doRequest(self, request):
        try:
            if self.discard_next_event:
                # Last event was a double click (which ends with a single click event that we need to dismiss)
                self.discard_next_event = False
                return
            if request.press_type == CommandType.SINGLE_CLICK:
                action_group = self.single_click_action_mappings[request.button_id]
                if action_group is not None:
                    doActionGroup(action_group)
            elif request.press_type == CommandType.DOUBLE_CLICK:
                action_group = self.double_click_action_mappings[request.button_id]
                self.discard_next_event = True
                if action_group is not None:
                    doActionGroup(action_group)
            elif request.press_type == CommandType.HOLD:
                device = self.hold_button_dimmer_mappings[request.button_id]
                if device is not None:
                    brightness = request.level
                    doDimmingAction(device, brightness)
        except Exception as e:
            print("No action defined" + str(e))


def get_last_controller_events(num_events, controller_ids):
    log_file = open(LOG_PATH, 'r')
    lines = tail(log_file, num_events)

    new_events = []

    for line in lines:
        line = line.strip()
        components = line.split(' ')

        if len(components) != 18:
            continue

        if components[1] in received_events:
            continue

        received_events.append(components[1])

        if components[10] == '05' and components[11] == '5B':  # Central scene command class?
            request_bytes = components[4:17]
            if request_bytes[5] in controller_ids:
                new_event = ZWaveRCVDLogEvent(request_bytes)
                new_events.append(new_event)
                print(request_bytes)

    log_file.close()

    if len(new_events) > 0:
        return new_events

    return None


def doActionGroup(action_group_title):
    url = "http://{}:{}/actions/{}?_method=execute".format(host, port, action_group_title)

    requests.get(url, auth=requests.auth.HTTPDigestAuth(user, password))

    print("Action group {}".format(action_group_title))


def doDimmingAction(device_title, brightness):
    brightness = int(brightness, 16)
    OldRange = (255 - 0)
    NewRange = (100 - 0)
    brightness = int((((brightness - 0) * NewRange) / OldRange) + 0)

    url = "http://{}:{}/devices/{}?brightness={}&_method=put".format(host, port, device_title, brightness)

    requests.get(url, auth=requests.auth.HTTPDigestAuth(user, password))

    print("Dimming device {}, level {}".format(device_title, brightness))


def execute_events(events):
    if events is not None:
        for event in events:
            if event.controller_id in controllers:
                controller = controllers[event.controller_id]
                controller.doRequest(event)


def setup_controllers():
    # Controller 1 (id 3) (Kitchen)
    # -----------------------------
    controller = EightButtonController('38')

    # General
    controller.addSingleClickActionMapping('01', 'Guidelights On (100%)')  # Button 1 - For single click
    controller.addDoubleClickActionMapping('01', 'Guidelights Off')  # Button 1 - For double click
    #controller.addHoldButtonDimmerMapping('05', 'Counter lights')  # Button 5 - For hold/release

    # Scenes
    #controller.addSingleClickActionMapping('05', 'Toggle kitchen lights')  # Button 5 - For single click

    # Appliances
    #controller.addSingleClickActionMapping('07', 'Turn Off Oven')  # Button 7 - For single click
    #controller.addSingleClickActionMapping('07', 'Turn Off Coffee Maker')  # Button 7 - For single click
    #controller.addSingleClickActionMapping('07', 'Turn Off TV')  # Button 7 - For single click

    controllers['38'] = controller


def run_loop():
    mtime_last = 0
    mtime_cur = mtime_last

    while True:
        time.sleep(0.05)

        if os.path.isfile(LOG_PATH):
            mtime_cur = os.path.getmtime(LOG_PATH)
            if mtime_cur != mtime_last:
                new_events = get_last_controller_events(10, ['38', ])
                execute_events(new_events)

            mtime_last = mtime_cur


if __name__ == '__main__':
    print("Stop-gap central scene hack for IndigoHome.")
    setup_controllers()
    run_loop()
