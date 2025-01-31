import logging
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import openai
import pyttsx3
import time
from threading import Thread

# Initialize the Flask app
app = Flask(__name__)

# Enable CORS for all routes, allowing all origins (you can restrict to specific domains)
CORS(app, resources={r"/*": {"origins": "*"}})

# Flask secret key for session management
app.secret_key = 'your_secret_key'

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Set your OpenAI API key (Make sure to replace it with your actual API key)
API_KEY = "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"
openai.api_key = API_KEY

ASSISTANT_ID = "asst_QIz5kji53tTMES43YeZu58pk"  # Replace with your actual assistant ID

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Inactivity tracker
last_interaction_time = time.time()  # Track the time of last user interaction
inactivity_delay = 90  # Set the inactivity delay to 90 seconds (1.5 minutes)
inactivity_message = "Wa'alaikumussalam Warahmatullahi Wabarakatuh"

# Chat endpoint with session for history
@app.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        global last_interaction_time
        # Reset the inactivity timer whenever there's user input
        last_interaction_time = time.time()

        # Get the request data
        data = request.json
        if not data:
            logging.error("No JSON data provided in request")
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_input = data.get('message')
        use_tts = data.get('use_tts', False)
        need_hadith = data.get('need_hadith', False)

        if not user_input:
            logging.error("No message provided in the request")
            return jsonify({"error": "No message provided"}), 400

        # Log the user input
        logging.info(f"Received user input: {user_input}")

        # Generate a general response from OpenAI
        general_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Kamu adalah asisten muslim yang menjawab pertanyaan di awali dengan Bismillahirrahmanirrahim."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1000
        )

        # Ensure 'choices' exist in the response
        if 'choices' not in general_response or len(general_response['choices']) == 0:
            logging.error("No valid response from OpenAI")
            return jsonify({"error": "No valid response from AI"}), 500

        response_message = general_response['choices'][0]['message']['content'].strip()

        # Log the response message
        logging.info(f"Response from OpenAI: {response_message}")

        # Determine if the response should include a Hadith
        if need_hadith:
            hadith_content = "The Prophet Muhammad (peace be upon him) said: 'The best of you are those who have the best manners and character.' (Sahih Bukhari)"
            response_message += f"\n\nRelated Hadith: {hadith_content}"
        
        # Text-to-Speech (TTS) if requested
        if use_tts:
            speak_message(response_message)

        # Save chat history in session (if needed)
        if 'chat_history' not in session:
            session['chat_history'] = []
        session['chat_history'].append({'user': user_input, 'bot': response_message})

        # Return the response along with page type
        return jsonify({
            "response": response_message,
            "assistant_id": ASSISTANT_ID
        })

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
