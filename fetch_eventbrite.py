import requests
import arrow
from sqlalchemy.exc import IntegrityError
from sql import get_session, Venue, Event, Category
from secrets import EVENTBRITE_PERSONAL_TOKEN

EVENTBRITE_API_URL = 'https://www.eventbriteapi.com/v3'
TOKEN_PARAM = "".join(['token=', EVENTBRITE_PERSONAL_TOKEN])
LOC_ADDRESS_PARAM = 'location.address='
LOCATION_WITHIN_PARAM = 'location.within='
SORT_BY_PARAM = 'sort_by='
POPULAR_PARAM = 'popular='
START_DATE_PARAM = 'start_date.range_start='
END_DATE_PARAM = 'start_date.range_end='
PAGE_PARAM = 'page='
EVENT_SEARCH_ENDPOINT = '/events/search/?'

def request_and_return_res(query_url, term, per_page=50, page_num=0, ttl_page=1):
    while page_num <= ttl_page:
        url = "".join([query_url, "&page=", str(page_num)])
        print ("Sending GET request to ", url)
        res = requests.get(url).json()
        #TODO: handle error
        # if res.get(status_code) >= 400:
        #     raise Error((res.error, res.error_description))
        # print (res)
        ttl_page = res['pagination']["page_count"]
        page_size = res['pagination']['page_size']

        res = res[term]

        # print res
        print (page_num, ttl_page)
        page_num += 1
        yield res
def get_venue_info(evt_id):
    query_url = "".join([EVENTBRITE_API_URL, "/venues/", evt_id, "/?", TOKEN_PARAM])
    res = requests.get(query_url).json()
    return res

def get_category_name(category_id):
    query_url = "".join([EVENTBRITE_API_URL, "/categories/", category_id, "/?", TOKEN_PARAM])
    res = requests.get(query_url).json()
    return res

def search_events_by_location(address, location_within, popular, sort_by, start_date_range_start, start_date_range_end):
    top_url = "".join([EVENTBRITE_API_URL,EVENT_SEARCH_ENDPOINT])
    param_url = "&".join([TOKEN_PARAM, LOC_ADDRESS_PARAM+address, LOCATION_WITHIN_PARAM+location_within, POPULAR_PARAM+popular, SORT_BY_PARAM+sort_by, START_DATE_PARAM+start_date_range_start, END_DATE_PARAM+start_date_range_end])
    query_url = "".join([top_url, param_url])

    session = get_session()
    ttl_events = {}
    #TODO: fix startpage
    for evt in request_and_return_res(query_url, "events"):
        for e in evt:
            try:
                v = get_venue_info(e["venue_id"])
                venue = session.query(Venue).filter(Venue.eventbrite_id==e['venue_id']).first()
                v_name = v['name'].encode("latin-1", "ignore") if v.get('name') else None

                if "address" not in v:
                    continue
                if not venue:
                    venue = Venue(name=v_name,
                                  address='{}, {}, {} {}'.format(v["address"]["address_1"], v["address"]["city"], v["address"]["region"], v["address"]["postal_code"]),
                                  lat=v["address"]["latitude"],
                                  long=v["address"]["longitude"],
                                  capacity=int(e["capacity"]),
                                  eventbrite_id=e['venue_id'])
                    session.add(venue)
                    session.commit()
                    print ("Added Venue:", v_name)
                else:
                    session.query(Venue).filter(Venue.eventbrite_id==e['venue_id']).update({'capacity':int(e["capacity"])})
                    session.commit()
                    print("Updated CAPACITY", v_name, int(e["capacity"]))
            #
                image_url = None
                if "logo" in e:
                    if e["logo"] != None and "url" in e["logo"]:
                        image_url = e["logo"]["url"]
                event = session.query(Event).filter(Event.eventbrite_id==e['id']).first()
                e_name = e["name"]["text"].encode("latin-1", "ignore") if e.get("name").get("text") else None

                if not event:
                    event = Event(name=e_name,
                                  start_time=e["start"]["local"].replace("T", " "),
                                  end_time=e["end"]["local"].replace("T", " "),
                                  eventbrite_id=e['id'],
                                  image_url=image_url,
                                  venue=venue)
                    session.add(event)
                    session.commit()
                    print ("Added Event:", e_name)
                else:
                    print ("Skipped:", e_name)

                if e["category_id"]:
                    c = get_category_name(e["category_id"])
                    if not c.get("name"):
                        continue
                    else:
                        cat_name = c["name"].encode("latin-1", "ignore")

                    category = session.query(Category).filter(Category.type==cat_name).first()
                    if not category:
                        category = Category(type=cat_name, name=cat_name)
                        session.add(category)
                        event.categories.append(category)
                        session.commit()
                        print ("Added Category:", cat_name)
                    else:
                        print ("Skipped:", cat_name)
                print('----------------------')

            except UnicodeEncodeError:
                session.rollback()
                print("FAILED")
                # print("FAILED: {} @ {}".format(e["name"]["text"], v['name']))
                continue
            except IntegrityError:
                session.rollback()
                print("DUPLICATE")
                # print("DUPLICATE: {} @ {}".formate(e["name"]["text"], v['name']))
                continue


if __name__ == "__main__":
    # session = get_session()
    time_start = "".join([arrow.utcnow().format('YYYY-MM-DDTHH:mm:ss'),"Z"])
    time_end = "".join([arrow.utcnow().replace(days=+7).format('YYYY-MM-DDTHH:mm:ss'),"Z"])
    search_events_by_location(address="San+Francisco", location_within="70mi", popular="true", sort_by="date", start_date_range_start=time_start, start_date_range_end=time_end)
    print (time_start, time_end)

    # search_events_by_location()
