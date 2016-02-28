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
        replace(hours=-4).\
        to('US/Pacific').\
        format('YYYY-MM-DD HH:mm:ss')

    stop_cutoff = arrow.utcnow().\
        replace(days=3).\
        to('US/Pacific').\
        format('YYYY-MM-DD HH:mm:ss')

    eventful_events = list(session.query(Event).\
        filter(Event.eventful_popularity > 40).\
        filter(Event.start_time > start_cutoff).\
        filter(Event.start_time > stop_cutoff))

    songkick_events = list(session.query(Event).\
        filter(Event.songkick_popularity > 0).\
        filter(Event.start_time > start_cutoff).\
        filter(Event.start_time > stop_cutoff))

    eventbrite_events = list(session.query(Event).\
        filter(Event.eventbrite_id != None).\
        filter(Event.start_time > start_cutoff).\
        filter(Event.start_time > stop_cutoff))

    events = set(eventful_events + songkick_events + eventbrite_events)

    ranked_events = []
    for event in events:
        score = 0.0
        if event.eventful_popularity:
            score += event.eventful_popularity/170 * 3
        else:
            score += 1
        if event.songkick_popularity:
            score += float(min(event.songkick_popularity*10, 1) * 3)
        else:
            score += 1
        if event.venue.capacity:
            score += float(min(5000, event.venue.capacity)/5000 * 3)
        else:
            score += 1

        ranked_events.append((score, event))

    data = {}
    counter = 0
    for score, event in ranked[:500]:
        start_time = arrow.get(event.start_time).format('YYYY-MM-DD HH:mm')
        data['valleys/'+str(counter)] = {
            'id': counter,
            'name': event.name,
            'time': start_time,
            'rating': score/5,
            'lat': str(event.venue.lat),
            'long': str(event.venue.long)
        }
        end_time = arrow.get(event.end_time).format('YYYY-MM-DD HH:mm') if event.end_time else arrow.get(event.start_time).replace(hours=3).format('YYYY-MM-DD HH:mm')
        data['peaks/'+str(counter)] = {
            'id': counter,
            'name': event.name,
            'time': end_time,
            'rating': score/3,
            'lat': str(event.venue.lat),
            'long': str(event.venue.long)
        }
        counter += 1

    ref.update(data)


if __name__ == '__main__':
    main()
