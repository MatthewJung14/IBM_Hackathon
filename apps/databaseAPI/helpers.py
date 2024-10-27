
from typing import List, Tuple, Optional, re
from sqlalchemy import func
from sqlalchemy.orm import Session

from apps import db
from apps.databaseAPI.models import WantedItem, DonatedItem, ItemLink


def haversine_distance_sql(lon1, lat1, lon2, lat2):
    """
    Returns the Haversine distance between two points in miles using SQLAlchemy functions.

    :param lon1: Longitude of the first point.
    :param lat1: Latitude of the first point.
    :param lon2: Longitude of the second point.
    :param lat2: Latitude of the second point.
    :return: SQLAlchemy expression representing the Haversine distance in miles.
    """
    # Earth's radius in miles
    R = 3959

    # Convert decimal degrees to radians
    lon1_rad = func.radians(lon1)
    lat1_rad = func.radians(lat1)
    lon2_rad = func.radians(lon2)
    lat2_rad = func.radians(lat2)

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = func.pow(func.sin(dlat / 2), 2) + func.cos(lat1_rad) * func.cos(lat2_rad) * func.pow(func.sin(dlon / 2), 2)
    c = 2 * func.asin(func.sqrt(a))

    distance = R * c
    return distance



def list_available_items(
    item_types: List[str],
    x: Optional[float] = None,
    y: Optional[float] = None,
    distance: Optional[float] = None
) -> Tuple[List[Tuple[str, int, List[Tuple[int, str]]]], List[Tuple[str, int, List[Tuple[int, str]]]]]:
    """
    Lists available Wanted and Donated items based on item types and optional location filtering.

    :param item_types: List of item type strings to filter.
    :param x: Optional X-coordinate for location filtering (only applies to DonatedItems).
    :param y: Optional Y-coordinate for location filtering (only applies to DonatedItems).
    :param distance: Optional radius distance to include items within (only applies to DonatedItems).
    :return: Tuple containing two lists:
             - List of tuples for WantedItems (item_type, total_available_amount, [(available_amount, item_id)])
             - List of tuples for DonatedItems (item_type, total_available_amount, [(available_amount, item_id)])
    """
    # Subquery to calculate total fulfilled for WantedItems
    fulfilled_wanted_subq = (
        db.session.query(
            ItemLink.wanted_item_id,
            func.coalesce(func.sum(ItemLink.amount_fulfilled), 0).label('total_fulfilled')
        )
        .filter(ItemLink.wanted_item_id == WantedItem.id)
        .group_by(ItemLink.wanted_item_id)
        .subquery()
    )

    # Subquery to calculate total fulfilled for DonatedItems
    fulfilled_donated_subq = (
        db.session.query(
            ItemLink.donated_item_id,
            func.coalesce(func.sum(ItemLink.amount_fulfilled), 0).label('total_fulfilled')
        )
        .filter(ItemLink.donated_item_id == DonatedItem.id)
        .group_by(ItemLink.donated_item_id)
        .subquery()
    )

    # Query for WantedItems with available_amount = item_amount - total_fulfilled
    wanted_query = (
        db.session.query(
            WantedItem.item_type,
            WantedItem.id,
            (WantedItem.item_amount - func.coalesce(fulfilled_wanted_subq.c.total_fulfilled, 0)).label('available_amount')
        )
        .outerjoin(fulfilled_wanted_subq, WantedItem.id == fulfilled_wanted_subq.c.wanted_item_id)
        .filter(
            WantedItem.item_type.in_(item_types),
            WantedItem.is_available == True
        )
    )

    # Aggregate available amounts for WantedItems
    wanted_items = (
        db.session.query(
            WantedItem.item_type,
            func.sum(WantedItem.item_amount - func.coalesce(fulfilled_wanted_subq.c.total_fulfilled, 0)).label('total_available')
        )
        .outerjoin(fulfilled_wanted_subq, WantedItem.id == fulfilled_wanted_subq.c.wanted_item_id)
        .filter(
            WantedItem.item_type.in_(item_types),
            WantedItem.is_available == True
        )
        .group_by(WantedItem.item_type)
        .all()
    )

    # Query for WantedItems with item information
    wanted_items_info = (
        wanted_query
        .all()
    )

    # Base query for DonatedItems
    donated_query = (
        db.session.query(
            DonatedItem.item_type,
            DonatedItem.id,
            (DonatedItem.item_amount - func.coalesce(fulfilled_donated_subq.c.total_fulfilled, 0)).label('available_amount')
        )
        .outerjoin(fulfilled_donated_subq, DonatedItem.id == fulfilled_donated_subq.c.donated_item_id)
        .filter(
            DonatedItem.item_type.in_(item_types),
            DonatedItem.is_available == True
        )
    )

    # If location filtering is applied (only for DonatedItems)
    if x is not None and y is not None and distance is not None:
        donated_query = donated_query.filter(
            func.sqrt(
                func.pow(DonatedItem.x - x, 2) + func.pow(DonatedItem.y - y, 2)
            ) <= distance
        )

    # Aggregate available amounts for DonatedItems
    donated_items = (
        db.session.query(
            DonatedItem.item_type,
            func.sum(DonatedItem.item_amount - func.coalesce(fulfilled_donated_subq.c.total_fulfilled, 0)).label('total_available')
        )
        .outerjoin(fulfilled_donated_subq, DonatedItem.id == fulfilled_donated_subq.c.donated_item_id)
        .filter(
            DonatedItem.item_type.in_(item_types),
            DonatedItem.is_available == True
        )
    )

    if x is not None and y is not None and distance is not None:
        donated_items = donated_items.filter(
            func.sqrt(
                func.pow(DonatedItem.x - x, 2) + func.pow(DonatedItem.y - y, 2)
            ) <= distance
        )

    donated_items = (
        donated_items
        .group_by(DonatedItem.item_type)
        .all()
    )

    # Query for DonatedItems with item information
    donated_items_info = (
        donated_query
        .all()
    )

    # Convert results to dictionaries for easy lookup
    wanted_dict = {item_type: total for item_type, total in wanted_items}
    donated_dict = {item_type: total for item_type, total in donated_items}

    # Prepare the result lists
    wanted_result = []
    donated_result = []

    for item_type in item_types:
        wanted_amount = wanted_dict.get(item_type, 0)
        donated_amount = donated_dict.get(item_type, 0)

        wanted_items_info_list = [
            (available_amount, item_id)
            for item_type_, item_id, available_amount in wanted_items_info
            if item_type_ == item_type and available_amount > 0
        ]

        donated_items_info_list = [
            (available_amount, item_id)
            for item_type_, item_id, available_amount in donated_items_info
            if item_type_ == item_type and available_amount > 0
        ]

        wanted_result.append((item_type, wanted_amount, wanted_items_info_list))
        donated_result.append((item_type, donated_amount, donated_items_info_list))

    return wanted_result, donated_result


