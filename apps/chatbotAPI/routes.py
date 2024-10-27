import requests
from flask import render_template, redirect, request, url_for, session, current_app, jsonify
from apps.chatbotAPI import blueprint
from apps.prompts.prompts import UserActionHandler

userActionHandler = UserActionHandler()

# Caches
cache = {}
location_cache = {}
IPINFO_API_TOKEN = "52bed83427e70c"  # Replace with your actual IPInfo API token


def get_geolocation(ip_address):
    """
    Geolocates the IP address using ipinfo.io API.

    :param ip_address: The IP address to geolocate.
    :return: A dictionary with geolocation data or an error message.
    """
    url = f"http://ipinfo.io/{ip_address}/json?token={IPINFO_API_TOKEN}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def handle_response_task(user_id, message, task):
    """
    Handles the response task. Tries to get the cached wanted_needed_items for the user_id.
    Returns the nearby items list and task values of 'confirm donate to' or 'confirm get from'.
    """
    wanted_needed_items = cache.get(user_id)

    if not wanted_needed_items:
        print("Failed at handling task for user:", user_id)
        return {'error': 'No pending tasks found for this user.'}, 'error'

    message = message.strip().lower()
    if 'yes' not in message:
        return {'message': 'Confirmation not received or message not recognized.'}, 'no confirmation'

    # Get user location
    x, y = location_cache.get(user_id, (None, None))
    if x is None or y is None:
        # Cannot proceed without location
        return {'error': 'User location not available.'}, 'error'

    # Assuming we have a function to get item_location based on coordinates
    item_location = 'Your Location'  # Placeholder

    headers = {'Content-Type': 'application/json'}

    if task == 'donate confirmation':
        # Handle donation confirmation as before
        donate_url = url_for('databaseAPI_blueprint.donate_items', _external=True)

        # Prepare data for /api/donate
        donate_items = wanted_needed_items.get('donate', [])
        items = donate_items  # List of [item_type, item_amount]

        if not items:
            return {'error': 'No items to donate found.'}, 'error'

        data = {
            'user_id': user_id,
            'x': x,
            'y': y,
            'item_location': item_location,
            'items': items
        }
        response = requests.post(donate_url, json=data, headers=headers)

        if response.status_code == 201:
            # Donation successful
            list_items_url = url_for('databaseAPI_blueprint.list_available_items_route', _external=True)

            item_types = [item[0] for item in items]
            params = [('item_types', it) for it in item_types]
            list_response = requests.get(list_items_url, params=params)

            if list_response.status_code == 200:
                list_data = list_response.json()

                # Check if there are wanted items with availability greater than zero
                available_wanted_items = [
                    item for item in list_data.get('wanted_items', [])
                    if item.get('total_available', 0) > 0
                ]

                if available_wanted_items:
                    # Store allocation data in cache for future confirmation
                    cache[f'allocation_{user_id}'] = {
                        'donated_item_ids': [item['id'] for item in response.json()['donated_items']],
                        'wanted_items': available_wanted_items
                    }

                    # Prepare response with available wanted items
                    return {
                        'message': 'Donation successful. There are people requesting your items.',
                        'wanted_items': available_wanted_items
                    }, 'confirm donate to'
                else:
                    # No wanted items with availability greater than zero
                    return {
                        'message': 'You have donated the items, but no one is currently requesting them.'
                    }, 'no items found'

            else:
                return {'error': 'Failed to retrieve wanted items.'}, 'error'
        else:
            return {'error': 'Failed to donate items.'}, 'error'

    elif task == 'need confirmation':
        # Handle need confirmation as before
        wanted_items = wanted_needed_items.get('needs', [])
        items = wanted_items  # List of [item_type, item_amount]

        if not items:
            return {'error': 'No items requested found.'}, 'error'

        # Prepare data for /api/want
        want_url = url_for('databaseAPI_blueprint.want_items', _external=True)
        data = {
            'user_id': user_id,
            'item_location': item_location,
            'items': items
        }
        response = requests.post(want_url, json=data, headers=headers)

        if response.status_code == 201:
            wanted_items_data = response.json()['wanted_items']
            allocations = []
            for item in wanted_items_data:
                find_items_url = url_for('databaseAPI_blueprint.find_closest_items_route', _external=True)
                item_type = item['item_type']
                amount = item['item_amount']
                wanted_item_id = item['id']
                params = {
                    'item_type': item_type,
                    'amount': amount,
                    'x': x,
                    'y': y,
                    'max_distance': 50  # 50 miles
                }
                find_response = requests.get(find_items_url, params=params)
                if find_response.status_code == 200:
                    find_data = find_response.json()
                    if find_data.get('closest_items'):
                        # Store allocation data in cache for future confirmation
                        cache[f'allocation_{user_id}'] = {
                            'wanted_item_id': wanted_item_id,
                            'allocations': [
                                [item['donated_item_id'], item['allocated_amount']] for item in
                                find_data['closest_items']
                            ]
                        }
                        allocations.append({
                            'item_type': item_type,
                            'available_items': find_data['closest_items']
                        })
                    else:
                        allocations.append({
                            'item_type': item_type,
                            'message': f'No donated items found for {item_type}'
                        })
                else:
                    allocations.append({
                        'item_type': item_type,
                        'message': f'Error finding items for {item_type}'
                    })
            return {'allocations': allocations}, 'confirm get from'

    elif task == 'confirm donate to':
        # User is confirming they want to allocate their donation to specific requests
        allocation_data = cache.get(f'allocation_{user_id}')
        if not allocation_data:
            return {'error': 'No allocation data found.'}, 'error'

        donated_item_ids = allocation_data.get('donated_item_ids')
        wanted_items = allocation_data.get('wanted_items')

        if not donated_item_ids or not wanted_items:
            return {'error': 'Incomplete allocation data.'}, 'error'

        # Prepare allocations
        allocations = []
        for wanted_item in wanted_items:
            wanted_item_id = wanted_item['id']
            item_type = wanted_item['item_type']
            total_available = wanted_item['total_available']

            # For simplicity, allocate from the first donated item
            donated_item_id = donated_item_ids[0]
            allocations.append([donated_item_id, total_available])

        # Prepare data for /complete-request
        complete_request_url = url_for('databaseAPI_blueprint.complete_request_route', _external=True)
        data = {
            'wanted_item_id': wanted_items[0]['id'],  # Assuming only one wanted item for simplicity
            'allocations': allocations
        }
        response = requests.post(complete_request_url, json=data, headers=headers)
        if response.status_code == 201:
            return {'message': 'Your donation has been allocated to those in need.'}, 'success'
        else:
            return {'error': 'Failed to complete allocation.'}, 'error'

    elif task == 'confirm get from':
        # User is confirming they want to receive items from donors
        allocation_data = cache.get(f'allocation_{user_id}')
        if not allocation_data:
            return {'error': 'No allocation data found.'}, 'error'

        wanted_item_id = allocation_data.get('wanted_item_id')
        allocations = allocation_data.get('allocations')

        if not wanted_item_id or not allocations:
            return {'error': 'Incomplete allocation data.'}, 'error'

        # Prepare data for /complete-request
        complete_request_url = url_for('databaseAPI_blueprint.complete_request_route', _external=True)
        data = {
            'wanted_item_id': wanted_item_id,
            'allocations': allocations
        }
        response = requests.post(complete_request_url, json=data, headers=headers)
        if response.status_code == 201:
            return {'message': 'Items have been allocated to you. Please contact the donor for pickup details.'}, 'success'
        else:
            return {'error': 'Failed to complete allocation.'}, 'error'

    else:
        return {'message': 'Task not handled.'}, 'error'

    # If nothing matches
    return {'message': 'Task not handled.'}, 'error'


