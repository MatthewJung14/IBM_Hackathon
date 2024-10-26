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

def obtain_tool_list(tools_file_path="tools.json"):
    with open(tools_file_path, 'r') as file:
        tools_data = json.load(file)
    items_list = list(tools_data.keys())
    return items_list

def obtain_JSON(model_output):
    json_pattern = re.search(r'\{.*\}', model_output, re.DOTALL)
    if json_pattern:
        json_str = json_pattern.group()  # Extract JSON-like part as a string
        try:
            # Parse JSON string and write to file
            json_data = json.loads(json_str)
            print(json_data)
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

    prompt = f'''Based on the user's input, identify the action they want to take from the following list:

    Actions:
    - {', '.join(actions)}

    User Input: "{user_input}"

    Respond with the corresponding action only, without any additional explanations or context.
    '''
    action = model.generate_text(prompt).strip()
    print(action)

    if "get news" in action:
        print("Action identified: get news")
        # Add logic for getting news
    if "view profile" in action:
        print("Action identified: view profile")
        # Add logic for viewing profile
    if "logout" in action:
        print("Action identified: logout")
        # Add logic for logout
    if "obtain safety checklist" in action:
        print("Action identified: obtain safety checklist")
        # Add logic for obtaining safety checklist
    if "preview requests" in action:
        print("Action identified: preview requests")
        # Add logic for previewing requests
    if "weather alerts" in action:
        print("Action identified: weather alerts")
        # Add logic for handling weather alerts
    if "get/send help" in action:
        extract_tools()
        print("Action identified: get/send help")
    else:
        print("Unidentified action.")

determine_action()

def parseRequest(request):
    #1, see what the request is
    #2. execute each request and have ai chatbot respond to those requests
    #3. store those responses in a a string array and return that
    pass