def find_closest_items(
        item_type: str,
        amount: int,
        x: float,  # Longitude of desired location
        y: float,  # Latitude of desired location
        max_distance: float
) -> List[Tuple[int, float, float, str, int]]:
    """
    Finds the closest available donated items to fulfill a wanted item request using the Haversine distance.

    :param item_type: The type of the item to find.
    :param amount: The total amount needed.
    :param x: Longitude of the desired location.
    :param y: Latitude of the desired location.
    :param max_distance: Maximum distance to search for items (in miles).
    :return: List of tuples, each containing:
             (donated_item_id, donated_x, donated_y, item_location, allocated_amount)
    """
    session: Session = db.session

    # Subquery to calculate total fulfilled for DonatedItems
    fulfilled_donated_subq = (
        session.query(
            ItemLink.donated_item_id,
            func.coalesce(func.sum(ItemLink.amount_fulfilled), 0).label('total_fulfilled')
        )
        .group_by(ItemLink.donated_item_id)
        .subquery()
    )

    # Calculate Haversine distance and filter donated items within max_distance
    distance_expr = haversine_distance_sql(DonatedItem.x, DonatedItem.y, x, y)

    # Query to get available donated items with calculated available_amount and distance
    available_donated = (
        session.query(
            DonatedItem.id,
            DonatedItem.x,
            DonatedItem.y,
            DonatedItem.item_location,  # Include the location name
            (DonatedItem.item_amount - func.coalesce(fulfilled_donated_subq.c.total_fulfilled, 0)).label(
                'available_amount'),
            distance_expr.label('distance')
        )
        .outerjoin(fulfilled_donated_subq, DonatedItem.id == fulfilled_donated_subq.c.donated_item_id)
        .filter(
            DonatedItem.item_type == item_type,
            DonatedItem.is_available == True,
            distance_expr <= max_distance,
            (DonatedItem.item_amount - func.coalesce(fulfilled_donated_subq.c.total_fulfilled, 0)) > 0
        )
        .order_by('distance')
    )

    donated_items = available_donated.all()

    result = []
    total_collected = 0

    for item in donated_items:
        if total_collected >= amount:
            break
        available = item.available_amount
        if available <= 0:
            continue

        needed = amount - total_collected
        allocated = min(available, needed)

        # Append item_location to the tuple
        result.append((item.id, item.x, item.y, item.item_location, allocated))
        total_collected += allocated

    return result



