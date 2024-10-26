
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from apps import db
import math
from typing import List, Tuple, Optional
from sqlalchemy import func, select, case


# New Models


class WantedItem(db.Model):
    __tablename__ = 'WantedItems'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.String(256), nullable=False, index=True)
    item_type = db.Column(db.String(128), nullable=False)
    item_amount = db.Column(db.Integer, nullable=False)
    item_location = db.Column(db.String(256), nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    # Relationship to ItemLinks
    links = relationship('ItemLink', back_populates='wanted_item', cascade="all, delete-orphan")

    def __repr__(self):
        return f"WantedItem(id={self.id}, type={self.item_type}, amount={self.item_amount})"


class DonatedItem(db.Model):
    __tablename__ = 'DonatedItems'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.String(256), nullable=False, index=True)
    item_type = db.Column(db.String(128), nullable=False)
    item_amount = db.Column(db.Integer, nullable=False)
    item_location = db.Column(db.String(256), nullable=False)
    x = db.Column(db.Float, nullable=False)  # X-coordinate
    y = db.Column(db.Float, nullable=False)  # Y-coordinate
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    # Relationship to ItemLinks
    links = relationship('ItemLink', back_populates='donated_item', cascade="all, delete-orphan")

    def __repr__(self):
        return f"DonatedItem(id={self.id}, type={self.item_type}, amount={self.item_amount}, location=({self.x}, {self.y}))"


class ItemLink(db.Model):
    __tablename__ = 'ItemLinks'

    id = db.Column(db.Integer, primary_key=True)
    wanted_item_id = db.Column(db.Integer, ForeignKey('WantedItems.id'), nullable=False)
    donated_item_id = db.Column(db.Integer, ForeignKey('DonatedItems.id'), nullable=False)
    amount_fulfilled = db.Column(db.Integer, nullable=False)

    # Relationships
    wanted_item = relationship('WantedItem', back_populates='links')
    donated_item = relationship('DonatedItem', back_populates='links')

    def __repr__(self):
        return (f"ItemLink(id={self.id}, wanted_item_id={self.wanted_item_id}, "
                f"donated_item_id={self.donated_item_id}, amount_fulfilled={self.amount_fulfilled})")





