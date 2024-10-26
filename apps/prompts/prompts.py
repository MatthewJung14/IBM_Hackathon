from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
import json
import re


class UserActionHandler:
    def __init__(self,project_id="ada8a81e-64d2-4d9b-a0c3-421e15989a77", api_key = "C9S_dk9_zIAAxT8YKPNI6ka2f8tXSDCO2Yef4viieCk0", model_id="ibm/granite-3-8b-instruct", url="https://us-south.ml.cloud.ibm.com"):
        # Set up credentials and model inference instance
        credentials = Credentials(url=url, api_key=api_key)
        client = APIClient(credentials)
        self.model = ModelInference(
            model_id=model_id,
            api_client=client,
            project_id=project_id,
            params={"max_new_tokens": 100}
        )
        self.possible_actions=["get news", "view profile", "logout",
                               "obtain safety checklist","preview requests",
                               "weather alerts","get/send help"]

    def obtain_tool_list(self, tools_file_path="tools.json"):
        with open(tools_file_path, 'r') as file:
            tools_data = json.load(file)
        items_list = list(tools_data.keys())
        return items_list

    def obtain_news_list(self, news_file_path="news.json"):
        with open(news_file_path, 'r') as file:
            news_data = json.load(file)
        news_list = list(news_data.keys())
        return news_list

    def obtain_JSON(self, model_output):
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

    def extract_tools(self, user_request):
        items_list = self.obtain_tool_list()

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

        Text: "{user_request}"
        '''
        model_output = self.model.generate_text(prompt)
        #print(model_output)

        location = self.get_location(user_request)
        print(location)

        return self.obtain_JSON(model_output)

    def determine_action(self, user_request):
        actions = self.possible_actions
        prompt = f'''Based on the user's input, identify the action they want to take from the following list (choose answers exactly from the list):
        Actions:
        - {', '.join(actions)}

        User Input: "{user_request}"

        Respond with the corresponding action only, without any additional explanations or context.
        '''
        actions = self.model.generate_text(prompt).strip()
        print(actions)
        return actions

    def parseActions(self, previous_request, action_list):
        actions =[]

        for action in self.possible_actions:
            if action in action_list:
                actions.append(action)

        return actions

    def generateTasks(self, user_request)->list[int,str]:
        action_list = self.determine_action(user_request)
        results=self.parseActions(user_request, action_list)
        return results

    def get_location(self, user_request):
        prompt = f'''Based on the user's input, if there is a location, return location.
        User Input: "{user_request}"
        Respond only with the location if a location was provided, or "false" if it was not. 
        No additional context, explanations, or code should be included.
        '''
        response = self.model.generate_text(prompt).strip()  # Get the model's response

        location_match = re.search(r'\b(?:in|at|located in)\s*([A-Z][a-zA-Z\s]+)', response)
        
        if location_match:
            return location_match.group(1).strip()  # Return the extracted location
        else:
            return "No location."

if __name__ == '__main__':

    # user_input = "I want to donate a ladder."
    handler = UserActionHandler()
    user_input = "I want a generator, ladders, a few waters, and seven plastic trays. I would like to donate some Plywood. "
    response = handler.generateTasks(user_input)
    print(response)
