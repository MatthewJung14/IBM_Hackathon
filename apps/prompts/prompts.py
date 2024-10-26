from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
import json
import re

credentials = Credentials(
    url = "https://us-south.ml.cloud.ibm.com",
    api_key = "C9S_dk9_zIAAxT8YKPNI6ka2f8tXSDCO2Yef4viieCk0",
)

client = APIClient(credentials)

model = ModelInference(
  model_id="ibm/granite-13b-chat-v2",
  api_client=client,
  project_id="ada8a81e-64d2-4d9b-a0c3-421e15989a77",
  params = {
      "max_new_tokens": 100
  }
)

user_input = "I want a generator, ladders, a few waters, and seven plastic trays. I would like to donate some Plywood."
#user_input = "I want to donate a ladder."

def obtain_tool_list(tools_file_path="tools.json"):
    with open(tools_file_path, 'r') as file:
        tools_data = json.load(file)
    items_list = list(tools_data.keys())
    return items_list

def obtain_news_list(news_file_path="news.json"):
    with open(news_file_path, 'r') as file:
        news_data = json.load(file)
    news_list = list(news_data.keys())
    return news_list

def obtain_JSON(model_output):
    json_pattern = re.search(r'\{.*\}', model_output, re.DOTALL)
    if json_pattern:
        json_str = json_pattern.group()  # Extract JSON-like part as a string
        try:
            # Parse JSON string and write to file
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError:
            print("Extracted text is not valid JSON:", json_str)
    else:
        print("No JSON structure found in model response.")

def extract_tools():
    items_list = obtain_tool_list()

    prompt = f'''Analyze the user's intent based on the input text and respond with only one of the following JSON outputs, based on that intent.
    Limit items to those in this list: {items_list}.

    Return only the appropriate JSON format with no extra explanations.

    Format all JSON items to be donated like this:
    {{
        "donate": [["item 1", amount], ["item 2", amount], ...]
    }}

    Format all JSON items to be needed like this:
    {{
        "needs": [["item 1", amount], ["item 2", amount], ...]
    }}

    Ensure that the output only contains "needs" and "donate". 
    
    If the user does not specify an amount, determine the number yourself, and return it as an integer.

    Text: "{user_input}"
    '''
    model_output = model.generate_text(prompt)
    #print(model_output)

    location = get_location()
    print(location)

    return obtain_JSON(model_output)

def determine_action():
    actions = [
    "get news",
    "view profile",
    "logout",
    "obtain safety checklist",
    "preview requests",
    "weather alerts",
    "get/send help"
    ]

    prompt = f'''Based on the user's input, identify the action they want to take from the following list (choose an answer exactly from the list):

    Actions:
    - {', '.join(actions)}

    User Input: "{user_input}"

    Respond with the corresponding action only, without any additional explanations or context.
    '''
    action = model.generate_text(prompt).strip()
    print(action)
    response_found = False
    responses =[]

    if "get news" in action:
        print("Action identified: get news")
        response_found = True
        news_list = obtain_news_list()
    if "view profile" in action:
        print("Action identified: view profile")
        response_found = True
        # Add logic for viewing profile
    if "logout" in action:
        print("Action identified: logout")
        response_found = True
        # Add logic for logout
    if "obtain safety checklist" in action:
        print("Action identified: obtain safety checklist")
        response_found = True
        # Add logic for obtaining safety checklist
    if "preview requests" in action:
        print("Action identified: preview requests")
        response_found = True
        # Add logic for previewing requests
    if "weather alerts" in action:
        print("Action identified: weather alerts")
        response_found = True
        # Add logic for handling weather alerts
    if "get/send help" in action:
        response_found = True
        responses.append(extract_tools())
        print("Action identified: get/send help")
    if response_found == False:
        print("Unidentified action.")

    for response in responses:
        print(response)

    return responses

def get_location():
    prompt = f'''Based on the user's input, if there is a location, return location.
    User Input: "{user_input}"
    Respond only with the location if a location was provided, or "false" if it was not. 
    No additional context, explanations, or code should be included.
    '''
    response = model.generate_text(prompt).strip()  # Get the model's response

    location_match = re.search(r'\b(?:in|at|located in)\s*([A-Z][a-zA-Z\s]+)', response)
    
    if location_match:
        return location_match.group(1).strip()  # Return the extracted location
    else:
        return "No location."

determine_action()

#print(get_location())