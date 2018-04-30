#!/usr/bin/env python3

import csv
import datetime

def load_data(filename):
    data = []
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            arrival = {'stop id': int(row['stop id']),
                       'arrival time': datetime.datetime.strptime(row['arrival time'],
                                                                  '%Y-%m-%dT%H:%M:%S'),
                       'route': int(row['route'])}
            data.append(arrival)
    return data

def calc_headways(arrivals):
    assert len(arrivals) > 1

    headways = []
    last = arrivals[0]
    for current in arrivals[1:]:
        category = headway_category(last, current)
        if category is not None:
            headways.append({'arrival time': current['arrival time'],
                             'interval': current['arrival time'] - last['arrival time'],
                             'adherence': category })
        last = current

    return [h for h in headways if h['interval'] < datetime.timedelta(hours=1)]

def headway_category(last_arrival, arrival):
    interval = arrival['arrival time'] - last_arrival['arrival time']
    last_arrival_time = last_arrival['arrival time'].time()
    arrival_time = arrival['arrival time'].time()

    def category(actual, target):
        if actual < datetime.timedelta(minutes=3):
            return 'BUNCHED'
        elif actual < target + datetime.timedelta(minutes=2):
            return 'ON TIME'
        elif actual < target + datetime.timedelta(minutes=5):
            return '2-5 MIN LATE'
        elif actual < target + datetime.timedelta(minutes=10):
            return '5-10 MIN LATE'
        else:
            return '10+ MIN LATE'

    # weekday schedule only
    if arrival_time >= datetime.time(hour=20) or arrival_time < datetime.time(hour=4):
        return category(interval, datetime.timedelta(minutes=20))
    elif arrival_time >= datetime.time(hour=18):
        return category(interval, datetime.timedelta(minutes=15))
    elif last_arrival_time >= datetime.time(hour=7):
        return category(interval, datetime.timedelta(minutes=10))
    else:
        return category(interval, datetime.timedelta(minutes=15))


arrivals = load_data('801-NB.csv')
arrivals = [a for a in arrivals if a['stop id'] == 610 and
                                   a['route'] == 801]
print('arrival time', 'interval', 'adherence', sep=',')
for h in calc_headways(arrivals):
    print(h['arrival time'].isoformat(),
          h['interval'].seconds // 60,
          h['adherence'],
          sep=',')

