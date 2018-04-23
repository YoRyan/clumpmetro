#!/usr/bin/env python3

# use me: ./record_arrivals.py 559 4039 591 610 2821 >dump.csv

import json
import sys
import urllib.request
from datetime import datetime, timedelta
from socket import timeout
from time import sleep

__author__ = "Ryan Young"
__email__ = "rayoung@utexas.edu"
__license__ = "public domain"

def get_trip_updates():
    data = None
    while data is None:
        try:
            req = urllib.request.urlopen('https://data.texas.gov/download/mqtr-wwpy/text%2Fplain',
                                         timeout=30)
            data = json.load(req)
        except (urllib.request.URLError, json.JSONDecodeError, timeout):
            sleep(10)
            break
    return data

def departures_for_stop(trip_updates, stop_id):
    """Return dict of time -> trip data"""
    try:
        stop_time_updates = lambda entity: [stu for stu in entity['trip_update']['stop_time_update']
                                            if stu['stop_id'] == str(stop_id)]
        inbound_trips = [(entity['trip_update']['trip'], stop_time_updates(entity)[0])
                         for entity in trip_updates['entity']
                         if len(stop_time_updates(entity)) == 1]
        return {datetime.fromtimestamp(stu['departure']['time']): trip
                for trip, stu in inbound_trips}
    except (ValueError, KeyError):
        return {}

if __name__ == '__main__':
    STOP_IDS = sys.argv[1:]

    print('stop id', 'arrival time', 'route', 'trip id', sep=',')
    tracking_trips = {stop: {} for stop in STOP_IDS}
    while True:
        data = get_trip_updates()
        retrieved = datetime.fromtimestamp(data['header']['timestamp'])

        for stop in STOP_IDS:
            # track all listed trips
            for _, departure in departures_for_stop(data, stop).items():
                trip_id = departure['trip_id']
                route = departure['route_id']
                tracking_trips[stop][trip_id] = (retrieved, route)

            # finalize trips that haven't been seen in awhile
            to_remove = []
            for trip_id, (last_seen, route) in tracking_trips[stop].items():
                if abs(retrieved - last_seen) >= timedelta(minutes=15):
                    print(stop,
                          last_seen.isoformat(timespec='seconds'),
                          route,
                          trip_id,
                          sep=',')
                    to_remove.append(trip_id)
            for trip_id in to_remove:
                tracking_trips[stop].pop(trip_id)

        sys.stdout.flush()
        sleep(30)

