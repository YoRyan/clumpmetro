#!/usr/bin/env python3

# use me: ./record_arrivals.py 559 4039 591 610 2821 >dump.csv

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
    if len(inbound_trips) > 0:
        return {datetime.fromtimestamp(stu['arrival']['time']): trip
                for (trip, stu) in inbound_trips}
    else:
        return {}

if __name__ == '__main__':
    STOP_IDS = sys.argv[1:]

    print('stop id', 'arrival time', 'route', 'trip id', sep=',')
    seen_routes = {stop: {} for stop in STOP_IDS}
    seen_trips = {stop: set() for stop in STOP_IDS}
    while True:
        data = get_trip_updates()
        retrieved = datetime.fromtimestamp(data['header']['timestamp'])

        for stop in STOP_IDS:
            departures = [d for (_, d) in departures_for_stop(data, stop).items()]
            future_trips = set([d['trip_id'] for d in departures])

            # seen before, now gone
            for departed_trip in seen_trips[stop] - future_trips:
                print(stop,
                      retrieved.isoformat(timespec='seconds'),
                      seen_routes[stop][departed_trip],
                      departed_trip,
                      sep=',')
                seen_trips[stop].remove(departed_trip)
                seen_routes[stop].pop(departed_trip)

            # not seen before
            for future_trip in future_trips - seen_trips[stop]:
                departure = [d for d in departures if d['trip_id'] == future_trip][0]
                seen_trips[stop].add(future_trip)
                seen_routes[stop][future_trip] = departure['route_id']

        sys.stdout.flush()
        sleep(30)

