# routes.py

from flask import render_template, redirect, request, url_for, session, current_app, jsonify
from apps.databaseAPI import blueprint
from apps.databaseAPI.helpers import (
    get_uncompleted_donated_items,
    get_unfulfilled_wanted_items,
    donateListofItems,
    wantListofItems,
    complete_request,
    list_available_items,
    find_closest_items, get_data_lists
)


@blueprint.route('/')
def route_default():
    """
    Default route that provides a list of available API actions with their details.
    """
    available_actions = {
        "available_actions": [
            {
                "endpoint": "/donate",
                "method": "POST",
                "description": "Donate a list of items. (Updates the database)",
                "payload": {
                    "user_id": "string (256 characters)",
                    "x": "float (Longitude of the donation location)",
                    "y": "float (Latitude of the donation location)",
                    "item_location": "string (General location description)",
                    "items": "list of [item_type (string), item_amount (integer)]"
                }
            },
            {
                "endpoint": "/want",
                "method": "POST",
                "description": "Request a list of wanted items. (Updates the database)",
                "payload": {
                    "user_id": "string (256 characters)",
                    "item_location": "string (General location description)",
                    "items": "list of [item_type (string), item_amount (integer)]"
                }
            },
            {
                "endpoint": "/complete-request",
                "method": "POST",
                "description": "Allocate donated items to fulfill a wanted item request. (Updates the database)",
                "payload": {
                    "wanted_item_id": "integer (ID of the wanted item)",
                    "allocations": "list of [donated_item_id (integer), amount (integer)]"
                }
            },
            {
                "endpoint": "/unfulfilled-wanted",
                "method": "GET",
                "description": "Retrieve unfulfilled wanted items for a specific user.",
                "parameters": {
                    "user_id": "string (256 characters)"
                }
            },
            {
                "endpoint": "/uncompleted-donated",
                "method": "GET",
                "description": "Retrieve still available donated items for a specific user.",
                "parameters": {
                    "user_id": "string (256 characters)"
                }
            },
            {
                "endpoint": "/list-available-items",
                "method": "GET",
                "description": "List available wanted and donated items based on item types and optional location filtering.",
                "parameters": {
                    "item_types": "list of strings (item types to filter)",
                    "x": "float (optional, Longitude for filtering donated items)",
                    "y": "float (optional, Latitude for filtering donated items)",
                    "distance": "float (optional, radius distance in miles for filtering donated items)"
                }
            },
            {
                "endpoint": "/find-closest-items",
                "method": "GET",
                "description": "Find the closest available donated items to fulfill a wanted item request.",
                "parameters": {
                    "item_type": "string (type of item to find)",
                    "amount": "integer (total amount needed)",
                    "x": "float (Longitude of the desired location)",
                    "y": "float (Latitude of the desired location)",
                    "max_distance": "float (maximum distance in miles to search for items)"
                }
            }
        ]
    }

    return jsonify(available_actions), 200