def donateListofItems(
    user_id: str,
    x: float,
    y: float,
    item_location: str,
    items: List[Tuple[str, int]]
) -> List[DonatedItem]:
    """
    Adds a list of donated items to the DonatedItems table.

    :param user_id: Unique identifier for the user donating the items.
    :param x: X-coordinate of the donation location.
    :param y: Y-coordinate of the donation location.
    :param item_location: General location description of the donation.
    :param items: List of tuples containing (item_type, item_amount).
    :return: List of DonatedItem instances added to the database.
    """
    donated_items = []
    for item_type, item_amount in items:
        if item_amount <= 0:
            continue  # Skip invalid amounts
        donated_item = DonatedItem(
            user_id=user_id,
            x=x,
            y=y,
            item_location=item_location,
            item_type=item_type,
            item_amount=item_amount
        )
        donated_items.append(donated_item)

    if donated_items:
        db.session.add_all(donated_items)
        db.session.commit()

    return donated_items


def wantListofItems(
    user_id: str,
    item_location: str,
    items: List[Tuple[str, int]]
) -> List[WantedItem]:
    """
    Adds a list of wanted items to the WantedItems table.

    :param user_id: Unique identifier for the user requesting the items.
    :param item_location: General location description where items are needed.
    :param items: List of tuples containing (item_type, item_amount).
    :return: List of WantedItem instances added to the database.
    """
    wanted_items = []
    for item_type, item_amount in items:
        if item_amount <= 0:
            continue  # Skip invalid amounts
        wanted_item = WantedItem(
            user_id=user_id,
            item_location=item_location,
            item_type=item_type,
            item_amount=item_amount
        )
        wanted_items.append(wanted_item)

    if wanted_items:
        db.session.add_all(wanted_items)
        db.session.commit()

    return wanted_items


def get_unfulfilled_wanted_items(user_id: str) -> List[WantedItem]:
    """
    Retrieves unfulfilled wanted items for a specific user.

    :param user_id: Unique identifier for the user.
    :return: List of WantedItem instances that are not fully fulfilled.
    """
    # Subquery to calculate total fulfilled amounts per WantedItem
    fulfilled_subq = (
        db.session.query(
            ItemLink.wanted_item_id,
            func.coalesce(func.sum(ItemLink.amount_fulfilled), 0).label('total_fulfilled')
        )
        .group_by(ItemLink.wanted_item_id)
        .subquery()
    )

    # Query to get WantedItems where item_amount > total_fulfilled
    unfulfilled_items = (
        db.session.query(WantedItem)
        .outerjoin(fulfilled_subq, WantedItem.id == fulfilled_subq.c.wanted_item_id)
        .filter(
            WantedItem.user_id == user_id,
            WantedItem.is_available == True,
            (WantedItem.item_amount - func.coalesce(fulfilled_subq.c.total_fulfilled, 0)) > 0
        )
        .all()
    )

    return unfulfilled_items


def get_uncompleted_donated_items(user_id: str) -> List[DonatedItem]:
    """
    Retrieves undelivered donated items for a specific user.

    :param user_id: Unique identifier for the user.
    :return: List of DonatedItem instances that are not fully allocated.
    """
    # Subquery to calculate total fulfilled amounts per DonatedItem
    fulfilled_subq = (
        db.session.query(
            ItemLink.donated_item_id,
            func.coalesce(func.sum(ItemLink.amount_fulfilled), 0).label('total_fulfilled')
        )
        .group_by(ItemLink.donated_item_id)
        .subquery()
    )

    # Query to get DonatedItems where item_amount > total_fulfilled
    uncompleted_items = (
        db.session.query(DonatedItem)
        .outerjoin(fulfilled_subq, DonatedItem.id == fulfilled_subq.c.donated_item_id)
        .filter(
            DonatedItem.user_id == user_id,
            DonatedItem.is_available == True,
            (DonatedItem.item_amount - func.coalesce(fulfilled_subq.c.total_fulfilled, 0)) > 0
        )
        .all()
    )

    return uncompleted_items


