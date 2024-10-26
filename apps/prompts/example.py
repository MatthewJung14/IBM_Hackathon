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
            print("JSON data saved to model_output.json")
            return json_data
        except json.JSONDecodeError:
            print("Extracted text is not valid JSON:", json_str)
    else:
        print("No JSON structure found in model response.")

def extract_tools():
    items_list = obtain_tool_list()

    user_input = "I want a generator, ladders, a few waters, and seven plastic trays."

    prompt = f'''Analyze the user's intent based on the input text and respond with only one of the following JSON outputs, based on that intent.
    Limit items to those in this list: {items_list}.

    Return only the appropriate JSON format with no extra explanations.

    Format all JSON items to be donated like this:
    {{
        "donate": [["item 1", "amount"], ["item 2", "amount"], ...]
    }}

    Format all JSON items to be needed like this:
    {{
        "needs": [["item 1", "amount"], ["item 2", "amount"], ...]
    }}

    Text: "{user_input}"
    '''
    model_output = model.generate_text(prompt)
    print(model_output)

    return obtain_JSON(model_output)

extract_tools()

# user_input = "My Kitchen got flooded."

# prompt = '''Respond in JSON format with lists of items that a person "needs" and items they "give" based on the input text. Use this format: 
# {{"needs": ["item 1", "amount", "item 2", "amount" ...], "gives": ["item 1", "amount", "item 2", "amount" ...]}}
# Text: "{user_input}"
# '''