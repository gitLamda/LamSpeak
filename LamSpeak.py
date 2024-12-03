import streamlit as st
import speech_recognition as sr
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import re

# Initialize session state
if "is_listening" not in st.session_state:
    st.session_state.is_listening = False
if "recognized_text" not in st.session_state:
    st.session_state.recognized_text = []  # Store recognized phrases
if "start_time" not in st.session_state:
    st.session_state.start_time = None  # Track session duration

# Google Sheets setup
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("ultra-cinema-443204-r8-f4e7d0c0f166.json", scope)
    client = gspread.authorize(creds)
    return client

def extract_spreadsheet_id(url):
    """Extract the spreadsheet ID from the Google Sheets URL."""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    else:
        return None

def save_to_google_sheets(sheet_url, cell):
    try:
        client = authenticate_google_sheets()
        spreadsheet_id = extract_spreadsheet_id(sheet_url)
        if not spreadsheet_id:
            st.write("Invalid Google Sheets URL. Please provide a valid URL.")
            return

        sheet = client.open_by_key(spreadsheet_id).sheet1
        full_text = " ".join(st.session_state.recognized_text)
        sheet.update(cell, [[full_text]])
        st.write(f"All text saved to cell '{cell}': {full_text}")
    except gspread.exceptions.APIError as e:
        st.write(f"API Error: {e}")
    except PermissionError:
        st.write("Permission Error: Ensure the Service Account has access to the Google Sheet.")
    except Exception as e:
        st.write(f"Unexpected Error: {e}")


def start_listening(chunk_duration=60):
    """Continuously listen to speech in chunks."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening... Speak now.")
        recognizer.adjust_for_ambient_noise(source)
        while st.session_state.is_listening:
            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=chunk_duration)
                text = recognizer.recognize_google(audio, language="si-LK")
                st.session_state.recognized_text.append(text)
                st.write(f"Recognized: {text}")
                st.session_state.start_time = st.session_state.start_time or time.time()
                elapsed_time = time.time() - st.session_state.start_time
                st.write(f"Session Duration: {elapsed_time // 60:.0f} minutes {elapsed_time % 60:.0f} seconds")
            except sr.UnknownValueError:
                st.write("Could not understand the audio. Please continue speaking.")
            except sr.RequestError as e:
                st.write(f"Error with Google API: {e}")
                break

# Streamlit UI
st.title("Aqua Speech to Text (Sinhala)")

sheet_url = st.text_input("Google Sheets URL:")
cell = st.text_input("Cell (e.g., A1):")

chunk_duration = st.slider("Chunk Duration (seconds)", 30, 300, 60)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Start Listening") and not st.session_state.is_listening:
        st.session_state.is_listening = True
        st.session_state.start_time = None  # Reset session timer

with col2:
    if st.button("Pause Listening"):
        st.session_state.is_listening = False
        st.write("Paused. You can resume or stop.")

with col3:
    if st.button("Stop and Save"):
        st.session_state.is_listening = False
        if sheet_url and cell:
            save_to_google_sheets(sheet_url, cell)
        else:
            st.write("Please provide a valid sheet URL and cell.")

# Real-time transcription display
if st.session_state.recognized_text:
    st.text_area("Transcribed Text", value=" ".join(st.session_state.recognized_text), height=200)

# Listening loop in the background
if st.session_state.is_listening:
    start_listening(chunk_duration)