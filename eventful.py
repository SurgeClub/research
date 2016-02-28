import requests
import arrow
from sqlalchemy.exc import IntegrityError

from sql import get_session, Venue, Event, Category
from secrets import EVENTFUL_KEY

def main():

    params = {
        "app_key": EVENTFUL_KEY,
        "location": "San Francisco",
        "include": "categories,popularity,tickets,subcategories",
        "page_size": "100",
        "sort_order": "popularity",
        "date": "This Week",
    }

    page = 22
    data = {}

    session = get_session()
    time_cutoff = arrow.utcnow().replace(days=-1)

    while True:
        params['page_number'] = page

        r = requests.get('https://api.eventful.com/json/events/search', params=params)

        if r.status_code != 200 or not r.json().get('events'):
            return

        for e in r.json()['events']['event']:

            if not e.get('start_time') or arrow.get(e['start_time']+'-08:00') < time_cutoff:
                print("Skipping {} @ {}".format(e['title'], e['start_time']))
                continue

            if session.query(Event).filter(Event.eventful_id==e['id']).first():
                continue

            print("Trying {} @ {}".format(e['title'], e['venue_name']))

            try:
                venue = session.query(Venue).filter(Venue.eventful_id==e['venue_id']).first()
                if not venue:
                    venue = Venue(name=e['venue_name'],
                                  address='{}, {}, {} {}'.format(e['venue_address'], e['city_name'], e['region_abbr'], e['postal_code']),
                                  lat=e['latitude'],
                                  long=e['longitude'],
                                  eventful_id=e['venue_id'])
                    session.add(venue)
                    session.commit()

                event = Event(name=e['title'],
                              start_time=e['start_time'],
                              end_time=e['stop_time'],
                              eventful_popularity=int(e['popularity']),
                              eventful_id=e['id'],
                              image_url=e['image']['medium']['url'] if e.get('image') else None,
                              venue=venue)
                session.add(event)
                session.commit()

                for c in e['categories']['category']:
                    category = session.query(Category).filter(Category.type==c['id']).first()
                    if not category:
                        category = Category(type=c['id'], name=c['name'])
                        session.add(category)
                    event.categories.append(category)
                    session.commit()
            except UnicodeEncodeError:
                session.rollback()
                print("FAILED: {} @ {}".format(e['title'], e['venue_name']))
                continue

            except IntegrityError:
                session.rollback()
                print("DUPLICATE: {} @ {}".format(e['title'], e['venue_name']))
                continue

        page += 1
        print('----------On to page {}------------'.format(page))
    session.commit()



if __name__ == '__main__':
    main()
