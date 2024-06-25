from flask import Flask, render_template, request, jsonify
import requests
import logging
import time
import re

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return render_template('index.html')

def add_hyperlink(text):
    # Regex to find standalone phs ID (e.g., phs123456) not part of a URL
    phs_pattern = r'\b(phs\d{6})\b(?![^<]*<\/a>)'
    phs_replacement = r'<a href="https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=\1" target="_blank">\1</a>'

    # Regex to find URLs
    url_pattern = r'(https?://[^\s]+)'
    url_replacement = r'<a href="\1">\1</a>'

    # First, replace URLs with hyperlinks
    text = re.sub(url_pattern, url_replacement, text)

    # Then, replace standalone phs IDs with hyperlinks
    text = re.sub(phs_pattern, phs_replacement, text)

    return text

@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.form['message']
    api_url = 'https://koios-llama.apps.renci.org/dug-qa/invoke'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = {
        "input": {
            "question": user_message
        },
        "config": {},
        "kwargs": {}
    }

    # Add a unique query parameter to prevent caching
    unique_url = f"{api_url}?_={int(time.time())}"

    logging.debug(f"Payload being sent to API: {payload}")

    try:
        response = requests.post(unique_url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        logging.debug(f"Response received: {response.json()}")

        bot_response = response.json().get('output', {}).get('result', 'Sorry, I did not understand that.')
        bot_response = add_hyperlink(bot_response)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        bot_response = 'Sorry, there was an error processing your request.'
    except Exception as err:
        logging.error(f"Other error occurred: {err}")
        bot_response = 'Sorry, there was an error processing your request.'

    return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)
