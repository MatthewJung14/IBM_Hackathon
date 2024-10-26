from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
import json
import re
import textwrap

credentials = Credentials(
    url = "https://us-south.ml.cloud.ibm.com",
    api_key = "C9S_dk9_zIAAxT8YKPNI6ka2f8tXSDCO2Yef4viieCk0",
)

client = APIClient(credentials)

model = ModelInference(
  model_id="ibm/granite-3-8b-instruct",
  api_client=client,
  project_id="ada8a81e-64d2-4d9b-a0c3-421e15989a77",
  params = {
      "max_new_tokens": 100
  }
)

user_input = "What is the current situation like?"
#user_input = "I want a generator, ladders, a few waters, and seven plastic trays. I would like to donate some Plywood."

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

def get_news():
    with open('news.json', 'r') as file:
        news_list = json.load(file)

    prompt = (f"Create a 20 word short summary about the news from all the titles and descriptions in the articles in the JSON files (Do not describe the json file and At the end insert a new line and print 'To get more news Click <newsButton>'): {news_list},"
              )

    result_paragraph = model.generate_text(prompt)
    # Wrap the text to a width of 50 characters per line
    wrapped_text = textwrap.fill(result_paragraph, width=50)

    # Print the formatted text
    print(wrapped_text)



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

    prompt = f'''Based on the user's input, identify the action they want to take from the following list (choose an answer exactly from the list):

    Actions:
    - {', '.join(actions)}

    User Input: "{user_input}"

    Respond with the corresponding action only, without any additional explanations or context.
    '''
    action = model.generate_text(prompt).strip()
    print(action)
    response_found = False

    if "get news" in action:
        print("Action identified: get news")
        response_found = True
        # Add logic for getting news
        get_news()
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
        extract_tools()
        print("Action identified: get/send help")
    if response_found == False:
        print("Unidentified action.")

determine_action()

def parseRequest(request):
    #1, see what the request is
    #2. execute each request and have ai chatbot respond to those requests
    #3. store those responses in a a string array and return that
    pass