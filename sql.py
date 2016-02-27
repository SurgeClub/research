from sqlalchemy import create_engine, Table, Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import Integer, String, Numeric, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

from secrets import DB_CONNECTION

Base = declarative_base()
engine = create_engine(DB_CONNECTION)
Session = sessionmaker(bind=engine)

class Venue(Base):
    __tablename__ = 'venues'
    __table_args__ = (
        UniqueConstraint('name', 'zip_code', name='name_location_uc'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(255), nullable=False)
    zip_code = Column(String(255), nullable=False)
    lat = Column(Numeric(precision=7, scale=4), nullable=False)
    long = Column(Numeric(precision=7, scale=4), nullable=False)
    description = Column(Text)
    capacity = Column(Integer)
    eventful_id = Column(String(255))
    songkick_id = Column(String(255))
    image_url = Column(String(255))
    events = relationship('Event', back_populates='venue')

    def __repr__(self):
        return "{} @ {}".format(self.name, self.address)

association_table = Table('event_categories', Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class Event(Base):
    __tablename__ = 'events'
    __table_args__ = (
        UniqueConstraint('name', 'venue_id', name='name_venue_uc'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime)
    est_end_time = Column(DateTime)
    eventful_popularity = Column(Integer)
    songkick_popularity = Column(Numeric(precision=7, scale=6))
    eventful_id = Column(String(255))
    songkick_id = Column(String(255))
    tickets_sold = Column(Integer)
    description = Column(Text)
    image_url = Column(String(255))
    venue_id = Column(Integer, ForeignKey('venues.id'))
    venue = relationship('Venue', back_populates='events', uselist=False)
    categories = relationship('Category', secondary=association_table, back_populates='events')

    def __repr__(self):
        return "{} @ {}".format(self.name, self.venue.name)

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    type = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    events = relationship('Event', secondary=association_table, back_populates='categories')

    def __repr__(self):
        return "{}: {}".format(self.type, self.name)

def main():
    Base.metadata.create_all(engine)

def get_session():
    return Session()

if __name__ == '__main__':
    main()