@blueprint.route('/donate', methods=['POST'])
def donate_items():
    """
    Endpoint to donate a list of items.
    Expects JSON payload with user_id, x, y, item_location, and items.
    """
    data = request.get_json()

    user_id = data.get('user_id')
    x = data.get('x')  # Longitude
    y = data.get('y')  # Latitude
    item_location = data.get('item_location')
    items = data.get('items')  # Expected to be a list of [item_type, item_amount] lists

    if not all([user_id, x !=None, y !=None, item_location, items]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Validate items format
    if not isinstance(items, list) or not all(isinstance(item, list) and len(item) == 2 for item in items):
        return jsonify({"error": "Items must be a list of [item_type, item_amount] lists"}), 400

    try:
        donated_items = donateListofItems(user_id, x, y, item_location, items)
        donated_items_data = [
            {
                "id": item.id,
                "item_type": item.item_type,
                "item_amount": item.item_amount,
                "location": item.item_location,
                "coordinates": {"x": item.x, "y": item.y},
                "timestamp": item.timestamp.isoformat()
            }
            for item in donated_items
        ]
        return jsonify({"status": "Donation successful", "donated_items": donated_items_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprint.route('/want', methods=['POST'])
def want_items():
    """
    Endpoint to request a list of wanted items.
    Expects JSON payload with user_id, item_location, and items.
    """
    data = request.get_json()

    user_id = data.get('user_id')
    item_location = data.get('item_location')
    items = data.get('items')  # Expected to be a list of [item_type, item_amount] lists

    if not all([user_id, item_location, items]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Validate items format
    if not isinstance(items, list) or not all(isinstance(item, list) and len(item) == 2 for item in items):
        return jsonify({"error": "Items must be a list of [item_type, item_amount] lists"}), 400

    try:
        wanted_items = wantListofItems(user_id, item_location, items)
        wanted_items_data = [
            {
                "id": item.id,
                "item_type": item.item_type,
                "item_amount": item.item_amount,
                "location": item.item_location,
                "timestamp": item.timestamp.isoformat()
            }
            for item in wanted_items
        ]
        return jsonify({"status": "Request successful", "wanted_items": wanted_items_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprint.route('/complete-request', methods=['POST'])
def complete_request_route():
    """
    Endpoint to complete a wanted item request by allocating donated items.
    Expects JSON payload with wanted_item_id and allocations.
    """
    data = request.get_json()

    wanted_item_id = data.get('wanted_item_id')
    allocations = data.get('allocations')  # Expected to be a list of [donated_item_id, amount] lists

    if not all([wanted_item_id, allocations]):
        return jsonify({"error": "Missing required parameters: 'wanted_item_id' and 'allocations'"}), 400

    # Validate allocations format
    if not isinstance(allocations, list) or not all(isinstance(item, list) and len(item) == 2 for item in allocations):
        return jsonify({"error": "Allocations must be a list of [donated_item_id, amount] lists"}), 400

    try:
        # Convert allocations to list of tuples
        allocations_tuples = [(int(item[0]), int(item[1])) for item in allocations]

        # Call the helper function to perform allocations
        created_links = complete_request(wanted_item_id, allocations_tuples)

        # Prepare response data
        links_data = [
            {
                "id": link.id,
                "wanted_item_id": link.wanted_item_id,
                "donated_item_id": link.donated_item_id,
                "amount_fulfilled": link.amount_fulfilled,
                "timestamp": link.wanted_item.timestamp.isoformat()  # Assuming you want the wanted item's timestamp
            }
            for link in created_links
        ]

        return jsonify({"status": "Request completed successfully", "allocations": links_data}), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprint.route('/unfulfilled-wanted', methods=['GET'])
def unfulfilled_wanted_items():
    """
    Endpoint to retrieve unfulfilled wanted items for a user.
    Expects 'user_id' as a query parameter.
    """
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing 'user_id' parameter"}), 400

    try:
        unfulfilled_items = get_unfulfilled_wanted_items(user_id)
        items_data = [
            {
                "id": item.id,
                "item_type": item.item_type,
                "requested_amount": item.item_amount,
                "location": item.item_location,
                "timestamp": item.timestamp.isoformat(),
                "available_amount": item.item_amount - sum(link.amount_fulfilled for link in item.links)
            }
            for item in unfulfilled_items
        ]
        return jsonify({"unfulfilled_wanted_items": items_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprint.route('/uncompleted-donated', methods=['GET'])
def uncompleted_donated_items():
    """
    Endpoint to retrieve undelivered donated items for a user.
    Expects 'user_id' as a query parameter.
    """
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing 'user_id' parameter"}), 400

    try:
        uncompleted_items = get_uncompleted_donated_items(user_id)
        items_data = [
            {
                "id": item.id,
                "item_type": item.item_type,
                "donated_amount": item.item_amount,
                "location": item.item_location,
                "coordinates": {"x": item.x, "y": item.y},
                "timestamp": item.timestamp.isoformat(),
                "available_amount": item.item_amount - sum(link.amount_fulfilled for link in item.links)
            }
            for item in uncompleted_items
        ]
        return jsonify({"uncompleted_donated_items": items_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprint.route('/list-available-items', methods=['GET'])
def list_available_items_route():
    """
    Endpoint to list available wanted and donated items based on item types and optional location filtering.
    Expects query parameters: item_types (can be multiple), x, y, distance.
    """
    item_types = request.args.getlist('item_types')  # e.g., /list-available-items?item_types=Blankets&item_types=Food
    x = request.args.get('x', type=float)  # Longitude
    y = request.args.get('y', type=float)  # Latitude
    distance = request.args.get('distance', type=float)

    if not item_types:
        return jsonify({"error": "At least one 'item_types' parameter is required"}), 400

    # If any of x, y is provided, ensure all three (x, y, distance) are provided
    if any(param is not None for param in [x, y, distance]):
        if not all(param is not None for param in [x, y, distance]):
            return jsonify({"error": "When filtering by location, 'x', 'y', and 'distance' must all be provided"}), 400

    try:
        wanted, donated = list_available_items(item_types, x, y, distance)

        wanted_items = [
            {"item_type": t, "total_available": a, "userAvailableAmounts":u}
            for t, a,u in wanted
        ]

        donated_items = [
            {"item_type": t, "total_available": a, "userAvailableAmounts":u}
            for t, a,u in donated
        ]

        return jsonify({
            "wanted_items": wanted_items,
            "donated_items": donated_items
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprint.route('/find-closest-items', methods=['GET'])
def find_closest_items_route():
    """
    Endpoint to find the closest available donated items to fulfill a wanted item request.
    Expects query parameters:
        - item_type (string)
        - amount (integer)
        - x (float)
        - y (float)
        - max_distance (float)
    """
    item_type = request.args.get('item_type')
    amount = request.args.get('amount', type=int)
    x = request.args.get('x', type=float)  # Longitude
    y = request.args.get('y', type=float)  # Latitude
    max_distance = request.args.get('max_distance', type=float)

    # Validate required parameters
    if not all([item_type, amount, x is not None, y is not None, max_distance is not None]):
        return jsonify({"error": "Missing required parameters: 'item_type', 'amount', 'x', 'y', 'max_distance'"}), 400

    # Additional validations
    if amount <= 0:
        return jsonify({"error": "'amount' must be a positive integer"}), 400
    if max_distance <= 0:
        return jsonify({"error": "'max_distance' must be a positive float"}), 400

    try:
        closest_items = find_closest_items(item_type, amount, x, y, max_distance)

        allocations = [
            {
                "donated_item_id": item_id,
                "location name":address,
                "coordinates": {"x": donated_x, "y": donated_y},
                "allocated_amount": allocated
            }
            for item_id, donated_x, donated_y, address, allocated in closest_items
        ]

        return jsonify({"closest_items": allocations}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@blueprint.route('/data-lists', methods=['GET'])
def data_lists():
    """
    Endpoint to return lists of donated items, wanted items, and item links with coordinates.
    """
    try:
        donated_items_data, wanted_items_data, item_links_data = get_data_lists()

        return jsonify({
            "donated_items": donated_items_data,
            "wanted_items": wanted_items_data,
            "item_links": item_links_data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
