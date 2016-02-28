from sql import get_session, Event

def main():
    session = get_session()

    events = session.query(Event).filter(Event.end_time == None).limit(50)

    for event in events:
        if event.categories:
            print(event.categories)

if __name__ == '__main__':
    main()
