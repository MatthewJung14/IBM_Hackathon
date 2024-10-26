# routes.py

from flask import render_template, redirect, request, url_for, session, current_app, jsonify
from apps.chatbotAPI import blueprint
from apps.prompts.prompts import UserActionHandler

userActionHandler = UserActionHandler()

# Hypothetical function that processes the input string
def process_message(input_string: str) -> list:
    """
    Processes the input string and returns a list of tuples containing strings and integers.

    :param input_string: The input message to process.
    :return: A list of tuples, each containing a string and a string.
    """
    tasks=userActionHandler.generateTasks(input_string)
    wanted_needed_items=[]

    responses=[]

    for task in tasks:
        if task == "get/send help":
            wanted_needed_items = userActionHandler.extract_tools(input_string)
            print(wanted_needed_items)
        elif task == "view profile":
            responses.append(
                ("👋 Hey! Want to check out your profile or make some changes? Click here <profileLink>! 😊",
                 task))
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

    return responses


@blueprint.route('/message', methods=['POST'])
def handle_message():
    """
    Endpoint to handle messages. Accepts a JSON payload with a 'message' field.
    Processes the message and returns a JSON response containing the results.

    Expected JSON Payload:
    {
        "message": "Your input string here"
    }

    Responses:
    - Success: 200 OK with the processed data.
    - Client Error: 400 Bad Request if the input string is empty or missing.
    - Server Error: 500 Internal Server Error for unexpected issues.
    """
    data = request.get_json()

    # Check if JSON payload is provided
    if not data:
        return jsonify({"error": "Missing JSON payload"}), 400

    # Retrieve the 'message' field from the JSON payload
    message = data.get('message')

    # Validate that the 'message' field exists and is not empty
    if message is None:
        return jsonify({"error": "Missing 'message' field in the request"}), 400
    if not isinstance(message, str):
        return jsonify({"error": "'message' must be a string"}), 400
    if message.strip() == "":
        return jsonify({"error": "'message' field cannot be empty"}), 400

    try:
        # Process the message using the hypothetical function
        processed_data = process_message(message)

        # Validate the processed data format
        if not isinstance(processed_data, list):
            return jsonify({"error": "Processed data is not a list"}), 500
        for item in processed_data:
            if not (isinstance(item, tuple) and len(item) == 2):
                return jsonify({"error": "Each item in processed data must be a tuple of (string, int)"}), 500
            if not isinstance(item[0], str) or not isinstance(item[1], str):
                return jsonify({"error": "Each tuple must contain a pair of strings"}), 500

        # Structure the response data
        response = {
            "status": "Message processed successfully",
            "results": [
                {"text": text, "type": type} for text, type in processed_data
            ]
        }

        return jsonify(response), 200

    except Exception as e:
        # Log the exception details (optional but recommended)
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
