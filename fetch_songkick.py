import requests
import json
import pyrebase
from secrets import SONGKICK_API_KEY, SONGKICK_API_URL, SF_BAY_METRO_ID, FIREBASE_URL, FIREBASE_API_KEY
from sqlalchemy.exc import IntegrityError
from sql import get_session, Venue, Event, Category
from secrets import EVENTFUL_KEY
ref = pyrebase.Firebase(FIREBASE_URL, FIREBASE_API_KEY)
# def fetch_to_firebase(payload, directory):
#     ref.child(directory).update(payload)
#     print ("Sent", len(payload), "to Firebase")
#     # save memory
#     del payload

# def sort_event_dict_by_date_and_popularity(events, POPULARITY_LIMIT=0.01):
#     sorted_event_list = []
#     for e in sorted(events, key=lambda x: (events[x]["startTime"], -events[x]["songkickPopularity"])):
#         # print (events[e]["startTime"], events[e]["songkickPopularity"])
#         if events[e]["songkickPopularity"] > POPULARITY_LIMIT:
#             sorted_event_list.append({e: events[e]})
#
#     with open("evt_output.txt", "w+", encoding='utf-8') as a_file:
#         a_file.write("%s" % str(sorted_event_list))
#     print ("length of events", len(sorted_event_list))
#     return sorted_event_list

# def search_venues_by_keywords(search_query="SF+Bay+Area"):
#     venue_url = "".join([SONGKICK_API_URL, "/search/venues.json?", "query=", search_query, "&apikey=", SONGKICK_API_KEY])
#     venues = {}
#     cnt = 0
#     for res in request_and_return_res(venue_url, "venue"):
#         for idx, ven in enumerate(res):
#             if ("capacity" in ven and ven["capacity"]) or ("street" in ven and ven["street"]):
#                 venue_id = "".join(["sc-ven-", str(ven["id"])])
#                 venues[venue_id] = {}
#                 venues[venue_id]["id"] = ven["id"]
#                 venues[venue_id]["name"] = ven["displayName"]
#                 venues[venue_id]["capacity"] = ven["capacity"]
#                 venues[venue_id]["lat"] = ven["lat"]
#                 venues[venue_id]["lng"] = ven["lng"]
#                 venues[venue_id]["description"] = ven["description"]
#                 venues[venue_id]["zip"] = ven["zip"]
#                 if "street" not in ven or not ven["street"]:
#                     venues[venue_id]["address"] = "".join([ven["city"]["displayName"], ", ", ven["city"]["state"]["displayName"]])
#                 else:
#                     venues[venue_id]["address"] = "".join([ven["street"], ", ", ven["city"]["displayName"], ", ", ven["city"]["state"]["displayName"], " ", ven["zip"]])
#             # print (venues[venue_id])
#
#     fetch_to_firebase(venues, "venues")

def request_and_return_res(query_url, term, per_page=50, page_num=0, ttl_page=1):
    while page_num < ttl_page:
        url = "".join([query_url, "&page=", str(page_num)])

        res = requests.get(url).json()
        res = res["resultsPage"]
        # TODO: handle error
        if res['status'] != "ok":
            raise Exception({"status": "error", "msg": res['status']})
        ttl_entries = int(res["totalEntries"])
        ttl_page = ttl_entries // per_page
        res = res["results"][term]
        # print res
        print (page_num, ttl_page)
        page_num += 1
        yield res

def search_metro_area_upcoming_event(search_query="San+Francisco", metro_area_id=SF_BAY_METRO_ID, api_key=SONGKICK_API_KEY):
    # metro_url = "".join([SONGKICK_API_URL, "/metro_areas/"])
    session = get_session()
    calendar_url = "/calendar.json?"
    query_url = "".join([SONGKICK_API_URL, "/metro_areas/", SF_BAY_METRO_ID, calendar_url, "apikey=", api_key])
    print (query_url)
    cnt = 0
    for res in request_and_return_res(query_url, "event", page_num=3):
        # if cnt < 1:
        for idx, evt in enumerate(res):
            try:
                address = ref.child("venues").child('sc-ven-'+str(evt["venue"]["id"])).child('address').get().val()

                if evt.get("start"):
                    if not evt.get("start").get("time"):
                        continue
                    start_time = evt["start"]["date"] + " " + evt["start"]["time"]
                else:
                    start_time = None

                if evt.get("end"):
                    if not evt.get("end").get("time"):
                        continue
                    end_time = evt["end"]["date"] + " " + evt["end"]["time"]
                else:
                    end_time = None
                capacity = ref.child("venues").child('sc-ven-'+str(evt["venue"]["id"])).child('capacity').get().val()

                venue = session.query(Venue).filter(Venue.songkick_id==evt["venue"]["id"]).first()
                if not venue:
                    venue = Venue(name=evt["venue"]["displayName"],
                                  address=address,
                                  lat=evt["location"]["lat"],
                                  long=evt["location"]["lng"],
                                  songkick_id=evt["venue"]["id"])
                    session.add(venue)
                    session.commit()
                    print("Added VENUE:", evt["venue"]["displayName"])
                else:
                     session.query(Venue).filter(Venue.songkick_id==evt["venue"]["id"]).update({'capacity':capacity})
                     print("Added CAPACITY", evt["venue"]["displayName"], capacity)

                event = session.query(Event).filter(Event.songkick_id==evt["id"]).first()
                if not event:
                    event = Event(name=evt["displayName"],
                                  start_time=start_time,
                                  end_time=end_time,
                                  songkick_popularity=evt["popularity"],
                                  songkick_id=evt["id"],
                                  venue=venue)
                    session.add(event)
                    session.commit()
                    print("Added VENUE:", evt["displayName"])

                category = session.query(Category).filter(Category.type==evt["type"]).first()
                if not category:
                    category = Category(type=evt["type"], name=evt["type"])
                    session.add(category)
                    print("Added CATEGORY:", evt["type"])
                event.categories.append(category)
                session.commit()

            except UnicodeEncodeError:
                session.rollback()
                print("FAILED")
                # print("FAILED: {} @ {}".format(e['title'], e['venue_name']))
                continue

            except IntegrityError:
                session.rollback()
                session.query(Event).filter(Event.songkick_id==evt["id"]).update({'name':evt["displayName"]})
                session.commit()
                print("DUPLICATE")
                # print("DUPLICATE: {} @ {}".format(e['title'], e['venue_name']))
                continue

            # print (events[evt_id])
        # else:
        #     break
        # cnt += 1

    # send to fire base
    # fetch_to_firebase(events, "events")

if __name__ == "__main__":
    # requests
    search_metro_area_upcoming_event()
    # search_venues_by_keywords()
    #practice()