def process_message(input_string: str, x: float = None, y: float = None) -> list:
    """
    Processes the input string and returns a list of tuples containing strings and integers.

    :param input_string: The input message to process.
    :param x: Optional latitude coordinate.
    :param y: Optional longitude coordinate.
    :return: A list of tuples, each containing a string and a string.
    """
    tasks = userActionHandler.generateTasks(input_string)
    wanted_needed_items = []
    responses = []

    user_id = request.get_json().get("user_id")
    ip_address = request.remote_addr
    coordinates = (x, y) if x is not None and y is not None else None

    if coordinates:
        # Store provided coordinates in location_cache
        location_cache[user_id] = coordinates
    else:
        # Get geolocation from IP if no coordinates are provided
        geolocation_data = get_geolocation(ip_address)
        loc = geolocation_data.get("loc", "29.6516,-82.3248")  # Default to (29.6516, -82.3248) if "loc" is missing
        location_cache[user_id] = tuple(map(float, loc.split(",")))

    print("Geolocation for user:", user_id, location_cache[user_id])

    # Process tasks and add appropriate responses
    for task in tasks:
        if task == "get/send help":
            wanted_needed_items = userActionHandler.extract_tools(input_string)
            print(wanted_needed_items)
        elif task == "view profile":
            responses.append(
                ("👋 Hey! Want to check out your profile or make some changes? Click here <profileLink>! 😊", task))
        elif task == "logout":
            responses.append((
                             "🚪 Time to log out? You can click the logout button on the left (it's the running person 🏃‍♂️) or click here <logoutLink>!",
                             task))
        elif task == "obtain safety checklist":
            responses.append((
                             "🌟 Stay safe! Check out <safetyChecklistLink> for tips on how to keep yourself safe and sound 🙏",
                             task))
        elif task == "weather alerts":
            responses.append((
                             "⛈️ Oh no! The hurricane is still headed your way! Stay updated and check out <weatherLink> for more info 🌪️",
                             task))

    # Process wanted/needed items
    if wanted_needed_items:
        location = userActionHandler.get_location(input_string)
        if 'donate' in wanted_needed_items and 'needs' in wanted_needed_items:
            if location:
                responses.append((
                                 f"🤝 You're donating and needing items at the same time! We've got you covered. Please confirm that you want to donate {', '.join([item[0] for item in wanted_needed_items['donate']])} and need {', '.join([item[0] for item in wanted_needed_items['needs']])} at {location}. Reply with 'yes' to confirm.",
                                 "donate and need confirmation"))
            else:
                responses.append((
                                 "🚨 Error! You're donating and needing items at the same time, but you didn't include a location. Please try again with a location.",
                                 "error"))
        elif 'donate' in wanted_needed_items:
            if location:
                responses.append((
                                 f"🎁 You're donating {', '.join([item[0] for item in wanted_needed_items['donate']])} at {location}. Please confirm by replying with 'yes'.",
                                 "donate confirmation"))
            else:
                responses.append((
                                 "🚨 Error! You're donating items, but you didn't include a location. Please try again with a location.",
                                 "error"))
        elif 'needs' in wanted_needed_items:
            if location:
                responses.append((
                                 f"🤝 You need {', '.join([item[0] for item in wanted_needed_items['needs']])} at {location}. Please confirm by replying with 'yes'.",
                                 "need confirmation"))
            else:
                responses.append((
                                 f"🤝 You need {', '.join([item[0] for item in wanted_needed_items['needs']])}. Please confirm by replying with 'yes'. You can also type your location for more accurate results.",
                                 "need confirmation"))

    return wanted_needed_items, responses


