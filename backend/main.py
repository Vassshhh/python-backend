from flask import Flask, request, jsonify, session
from flask_cors import CORS
import openai
import pyttsx3
import time
from threading import Thread

# Initialize the Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Set your OpenAI API key directly (Not recommended to hardcode for production)
API_KEY = "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"
openai.api_key = API_KEY

ASSISTANT_ID = "asst_QIz5kji53tTMES43YeZu58pk"  # Replace with your actual assistant ID

# Inactivity tracker
last_interaction_time = time.time()  # Track the time of last user interaction
inactivity_delay = 90  # Set the inactivity delay to 90 seconds (1.5 minutes)
inactivity_message = "Wa'alaikumussalam Warahmatullahi Wabarakatuh"

# Function to check inactivity and send the inactivity message
def inactivity_check():
    global last_interaction_time
    current_time = time.time()
    if current_time - last_interaction_time > inactivity_delay:
        # Send the inactivity message
        send_inactivity_message()
        # Reset the last interaction time after sending the inactivity message
        last_interaction_time = current_time

# Function to send the inactivity message (Text-to-Speech handled in the same thread)
def send_inactivity_message():
    response_message = inactivity_message
    speak_message(response_message)

# Function to perform the text-to-speech operation
def speak_message(message):
    def run_tts():
        engine.say(message)
        engine.runAndWait()

    # Start TTS in a new thread to avoid blocking the main thread
    tts_thread = Thread(target=run_tts)
    tts_thread.start()
    tts_thread.join()  # Ensure that the thread completes before moving forward

# Timer to check inactivity every 10 seconds
def start_inactivity_timer():
    while True:
        inactivity_check()
        time.sleep(10)  # Check every 10 seconds

# Start the inactivity timer in a separate thread to avoid blocking Flask server
inactivity_timer_thread = Thread(target=start_inactivity_timer)
inactivity_timer_thread.daemon = True  # This will allow the thread to exit when the main program exits
inactivity_timer_thread.start()

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
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_input = data.get('message')
        use_tts = data.get('use_tts', False)
        need_hadith = data.get('need_hadith', False)

        if not user_input:
            return jsonify({"error": "No message provided"}), 400

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
            return jsonify({"error": "No valid response from AI"}), 500

        response_message = general_response['choices'][0]['message']['content'].strip()

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

        # Determine if the response should go to the Hadith or General page
        page_type = "general" if not need_hadith else "hadith"

        # Return the response along with page type
        return jsonify({
            "response": response_message,
            "page_type": page_type,  # Indicates if this response is for a general page or hadith page
            "assistant_id": ASSISTANT_ID
        })

    except Exception as e:
        # Return an error message with the exception details
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Hadith endpoint (Optional: can be used for fetching top hadiths separately)
@app.route('/hadiths', methods=['POST'])
def get_top_hadiths():
    # Simulate fetching top 5 hadiths based on user query
    top_hadiths = [
        "Hadith 1: Narrated by...",
        "Hadith 2: Narrated by...",
        "Hadith 3: Narrated by...",
        "Hadith 4: Narrated by...",
        "Hadith 5: Narrated by..."
    ]
    return jsonify({'hadiths': top_hadiths})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