def complete_request(
    wanted_item_id: int,
    allocations: List[Tuple[int, int]]
) -> List[ItemLink]:
    """
    Allocates donated items to fulfill a wanted item request by creating ItemLink entries.

    :param wanted_item_id: The ID of the wanted item to fulfill.
    :param allocations: A list of tuples, each containing (donated_item_id, amount).
    :return: A list of created ItemLink instances.
    :raises ValueError: If validation fails.
    """
    session: Session = db.session

    # Fetch the wanted item
    wanted_item = session.query(WantedItem).filter_by(id=wanted_item_id, is_available=True).first()
    if not wanted_item:
        raise ValueError(f"WantedItem with id {wanted_item_id} does not exist or is not available.")

    # Calculate the currently fulfilled amount for the wanted item
    fulfilled_amount = session.query(func.coalesce(func.sum(ItemLink.amount_fulfilled), 0)) \
                              .filter_by(wanted_item_id=wanted_item_id).scalar()
    available_wanted_amount = wanted_item.item_amount - fulfilled_amount
    if available_wanted_amount <= 0:
        raise ValueError(f"WantedItem with id {wanted_item_id} is already fully fulfilled.")

    total_allocation = sum(amount for _, amount in allocations)
    if total_allocation > available_wanted_amount:
        raise ValueError(f"Total allocation amount ({total_allocation}) exceeds available wanted amount ({available_wanted_amount}).")

    created_links = []

    try:
        with session.begin_nested():  # Start a transaction
            for donated_item_id, amount in allocations:
                if amount <= 0:
                    raise ValueError(f"Allocation amount must be positive. Received: {amount} for DonatedItem ID: {donated_item_id}")

                # Fetch the donated item
                donated_item = session.query(DonatedItem).filter_by(id=donated_item_id, is_available=True).first()
                if not donated_item:
                    raise ValueError(f"DonatedItem with id {donated_item_id} does not exist or is not available.")

                # Calculate the available amount for the donated item
                fulfilled_donated_amount = session.query(func.coalesce(func.sum(ItemLink.amount_fulfilled), 0)) \
                                                 .filter_by(donated_item_id=donated_item_id).scalar()
                available_donated_amount = donated_item.item_amount - fulfilled_donated_amount
                if available_donated_amount <= 0:
                    raise ValueError(f"DonatedItem with id {donated_item_id} has no available amount.")

                if amount > available_donated_amount:
                    raise ValueError(f"Requested allocation amount ({amount}) exceeds available donated amount ({available_donated_amount}) for DonatedItem ID: {donated_item_id}.")

                # Create the ItemLink
                item_link = ItemLink(
                    wanted_item_id=wanted_item_id,
                    donated_item_id=donated_item_id,
                    amount_fulfilled=amount
                )
                session.add(item_link)
                created_links.append(item_link)

        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    return created_links


def get_data_lists():
    """
    Retrieves lists of donated items, wanted items, and item links with coordinate pairs.
    """
    session: Session = db.session
    try:
        # Get all DonatedItems
        donated_items = session.query(DonatedItem).all()
        donated_items_data = [
            {
                "item_type": item.item_type,
                "x": item.x,
                "y": item.y,
                "item_amount": item.item_amount
            }
            for item in donated_items
        ]

        # Get all WantedItems
        wanted_items = session.query(WantedItem).all()
        wanted_items_data = []
        for item in wanted_items:
            # Parse x and y from item_location
            try:
                # Use regex to extract numbers from item_location
                coords = item.item_location.split(",")

                if len(coords) >= 2:
                    x = float(coords[0])
                    y = float(coords[1])
                else:
                    x = 28.105275395664243
                    y = -82.37907792923211
            except Exception:
                x = None
                y = None
            wanted_items_data.append({
                "item_type": item.item_type,
                "x": x,
                "y": y,
                "item_amount": item.item_amount
            })

        # Get all ItemLinks and extract coordinate pairs
        item_links = session.query(ItemLink).all()
        item_links_data = []
        for link in item_links:
            donated_item = link.donated_item
            wanted_item = link.wanted_item
            xd = donated_item.x
            yd = donated_item.y
            # For wanted_item, parse x and y from item_location
            try:
                # Use regex to extract numbers from item_location
                coords = wanted_item.item_location.split(",")

                if len(coords) >= 2:
                    xw = float(coords[0])
                    yw = float(coords[1])
                else:
                    xw = 28.105275395664243
                    yw = -82.37907792923211
            except Exception:
                xw = None
                yw = None
            item_links_data.append({
                "xd": xd,
                "yd": yd,
                "xw": xw,
                "yw": yw
            })

        return donated_items_data, wanted_items_data, item_links_data

    except Exception as e:
        raise e