import os
import random
import math
from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from apps.config import Config  # Importing your Config class

# Define the base class
Base = declarative_base()

# Define the models
class WantedItem(Base):
    __tablename__ = 'WantedItems'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(256), nullable=False, index=True)
    item_type = Column(String(128), nullable=False)
    item_amount = Column(Integer, nullable=False)
    item_location = Column(String(256), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)

    # Relationship to ItemLinks
    links = relationship('ItemLink', back_populates='wanted_item', cascade="all, delete-orphan")

    def __repr__(self):
        return f"WantedItem(id={self.id}, type={self.item_type}, amount={self.item_amount})"

class DonatedItem(Base):
    __tablename__ = 'DonatedItems'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(256), nullable=False, index=True)
    item_type = Column(String(128), nullable=False)
    item_amount = Column(Integer, nullable=False)
    item_location = Column(String(256), nullable=False)
    x = Column(Float, nullable=False)  # X-coordinate
    y = Column(Float, nullable=False)  # Y-coordinate
    is_available = Column(Boolean, default=True, nullable=False)

    # Relationship to ItemLinks
    links = relationship('ItemLink', back_populates='donated_item', cascade="all, delete-orphan")

    def __repr__(self):
        return f"DonatedItem(id={self.id}, type={self.item_type}, amount={self.item_amount}, location=({self.x}, {self.y}))"

class ItemLink(Base):
    __tablename__ = 'ItemLinks'

    id = Column(Integer, primary_key=True)
    wanted_item_id = Column(Integer, ForeignKey('WantedItems.id'), nullable=False)
    donated_item_id = Column(Integer, ForeignKey('DonatedItems.id'), nullable=False)
    amount_fulfilled = Column(Integer, nullable=False)

    # Relationships
    wanted_item = relationship('WantedItem', back_populates='links')
    donated_item = relationship('DonatedItem', back_populates='links')

    def __repr__(self):
        return (f"ItemLink(id={self.id}, wanted_item_id={self.wanted_item_id}, "
                f"donated_item_id={self.donated_item_id}, amount_fulfilled={self.amount_fulfilled})")

# Import the database configuration from Config
DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

# Set up the database engine and session
try:
    engine = create_engine(DATABASE_URL, echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
except OperationalError as e:
    print(f"Database connection failed: {e}")
    exit(1)

# Create all tables
Base.metadata.create_all(engine)

# Define item types
item_types = [
    "Electric Generators",
    "First aid supplies",
    "Canned Food",
    "Water",
    "First aid supplies",
    "Canned Food",
    "Water",
    "First aid supplies",
    "Canned Food",
    "Water",
    "First aid supplies",
    "Canned Food",
    "Water",
    "Canned Food",
    "Water",
    "Canned Food",
    "Water",
    "Water",
    "Water",
    "Flashlights",
    "Blankets",
    "Batteries",
    "Cellular phone (w/ emergency numbers)",
    "Emergency light",
    "Buckets",
    "Life jacket",
    "Wet-Dry Vacuums",
    "Towels",
    "Trauma kits",
    "Disposable Gloves",
]

# Define base coordinates
base_coords = [
    (28.117526244224052, -82.50558252267152),
    (28.906719670851867, -82.46163720942181),
    (28.156278243698722, -82.50283594059343),
    (27.97935847435082, -81.95077294289383),
    (28.460959200218806, -81.43441551220967),
    (28.68046227063652, -81.46188133299074),
    (28.586445606069518, -81.17898337894569),
    (26.575749017721503, -81.60470361318838),
    (27.19307719773749, -81.85464259012126),
    (27.361517078262914, -82.43691799068002),
    (28.004010596460553, -81.95008408587385),
    (28.008041930110448, -81.6510993294297),
    (26.74678310154569, -81.41208223132303),
]

# Function to generate random points around a coordinate
def random_point_around(lat, lon, radius_km):
    """
    Generate a random point around a given location within a certain radius in kilometers.
    """
    # Earth radius in km
    R = 6378.1

    # Convert radius from kilometers to degrees
    radius_deg = radius_km / 111  # Approximate conversion

    u = random.random()
    v = random.random()

    w = radius_deg * math.sqrt(u)
    t = 2 * math.pi * v

    x_offset = w * math.cos(t)
    y_offset = w * math.sin(t)

    new_lat = lat + x_offset
    new_lon = lon + y_offset

    return new_lat, new_lon

# Generate user IDs
user_ids = [f'user_{i}' for i in range(1, 21)]

donated_items = []
wanted_items = []

try:
    for lat, lon in base_coords:
        # Generate 5 DonatedItems
        for _ in range(8):
            # Randomly pick a user_id
            user_id = random.choice(user_ids)
            # Randomly pick an item type
            item_type = random.choice(item_types)
            # Randomly decide the amount
            item_amount = random.randint(1, 10)
            # Generate random point around base coordinate
            x, y = random_point_around(lat, lon, radius_km=5)
            # Create DonatedItem
            donated_item = DonatedItem(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                item_type=item_type,
                item_amount=item_amount,
                item_location="Random Location",
                x=x,
                y=y,
                is_available=True,
            )
            donated_items.append(donated_item)
            session.add(donated_item)

        # Generate 5 WantedItems
        for _ in range(30):
            # Randomly pick a user_id
            user_id = random.choice(user_ids)
            # Randomly pick an item type
            item_type = random.choice(item_types)
            # Randomly decide the amount
            item_amount = random.randint(1, 10)
            x, y = random_point_around(lat, lon, radius_km=10)
            # Create WantedItem
            wanted_item = WantedItem(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                item_type=item_type,
                item_amount=item_amount,
                item_location=str(x)+","+str(y),
                is_available=True,
            )
            wanted_items.append(wanted_item)
            session.add(wanted_item)

    session.commit()

    # Create ItemLinks between matching items
    item_links = []

    for wanted_item in wanted_items:
        # Find DonatedItems with matching item_type and is_available
        matching_donated_items = [d for d in donated_items if d.item_type == wanted_item.item_type and d.is_available]

        if matching_donated_items:
            # For simplicity, pick the first matching DonatedItem
            donated_item = matching_donated_items[0]
            # Determine the amount to fulfill
            amount_fulfilled = min(wanted_item.item_amount, donated_item.item_amount)
            # Create ItemLink
            item_link = ItemLink(
                wanted_item_id=wanted_item.id,
                donated_item_id=donated_item.id,
                amount_fulfilled=amount_fulfilled
            )
            item_links.append(item_link)
            session.add(item_link)
            # Update the item amounts
            wanted_item.item_amount -= amount_fulfilled
            donated_item.item_amount -= amount_fulfilled
            if wanted_item.item_amount == 0:
                wanted_item.is_available = False
            if donated_item.item_amount == 0:
                donated_item.is_available = False

    session.commit()

    print("Data successfully inserted into the database.")

except Exception as e:
    session.rollback()
    print(f"An error occurred: {e}")
