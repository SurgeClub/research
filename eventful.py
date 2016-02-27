import requests

from sql import get_session, Venue, Event, Category
from secrets import EVENTFUL_KEY

def main():

    params = {
        "app_key": EVENTFUL_KEY,
        "location": "San Francisco",
        "include": "categories,popularity,tickets,subcategories",
        "page_size": "50",
        "sort_order": "popularity",
        "date": "This Week",
    }

    page = 1
    data = {}

    session = get_session()

    while True:
        params['page_number'] = page

        r = requests.get('https://api.eventful.com/json/events/search', params=params)

        if r.status_code != 200 or not r.json().get('events'):
            return

        stop = True
        for e in r.json()['events']['event']:
            if session.query(Event).filter(Event.eventful_id==e['id']).first():
                continue

            venue = session.query(Venue).filter(Venue.name==e['venue_name']).filter(Venue.zip_code==e['postal_code']).first()
            if not venue:
                venue = Venue(name=e['venue_name'],
                              address='{}, {}, {}'.format(e['venue_address'], e['city_name'], e['region_abbr']),
                              zip_code=e['postal_code'],
                              lat=e['latitude'],
                              long=e['longitude'],
                              description=e['venue_url'],
                              eventful_id=e['venue_id'])
                session.add(venue)
                session.commit()

            event = Event(name=e['title'],
                          start_time=e['start_time'],
                          end_time=e['stop_time'],
                          eventful_popularity=int(e['popularity']),
                          eventful_id=e['id'],
                          description=e['description'],
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

        if stop:
            session.commit()
            break
        page += 1

if __name__ == '__main__':
    main()
