from datetime import datetime
from time import sleep
import json
import requests

from secrets import LYFT_CLIENT_ID, LYFT_CLIENT_SECRET
from sql import get_session, Event, LyftPrice

def main():

    session = get_session()

    events = session.query(Event).\
        filter(Event.start_time > '2016-02-28 09:00:00').\
        filter(Event.start_time < '2016-02-28 16:00:00').\
        filter(Event.eventful_popularity > 40).\
        order_by(-Event.eventful_popularity)

    while True:

        print("Fetching Lyft prices at " + str(datetime.now()))

        lyft_response = requests.post(
            url="https://api.lyft.com/oauth/token",
            headers={
                "Content-Type": "application/json",
            },
            auth=(LYFT_CLIENT_ID, LYFT_CLIENT_SECRET),
            data=json.dumps({
                "scope": "public",
                "grant_type": "client_credentials"
            })
        )

        token = lyft_response.json()['access_token']

        for event in events:
            response = requests.get(
                url="https://api.lyft.com/v1/cost",
                headers={
                    "Authorization": "Bearer {}".format(token)
                },
                params={
                    'start_lat': event.venue.lat,
                    'start_lng': event.venue.long
                }
            )

            for price in response.json()['cost_estimates']:
                if price['ride_type'] != 'lyft':
                    continue
                else:
                    price = LyftPrice(
                        event=event,
                        primetime=(100+int(price['primetime_percentage'][:-1]))/100,
                        time=datetime.now()
                    )
                    session.add(price)
                    session.commit()
                    break

        sleep(180)


if __name__ == '__main__':
    main()
