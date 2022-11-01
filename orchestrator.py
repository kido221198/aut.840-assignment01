import requests
import json
from datetime import datetime
import random

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


class Workstation(object):
    def __init__(self, ws_id, ip_conveyor, ip_robot, dest_url):
        self.zone_actions = {'1': ['Transfer12', 'Transfer14'],
                             '2': ['Transfer23'],
                             '3': ['Transfer35'],
                             '4': ['Transfer45'],
                             '5': []}
        self.zones = {'1': None, '2': None, '3': None, '4': None, '5': None}
        self.id = ws_id
        self.ip_conveyor = 'http://' + ip_conveyor
        self.ip_robot = 'http://' + ip_robot
        self.dest_url = 'http://' + dest_url
        self.pen_color = ''
        self.subscribed_events = {'Z1_Changed': False, 'Z2_Changed': False,
                                  'Z3_Changed': False, 'Z4_Changed': False,
                                  'Z5_Changed': False,
                                  'PenChangeStarted': False, 'PenChangeEnded': False,
                                  'DrawStartExecution': False, 'DrawEndExecution': False}
        self.history = []
        self.list_order = {}
        self.pending_orders = []
        self.completed_orders = []
        self.subscribe_all()

    def calibrate(self):
        url = self.ip_robot + '/rest/services/Calibrate'
        print('Sending request POST ' + url)
        result = requests.post(url, json={})

        if result.status_code != 202:
            print('Error: ' + str(result.status_code))
            return EXIT_FAILURE, 'Request error!'

        return EXIT_SUCCESS, 'Calibration in progress..'

    def update_all(self):
        for i in range(5):
            self.get_zone(str(i + 1))

        self.get_pen_color()

    def get_zone(self, zone_id):
        url = self.ip_conveyor + '/rest/services/Z' + zone_id
        print('Sending request POST ' + url)
        result = requests.post(url, json={})
        # print(str(result.content))

        if result.status_code != 200:
            print('Error: ' + str(result.status_code))
            return EXIT_FAILURE, 'Request error!'

        content = json.loads(result.content)
        pallet_id = content['PalletID']

        if pallet_id == "-1":
            self.zones[zone_id] = None

        else:
            self.zones[zone_id] = str(pallet_id)

        return EXIT_SUCCESS, 'Get Info complete!'

    def trans_zone(self, former, latter):
        self.get_zone(former)
        self.get_zone(latter)

        if not self.zones[former]:
            print('Zone ' + former + ' is empty')
            return EXIT_FAILURE, 'Zone ' + former + ' is empty'

        elif self.zones[latter]:
            print('Zone ' + latter + ' is not empty')
            return EXIT_FAILURE, 'Zone ' + latter + ' is not empty'

        else:
            url = self.ip_conveyor + '/rest/services/TransZone' + former + latter
            print('Sending request POST ' + url)
            result = requests.post(url, json={'destUrl': self.dest_url})

            if result.status_code != 202:
                print('Error: ' + str(result.status_code))
                return EXIT_FAILURE, 'Request error!'

            return EXIT_SUCCESS, 'Transfer completed!'

    def get_pen_color(self):
        url = self.ip_robot + '/rest/services/GetPenColor'
        print('Sending request POST ' + url)
        result = requests.post(url, json={})

        if result.status_code != 200:
            print('Error: ' + str(result.status_code))
            return EXIT_FAILURE, 'Request error!'

        color = str(result.content)[25:-7]

        if color == "NA":
            self.pen_color = 'N/A'

        else:
            self.pen_color = color

        return EXIT_SUCCESS, 'Get Info complete!'

    def draw_recipe(self, recipe):
        self.get_zone('3')

        if not self.zones['3']:
            return EXIT_FAILURE, 'Zone 3 is empty'

        else:
            url = self.ip_robot + '/rest/services/Draw' + str(recipe)
            print('Sending request POST ' + url)
            result = requests.post(url, json={'destUrl': self.dest_url})

            if result.status_code != 202:
                print('Error: ' + str(result.status_code))
                return EXIT_FAILURE, 'Request error!'

            return EXIT_SUCCESS, 'Draw completed!'

    def change_pen(self, new_color):
        url = self.ip_robot + '/rest/services/ChangePen' + new_color
        print('Sending request POST ' + url)
        result = requests.post(url, json={'destUrl': self.dest_url})

        if result.status_code != 202:
            print('Error: ' + str(result.status_code))
            return EXIT_FAILURE, 'Request error!'

        return EXIT_SUCCESS, 'Change pen completed!'

    def replace_paper(self):
        url = self.ip_robot + '/rest/services/ReplacePaper'
        print('Sending request POST ' + url)
        result = requests.post(url, json={'destUrl': self.dest_url})

        if result.status_code != 202:
            print('Error: ' + str(result.status_code))
            return EXIT_FAILURE, 'Request error!'

        return EXIT_SUCCESS, 'Paper replacement completed!'

    def conveyor_event_handler(self, event_id, pallet_id):
        if event_id == 'Z1_Changed':
            if pallet_id == '-1':
                self.zones['1'] = None

            elif self.pending_orders:
                self.zones['1'] = pallet_id
                print(self.zones['1'], self.pending_orders)
                order = self.pending_orders.pop(0)
                frame = order['frame_id']
                screen = order['screen_id']
                keyboard = order['keyboard_id']
                f_color = order['f_color']
                s_color = order['s_color']
                k_color = order['k_color']
                self.list_order[pallet_id] = Pallet(frame, screen, keyboard, f_color, s_color, k_color)

                if not self.zones['2']:
                    self.trans_zone('1', '2')

                elif not self.zones['4']:
                    self.trans_zone('1', '4')

            else:
                self.zones['1'] = pallet_id
                self.list_order[pallet_id] = None

        if event_id == 'Z2_Changed':
            if pallet_id == '-1':
                self.zones['2'] = None

                if self.zones['1'] and self.list_order[self.zones['1']]:
                    self.trans_zone('1', '2')

            else:
                self.zones['2'] = pallet_id

                if not self.zones['3']:
                    # if self.pen_color == self.list_order[pallet_id].f_color:
                    #     self.trans_zone('2', '3')
                    #
                    # else:
                    #     self.change_pen(self.list_order[pallet_id].f_color')

                    self.trans_zone('2', '3')

        if event_id == 'Z3_Changed':
            if pallet_id == '-1':
                self.zones['3'] = None

                if self.zones['2']:
                    # if self.list_order[pallet_id].f_color == self.pen_color:
                    #     self.trans_zone('2', '3')
                    #
                    # else:
                    #     self.change_pen(self.list_order[pallet_id].f_color)

                    self.trans_zone('2', '3')

            else:
                self.zones['3'] = pallet_id
                self.draw_recipe(self.list_order[pallet_id].frame_id)

                # if not self.zones['5']:
                #     self.completed_orders.append(self.list_order[pallet_id])
                #     self.list_order.pop(pallet_id)
                #     self.trans_zone('3', '5')

        if event_id == 'Z4_Changed':
            if pallet_id == '-1':
                self.zones['4'] = None

                if self.zones['1'] and self.list_order[self.zones['1']]:
                    self.trans_zone('1', '4')

            else:
                self.zones['4'] = pallet_id

                if not self.zones['5']:
                    self.trans_zone('4', '5')

        if event_id == 'Z5_Changed':
            if pallet_id == '-1':
                del self.list_order[self.zones['5']]
                self.zones['5'] = None

                # if self.list_order[self.zones['3']].complete == 6:
                #     self.trans_zone('3', '5')

                if self.zones['3'] and not self.list_order[self.zones['3']]:
                    self.trans_zone('3', '5')

                elif self.zones['4']:
                    self.trans_zone('4', '5')

            else:
                self.zones['5'] = pallet_id

    def robot_event_handler(self, event_id):
        if event_id == 'PenChangeEnded':
            if self.zones['2'] and not self.zones['3']:
                self.trans_zone('2', '3')

        elif event_id == 'DrawEndExecution':
            pallet_id = self.zones['3']
            self.list_order[pallet_id].complete += 1

            if self.list_order[pallet_id].complete == 1:
                self.draw_recipe(self.list_order[pallet_id].screen_id)

            elif self.list_order[pallet_id].complete == 2:
                self.draw_recipe(self.list_order[pallet_id].keyboard_id)

            else:
                if not self.zones['5']:
                    self.completed_orders.append(self.list_order[pallet_id])
                    self.list_order.pop(pallet_id)
                    self.trans_zone('3', '5')

    def event_handler(self, json_data):
        if json_data:
            json_data['timestamp'] = datetime.now()
            print('Received event:', json_data)
            self.history.insert(0, json_data)
            event_id = json_data['id']

            if event_id[0] == 'Z':
                pallet_id = json_data['payload']['PalletID']
                self.conveyor_event_handler(event_id, pallet_id)

            else:
                self.robot_event_handler(event_id)

            return EXIT_SUCCESS, 'Updated successfully!'

        else:
            print('Received event with empty data:', json_data)
            return EXIT_FAILURE, 'Updated none!'

    def unsubscribe_event(self, target, event_id):
        url = '/rest/events/' + event_id + '/notifs'

        if target == 'robot':
            url = self.ip_robot + url

        elif target == 'conveyor':
            url = self.ip_conveyor + url

        else:
            return EXIT_FAILURE, 'Invalid target!'

        if self.subscribed_events[event_id]:
            print('Sending request DELETE ' + url)
            result = requests.delete(url)

            if result.status_code != 202:
                print('Error: ' + str(result.status_code))
                return EXIT_FAILURE, 'Request error!'

            self.subscribed_events[event_id] = False

        return EXIT_SUCCESS, 'Changed event ' + event_id + ' subscription!'

    def subscribe_event(self, target, event_id):
        url = '/rest/events/' + event_id + '/notifs'

        if target == 'robot':
            url = self.ip_robot + url

        elif target == 'conveyor':
            url = self.ip_conveyor + url

        else:
            return EXIT_FAILURE, 'Invalid target!'

        if not self.subscribed_events[event_id]:
            print('Sending request POST ' + url)
            result = requests.post(url, json={'destUrl': self.dest_url})

            if result.status_code != 200:
                print('Error: ' + str(result.status_code))
                return EXIT_FAILURE, 'Request error!'

            self.subscribed_events[event_id] = True

        return EXIT_SUCCESS, 'Changed event ' + event_id + ' subscription'

    def subscribe_all(self):
        for event, state in self.subscribed_events.items():
            if not state:
                if event[0] == 'Z':
                    self.subscribe_event('conveyor', event)

                else:
                    self.subscribe_event('robot', event)

        return EXIT_SUCCESS, 'Subscribed all events'

    def unsubscribe_all(self):
        for event, state in self.subscribed_events.items():
            if state:
                if event[0] == 'Z':
                    self.unsubscribe_event('conveyor', event)

                else:
                    self.unsubscribe_event('robot', event)

        return EXIT_SUCCESS, 'Unsubscribed all events'

    def new_order(self, frame, screen, keyboard, f_color, s_color, k_color):
        if self.zones['1'] and not self.list_order[self.zones['1']]:
            self.list_order[self.zones['1']] = Pallet(frame, screen, keyboard, f_color, s_color, k_color)

            if not self.zones['2']:
                self.trans_zone('1', '2')
                return EXIT_SUCCESS, 'New order has been made, transferring a pallet from Zone 1 to Zone 2!'

            elif not self.zones['4']:
                self.trans_zone('1', '4')
                return EXIT_SUCCESS, 'New order has been made, transferring a pallet from Zone 1 to Zone 4!'

        else:
            self.pending_orders.append({'frame_id': frame, 'screen_id': screen, 'keyboard_id': keyboard,
                                        'f_color': f_color, 's_color': s_color, 'k_color': k_color})
            return EXIT_SUCCESS, 'New order has been made and added to the pending list!'

    def random_order(self):
        color_set = ['RED', 'GREEN', 'BLUE']
        shape_set = ['1', '2', '3']
        frame = shape_set[random.randint(0, 2)]
        screen = shape_set[random.randint(0, 2)]
        keyboard = shape_set[random.randint(0, 2)]

        # Workstation currently cannot change pen when pallet at zone 3 presents
        color = color_set[random.randint(0, 2)]

        f_color = color
        s_color = color
        k_color = color

        # f_color = color_set[random.randint(0, 2)]
        # s_color = color_set[random.randint(0, 2)]
        # k_color = color_set[random.randint(0, 2)]
        self.new_order(frame, screen, keyboard, f_color, s_color, k_color)
        print('New random order has been made!')
        return EXIT_SUCCESS, 'New random order has been made!'


class Pallet(object):
    def __init__(self, frame, screen, keyboard, f_color, s_color, k_color):
        self.frame_id = int(frame)
        self.screen_id = int(screen) + 6
        self.keyboard_id = int(keyboard) + 3
        self.f_color = f_color
        self.s_color = s_color
        self.k_color = k_color
        self.complete = 0