@blueprint.route('/message', methods=['POST'])
def handle_message():
    """
    Endpoint to handle messages. Accepts a JSON payload with 'user_id', 'message', and optional 'task' fields.
    Processes the message and returns a JSON response containing the results.

    Expected JSON Payload:
    {
        "user_id": "User ID here",
        "message": "Your input string here",
        "task": "Optional task here"
    }

    Responses:
    - Success: 200 OK with the processed data.
    - Client Error: 400 Bad Request if required fields are missing or invalid.
    - Server Error: 500 Internal Server Error for unexpected issues.
    """
    data = request.get_json()

    # Check if JSON payload is provided
    if not data:
        return jsonify({"error": "Missing JSON payload"}), 400

    # Retrieve the 'user_id', 'message', and 'task' fields from the JSON payload
    user_id = data.get('user_id')
    message = data.get('message')
    task = data.get('task')  # This is optional
    x = data.get('x')  # Optional latitude
    y = data.get('y')  # Optional longitude

    # If 'task' is provided, call handle_response_task
    if task:
        result=handle_response_task(user_id, message, task)
        return jsonify(result)
    else:
        cache_retrieved = None

    # Validate user_id and message
    if not user_id or not isinstance(user_id, str) or not user_id.strip():
        return jsonify({"error": "Invalid or missing 'user_id'"}), 400
    if not message or not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Invalid or missing 'message'"}), 400

    try:
        # Process the message with optional coordinates
        wants_needs_items, processed_data = process_message(message, x, y)

        # Validate the processed data format
        if not isinstance(processed_data, list):
            return jsonify({"error": "Processed data is not a list"}), 500
        for item in processed_data:
            if not (isinstance(item, tuple) and len(item) == 2):
                return jsonify({"error": "Each item in processed data must be a tuple of (string, string)"}), 500

        # Store wanted_needed_items in cache associated with user_id
        if wants_needs_items:
            cache[user_id] = wants_needs_items

        # Structure the response data
        response = {
            "status": "Message processed successfully",
            "results": [{"text": text, "type": type} for text, type in processed_data]
        }
        if cache_retrieved is not None:
            response['cache_retrieved'] = cache_retrieved

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error processing message: {str(e)}")
        return jsonify({"error": "An error occurred while processing the message"}), 500


@blueprint.route('/')
def route_default():
    """
    Default route that provides a list of available API actions with their details.
    """
    available_actions = {
        "available_actions": [
            {
                "endpoint": "/message",
                "method": "POST",
                "description": "Send a message and receive processed responses.",
                "payload": {
                    "message": "string (The input message to process)"
                },
                "responses": {
                    "200": {
                        "description": "Successfully processed the message.",
                        "example": {
                            "status": "Message processed successfully",
                            "results": [
                                {"text": "response1", "number": 1},
                                {"text": "response2", "number": 2},
                                {"text": "response3", "number": 3}
                            ]
                        }
                    },
                    "400": {
                        "description": "Bad Request. Possible reasons: Missing payload, missing 'message' field, or empty 'message'.",
                        "example": {
                            "error": "'message' field cannot be empty"
                        }
                    },
                    "500": {
                        "description": "Internal Server Error. An unexpected error occurred.",
                        "example": {
                            "error": "An error occurred while processing the message"
                        }
                    }
                }
            }
        ]
    }

    return jsonify(available_actions), 200


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
