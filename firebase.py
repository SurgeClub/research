from collections import OrderedDict
from datetime import datetime
from time import mktime

import arrow
import pyrebase

from sql import get_session, Event
from secrets import FIREBASE_URL, FIREBASE_KEY

ref = pyrebase.Firebase(FIREBASE_URL, FIREBASE_KEY)

def main():
    session = get_session()

    start_cutoff = arrow.utcnow().\
        replace(hours=-3).\
        to('US/Pacific').\
        format('YYYY-MM-DD HH:mm:ss')

    stop_cutoff = arrow.utcnow().\
        replace(hours=6).\
        to('US/Pacific').\
        format('YYYY-MM-DD HH:mm:ss')

    eventful_events = session.query(Event).\
        filter(Event.eventful_popularity > 40).\
        filter(Event.start_time > start_cutoff).\
        filter(Event.start_time > stop_cutoff).\
        order_by(Event.start_time).\
        limit(150)

    data = {}
    counter = 0
    for event in eventful_events:
        start_time = arrow.get(event.start_time).format('YYYY-MM-DD HH:mm')
        data['valleys/'+str(counter)] = {
            'name': event.name,
            'time': start_time,
            'rating': event.eventful_popularity/170,
            'lat': str(event.venue.lat),
            'long': str(event.venue.long)
        }
        end_time = arrow.get(event.end_time).format('YYYY-MM-DD HH:mm') if event.end_time else arrow.get(event.start_time).replace(hours=3).format('YYYY-MM-DD HH:mm')
        data['peaks/'+str(counter)] = {
            'name': event.name,
            'time': end_time,
            'rating': event.eventful_popularity/170,
            'lat': str(event.venue.lat),
            'long': str(event.venue.long)
        }
        counter += 1

    ref.update(data)


if __name__ == '__main__':
    main()
