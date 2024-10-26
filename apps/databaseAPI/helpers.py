
from typing import List, Tuple, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from apps import db
from apps.databaseAPI.models import WantedItem, DonatedItem, ItemLink

def list_available_items(
    item_types: List[str],
    x: Optional[float] = None,
    y: Optional[float] = None,
    distance: Optional[float] = None
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    """
    Lists available Wanted and Donated items based on item types and optional location filtering.

    :param item_types: List of item type strings to filter.
    :param x: Optional X-coordinate for location filtering (only applies to DonatedItems).
    :param y: Optional Y-coordinate for location filtering (only applies to DonatedItems).
    :param distance: Optional radius distance to include items within (only applies to DonatedItems).
    :return: Tuple containing two lists:
             - List of tuples for WantedItems (item_type, total_available_amount)
             - List of tuples for DonatedItems (item_type, total_available_amount)
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

    # Base query for DonatedItems
    donated_query = (
        db.session.query(
            DonatedItem.item_type,
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

    # Convert results to dictionaries for easy lookup
    wanted_dict = {item_type: total for item_type, total in wanted_items}
    donated_dict = {item_type: total for item_type, total in donated_items}

    # Prepare the result lists
    wanted_result = []
    donated_result = []

    for item_type in item_types:
        wanted_amount = wanted_dict.get(item_type, 0)
        donated_amount = donated_dict.get(item_type, 0)
        wanted_result.append((item_type, wanted_amount))
        donated_result.append((item_type, donated_amount))

    return wanted_result, donated_result


def find_closest_items(
    item_type: str,
    amount: int,
    x: float,
    y: float,
    max_distance: float
) -> List[Tuple[int, float, float, int]]:
    """
    Finds the closest available donated items to fulfill a wanted item request.

    :param item_type: The type of the item to find.
    :param amount: The total amount needed.
    :param x: X-coordinate of the desired location.
    :param y: Y-coordinate of the desired location.
    :param max_distance: Maximum distance to search for items.
    :return: List of tuples, each containing:
             (donated_item_id, donated_x, donated_y, allocated_amount)
    """
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

    # Query to get available donated items with calculated available_amount
    available_donated = (
        db.session.query(
            DonatedItem.id,
            DonatedItem.x,
            DonatedItem.y,
            (DonatedItem.item_amount - func.coalesce(fulfilled_donated_subq.c.total_fulfilled, 0)).label('available_amount'),
            func.sqrt(func.pow(DonatedItem.x - x, 2) + func.pow(DonatedItem.y - y, 2)).label('distance')
        )
        .outerjoin(fulfilled_donated_subq, DonatedItem.id == fulfilled_donated_subq.c.donated_item_id)
        .filter(
            DonatedItem.item_type == item_type,
            DonatedItem.is_available == True,
            func.sqrt(func.pow(DonatedItem.x - x, 2) + func.pow(DonatedItem.y - y, 2)) <= max_distance,
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

        result.append((item.id, item.x, item.y, allocated))
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
