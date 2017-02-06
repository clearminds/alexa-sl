import os
import requests


class SL():
    def __init__(self, api_key, site_id=None, time_window=60, bus=False, metro=False, train=False, tram=False, ship=False, journey_direction=None):
        if not api_key:
            raise ValueError('No API_KEY set')
        self.api_key = api_key
        self.site_id = site_id
        self.time_window = time_window
        self.bus = bus
        self.metro = metro
        self.train = train
        self.tram = tram
        self.ship = ship
        self.journey_direction = None

    def reset_filter(self):
        self.site_id = None
        self.time_window = 60
        self.bus = False
        self.metro = False
        self.train = False
        self.tram = False 
        self.ship = False
        self.journey_direction = None

    def _get_realtime(self, site_id=None):
        if site_id and self.site_id != site_id:
            self.site_id = site_id
        if not self.site_id:
            raise ValueError('No site_id set')

        params = {'key': self.api_key,
                  'timewindow': self.time_window,
                  'bus': self.bus,
                  'metro': self.metro,
                  'train': self.train,
                  'tram': self.tram,
                  'ship': self.ship,
                  'siteid': self.site_id
                 }
        
        self.transporatation = []
        if self.bus:
            self.transporatation.append('Buses')
        if self.ship:
            self.transporatation.append('Ships')
        if self.train:
            self.transporatation.append('Trains')
        if self.tram:
            self.transporatation.append('Trams')
        if self.metro:
            self.transporatation.append('Metros')

        response = requests.get('http://api.sl.se/api2/realtimedeparturesV4.json', params=params)
        if response.status_code != 200:
            raise ValueError('Wrong reply from api.sl.se, %s' % response.status_code)
        try:
            json = response.json()
        except:
            raise ValueError('Not a valid JSON response from api.sl.se')
        if json['StatusCode'] != 0:
            raise ValueError('Received non zero StatusCode from api.sl.se - %s' % json['StatusCode'])
        return json

    def simple_list(self, site_id=None):
        if site_id and self.site_id != site_id:
            self.site_id = site_id
        
        if not self.site_id:
            raise ValueError('No site_id set')
        
        json = self._get_realtime()
        deviations = json['ResponseData'].get('StopPointDeviations',[])
        response = [] 
        for t in self.transporatation:
            for m in json['ResponseData'][t]:
                if m['DisplayTime'] == 'Nu':
                    continue 
                if self.journey_direction and m['JourneyDirection'] != int(self.journey_direction):
                    continue
                if ':' in m['DisplayTime']:
                    m['DisplayTime'] = 'at ' + m['DisplayTime']
                else:
                    m['DisplayTime'] = 'in ' + m['DisplayTime']
                    if m['DisplayTime'] == 'in 1 min':
                        m['DisplayTime'] = m['DisplayTime'].replace(' min', ' minute')
                    else:
                        m['DisplayTime'] = m['DisplayTime'].replace(' min', ' minutes')
                response.append( { 'line_number': m['LineNumber'],
                                   'time_left': m['DisplayTime'],
                                   'destination': m['Destination'],
                                   'transport_type': m['TransportMode'].capitalize(),
                                   'journey_direction': m['JourneyDirection'],
                                } )
        return response, deviations


if __name__ == '__main__':
    sl = SL(os.environ['SL_API_KEY'])
    print(1945)
    sl.bus = True
    print(sl.simple_list(1945))
    sl.reset_filter()
    sl.metro = True
    print(9161)
    print(sl.simple_list(9161))

