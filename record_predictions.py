#!/usr/bin/env python3

# use me: ./record_predictions.py 559 4039 591 610 2821 >dump.csv

import json
import sys
import urllib.request
from datetime import datetime
from time import sleep

def get_trip_updates():
    data = None
    while data is None:
        try:
            req = urllib.request.urlopen('https://data.texas.gov/download/mqtr-wwpy/text%2Fplain',
                                         timeout=30)
            data = json.load(req)
        except (urllib.request.URLError, json.JSONDecodeError):
            sleep(10)
            break
    return data

def departures_for_stop(trip_updates, stop_id):
    """Return dict of time -> trip data"""
    stop_time_updates = lambda entity: [stu for stu in entity['trip_update']['stop_time_update']
                                        if stu['stop_id'] == str(stop_id)]
    inbound_trips = [(entity['trip_update']['trip'], stop_time_updates(entity)[0])
                     for entity in trip_updates['entity']
                     if len(stop_time_updates(entity)) == 1]
    return {datetime.fromtimestamp(stu['arrival']['time']): trip for (trip, stu) in inbound_trips}

if __name__ == '__main__':
    STOP_IDS = sys.argv[1:]

    print('updated', 'stop id', 'predicted arrival', 'route', 'trip id', sep=',')
    while True:
        data = get_trip_updates()
        retrieved = datetime.fromtimestamp(data['header']['timestamp'])
        for stop in STOP_IDS:
            for (t, d) in departures_for_stop(data, stop).items():
                print(retrieved.isoformat(timespec='seconds'), stop,
                      t.isoformat(timespec='minutes'), d['route_id'], d['trip_id'],
                      sep=',')
        sys.stdout.flush()
        sleep(30)

