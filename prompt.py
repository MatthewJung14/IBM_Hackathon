from flask import Flask, request, render_template_string
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, CategoriesOptions
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

app = Flask(__name__)

# Watson NLU setup
authenticator = IAMAuthenticator('C9S_dk9_zIAAxT8YKPNI6ka2f8tXSDCO2Yef4viieCk0')
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2020-08-01',
    authenticator=authenticator
)
natural_language_understanding.set_service_url('https://us-south.ml.cloud.ibm.com')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['user_input']
        response = natural_language_understanding.analyze(
            text=user_input,
            features=Features(categories=CategoriesOptions(limit=3))
        ).get_result()

        return f"Watson Analysis: {response}"
    
    return render_template_string('''
        <form method="post">
            Enter Text: <input type="text" name="user_input"><br>
            <input type="submit" value="Submit">
        </form>
    ''')

if __name__ == '__main__':
    app.run(debug=True)