from datetime import datetime
from time import sleep

from uber_rides.session import Session
from uber_rides.client import UberRidesClient

from secrets import UBER_SERVER_TOKEN
from sql import get_session, Event, UberPrice

def main():

    session = get_session()

    events = session.query(Event).\
        filter(Event.start_time > '2016-02-27 17:00:00').\
        filter(Event.start_time < '2016-02-27 23:00:00').\
        filter(Event.eventful_popularity > 40).\
        order_by(-Event.eventful_popularity)

    while True:

        print("Fetching Uber prices at " + str(datetime.now()))

        client = UberRidesClient(Session(server_token=UBER_SERVER_TOKEN))

        for event in events:
            response = client.get_price_estimates(
                event.venue.lat,
                event.venue.long,
                37.700,
                -122.4
            )

            for price in response.json['prices']:
                if price['display_name'] != 'uberX':
                    continue
                else:
                    price = UberPrice(
                        event=event,
                        surge=price['surge_multiplier'],
                        time=datetime.now()
                    )
                    session.add(price)
                    session.commit()
                    break

        sleep(180)


if __name__ == '__main__':
    main()
