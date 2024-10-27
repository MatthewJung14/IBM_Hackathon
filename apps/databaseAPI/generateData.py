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
    x = Column(Float, nullable=False)  # X-coordinate (latitude)
    y = Column(Float, nullable=False)  # Y-coordinate (longitude)
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
    engine = create_engine(DATABASE_URL, echo=False)  # Set echo=False to reduce output
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

# Function to calculate distance in degrees between two points
def distance_in_degrees(lat1, lon1, lat2, lon2):
    delta_lat = lat1 - lat2
    delta_lon = lon1 - lon2
    return math.sqrt(delta_lat**2 + delta_lon**2)

# Generate user IDs
user_ids = [f'user_{i}' for i in range(1, 21)]

donated_items = []
wanted_items = []

try:
    # Generate DonatedItems and WantedItems
    for lat, lon in base_coords:
        # Generate DonatedItems
        for _ in range(7):
            # Randomly pick a user_id
            user_id = random.choice(user_ids)
            # Randomly pick an item type
            item_type = random.choice(item_types)
            # Randomly decide the amount
            item_amount = random.randint(1, 50)
            # Generate random point around base coordinate
            x, y = random_point_around(lat, lon, radius_km=7)
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

        # Generate WantedItems
        for _ in range(50):
            # Randomly pick a user_id
            user_id = random.choice(user_ids)
            # Randomly pick an item type
            item_type = random.choice(item_types)
            # Randomly decide the amount
            item_amount = random.randint(1, 10)
            x, y = random_point_around(lat, lon, radius_km=15)
            # Create WantedItem
            wanted_item = WantedItem(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                item_type=item_type,
                item_amount=item_amount,
                item_location=f"{x},{y}",
                is_available=True,
            )
            wanted_items.append(wanted_item)
            session.add(wanted_item)

    # Commit to save DonatedItems and WantedItems and assign IDs
    session.commit()

    # Now proceed to create ItemLinks between matching items
    item_links = []

    # Initialize amount_remaining for each DonatedItem
    for donated_item in donated_items:
        donated_item.amount_remaining = donated_item.item_amount

    for wanted_item in wanted_items:
        # Initialize amount_remaining for wanted_item
        wanted_amount_remaining = wanted_item.item_amount
        # Extract wanted_item's latitude and longitude
        wanted_lat_str, wanted_lon_str = wanted_item.item_location.split(',')
        wanted_lat = float(wanted_lat_str)
        wanted_lon = float(wanted_lon_str)
        # While the wanted item still needs fulfillment
        while wanted_amount_remaining > 0 and wanted_item.is_available:
            # Find DonatedItems with matching item_type, is_available, amount_remaining > 0, and within 0.8 degrees
            matching_donated_items = [
                d for d in donated_items
                if d.item_type == wanted_item.item_type and d.is_available and d.amount_remaining > 0
                and distance_in_degrees(wanted_lat, wanted_lon, d.x, d.y) <= 0.5
            ]

            if not matching_donated_items:
                # No more matching donated items available
                break

            # For simplicity, pick the first matching DonatedItem
            donated_item = matching_donated_items[0]

            # Determine the amount to fulfill
            amount_fulfilled = min(wanted_amount_remaining, donated_item.amount_remaining)
            # Create ItemLink
            item_link = ItemLink(
                wanted_item_id=wanted_item.id,
                donated_item_id=donated_item.id,
                amount_fulfilled=amount_fulfilled
            )
            item_links.append(item_link)
            session.add(item_link)
            session.flush()  # Flush to update relationships

            # Update amount_remaining
            wanted_amount_remaining -= amount_fulfilled
            donated_item.amount_remaining -= amount_fulfilled

            # Update is_available flags based on amount_remaining
            if wanted_amount_remaining == 0:
                wanted_item.is_available = False
            if donated_item.amount_remaining == 0:
                donated_item.is_available = False

    session.commit()

    print("Data successfully inserted into the database.")

except Exception as e:
    session.rollback()
    print(f"An error occurred: {e}")
