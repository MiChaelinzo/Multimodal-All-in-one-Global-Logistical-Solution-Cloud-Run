# --- Add necessary imports at the top ---
import streamlit as st
import google.generativeai as genai
import io
import os
import time
import base64
import json # For trace data
from PIL import Image, UnidentifiedImageError # Added UnidentifiedImageError
import pypdf
from docx import Document as DocxDocument # Use alias to avoid conflict if needed
from fpdf import FPDF
import smtplib
import ssl
from email.mime.text import MIMEText
from urllib.parse import quote # To safely create mailto links if needed (optional)
import pandas as pd # For reading Excel/CSV

# +++ Imports for URL fetching and parsing +++
import requests
from bs4 import BeautifulSoup
# +++ End of new imports +++

# +++ Imports for News Feed Mode +++
from datetime import datetime
try:
    from newsapi import NewsApiClient
    newsapi_available = True
except ImportError:
    newsapi_available = False
# +++ End of News Feed imports +++

# --- Check and Import Optional Libraries ---
# ... (rest of your imports)
# --- Check and Import Optional Libraries ---

pandas_available = False
try:
    import pandas as pd
    pandas_available = True
    # Check for the necessary Excel engine
    try:
        import openpyxl
        # You might not need to explicitly set a flag for openpyxl
        # if pandas can find it automatically, but checking can be useful.
        print("openpyxl engine found for Pandas.")
    except ImportError:
         st.sidebar.caption("`openpyxl` not found. Needed for .xlsx files. `pip install openpyxl`")
except ImportError:
    st.sidebar.caption("`pandas` not found. Marketing Email Tool disabled. `pip install pandas`")

gtts_available = False
try:
    from gtts import gTTS
    gtts_available = True
except ImportError:
    st.sidebar.caption("gTTS not found, TTS disabled. `pip install gTTS`") # Notify in sidebar

sr_available = False
try:
    import speech_recognition as sr
    sr_available = True
except ImportError:
    st.sidebar.caption("SpeechRecognition not found, Voice disabled. `pip install SpeechRecognition`")

webrtc_available = False
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
    import av # Required by streamlit-webrtc for processing
    webrtc_available = True
except ImportError:
    st.sidebar.caption("streamlit-webrtc/av not found, Webcam/Screen/Picture disabled. `pip install streamlit-webrtc av`")

audiorecorder_available = False
try:
    from audiorecorder import audiorecorder
    audiorecorder_available = True
except ImportError:
    st.sidebar.caption("audiorecorder not found, Voice widget disabled. `pip install streamlit-audiorecorder`")

# Imports for potential future file types (keep commented if not used yet)
# pandas_available = False
# try:
#     import pandas as pd
#     pandas_available = True
# except ImportError:
#     pass
# openpyxl_available = False
# try:
#     import openpyxl
#     openpyxl_available = True
# except ImportError:
#     pass
# moviepy_available = False
# try:
#     import moviepy.editor as mp
#     moviepy_available = True
# except ImportError:
#     pass


# --- Configuration ---
st.set_page_config(page_title="World Movers AI-Agent Assistant", page_icon="🚚", layout="wide")

# --- Apply custom CSS ---
# (Keep your existing CSS)
st.markdown(
    """
<style>
    /* Import Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inconsolata:wght@400;700&display=swap');

    body {
        font-family: 'Roboto', sans-serif;
        color: #EAEAEA;
        background-color: #1C2833; /* Fallback color */
    }

    .stApp {
        /* Background Image Setup */
        background: linear-gradient(rgba(28, 40, 51, 0.85), rgba(23, 32, 42, 0.95)), /* Adjusted Overlay Opacity */
                    url('https://i.imgur.com/UQrlUCg.png');
        background-size: contain; /* Ensure entire image is visible */
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* Titles & Headers */
    h1 {
        font-size: 2.8em; font-family: 'Roboto', sans-serif; font-weight: 700;
        color: #5DADE2; text-align: center; margin-bottom: 30px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    h2, h3, h4, h5, h6 {
        font-family: 'Roboto', sans-serif; color: #A9CCE3; font-weight: 400;
        margin-top: 20px; margin-bottom: 10px;
    }
    h2 { font-size: 1.8em; } h3 { font-size: 1.4em; }

    /* General Text & Links */
    p, div, textarea, input, select, span, li, label {
        color: #D5DBDB; font-family: 'Roboto', sans-serif; font-size: 1em; line-height: 1.6;
    }
    a { color: #5DADE2; text-decoration: none; transition: color 0.2s ease; }
    a:hover { color: #85C1E9; text-decoration: underline; }

    /* Buttons */
    .stButton>button {
        font-family: 'Roboto', sans-serif; font-weight: bold; color: #FFFFFF;
        background-color: #5DADE2; border: 1px solid #5DADE2;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
        transition: background-color 0.2s ease, box-shadow 0.2s ease, transform 0.1s ease;
        padding: 10px 20px; border-radius: 4px; margin: 5px 0;
        cursor: pointer; /* Ensure pointer cursor */
    }
    .stButton>button:hover { background-color: #3498DB; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); transform: translateY(-1px); }
    .stButton>button:active { background-color: #2E86C1; transform: translateY(0px); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
    .stButton>button:disabled {
         background-color: #4E6E81; border-color: #4E6E81; color: #97A4AF; cursor: not-allowed;
         opacity: 0.7;
    }
     /* Specific button styling for primary actions */
    .stButton>button[kind="primary"] {
        background-color: #2ECC71; border-color: #2ECC71;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #27AE60; border-color: #27AE60;
    }
    .stButton>button[kind="primary"]:disabled {
        background-color: #4a7c5c; border-color: #4a7c5c;
    }

    /* Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input,
    .stDateInput>div>div>input, .stTimeInput>div>div>input {
        color: #EAEAEA; background-color: #2C3E50; border: 1px solid #4E6E81;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1); font-family: 'Roboto', sans-serif;
        border-radius: 4px; padding: 10px; transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus, .stNumberInput>div>div>input:focus,
    .stDateInput>div>div>input:focus, .stTimeInput>div>div>input:focus {
        border-color: #5DADE2;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1), 0 0 0 2px rgba(93, 173, 226, 0.3);
        outline: none;
    }
    .stTextInput>div>div>input:disabled, .stTextArea>div>div>textarea:disabled, .stNumberInput>div>div>input:disabled {
         background-color: #212F3C; color: #7F8C8D;
    }

    /* Selectbox & Radio */
     .stSelectbox>div>div>div, .stRadio>div {
        color: #EAEAEA; background-color: #2C3E50; border: 1px solid #4E6E81;
        border-radius: 4px; font-family: 'Roboto', sans-serif; padding: 5px; /* Adjust padding */
     }
     /* Radio button label styling */
    .stRadio label { padding-left: 5px; font-size: 0.95em;}


    /* Dataframes */
    .stDataFrame { background-color: #2C3E50; border: 1px solid #4E6E81; border-radius: 4px; overflow: hidden; }
    .stDataFrame thead th { background-color: #1F618D; color: #FFFFFF; font-family: 'Roboto', sans-serif; font-weight: bold; text-align: left; padding: 10px; }
    .stDataFrame tbody tr td { color: #D5DBDB; font-family: 'Inconsolata', monospace; border-color: #4E6E81; padding: 8px 10px; }
    .stDataFrame tbody tr:nth-child(even) { background-color: #34495E; }

    /* Sidebar */
    .stSidebar { background-color: #212F3C; border-right: 1px solid #4E6E81; padding: 20px; }
    .stSidebar h2, .stSidebar h3 { color: #A9CCE3; }
    .stSidebar p, .stSidebar li, .stSidebar a, .stSidebar label, .stSidebar .stRadio label { color: #BDC3C7; } /* Ensure radio labels inherit color */
    .stSidebar .stButton>button { background-color: #2980B9; border-color: #2980B9; }
    .stSidebar .stButton>button:hover { background-color: #2471A3; }

    /* Code Block */
    .stCodeBlock { border: 1px solid #4E6E81; border-radius: 4px; background-color: #17202A !important; margin: 15px 0; }
    .stCodeBlock code { color: #BDC3C7; font-family: 'Inconsolata', monospace !important; font-size: 0.95em !important; background: transparent !important; }

    /* Divider */
    hr { border-top: 1px solid #4E6E81; margin: 25px 0; }

    /* Alert Boxes */
    div[data-testid="stAlert"] { font-family: 'Roboto', sans-serif; border-radius: 4px; border-width: 1px; border-style: solid; padding: 15px; margin: 15px 0; color: #FFFFFF; background-color: rgba(0,0,0,0.2); }
    div[data-testid="stAlert"] strong { font-weight: bold; }
    div[data-testid="stAlert"][data-baseweb="alert"][role="alert"].st-ae { background-color: rgba(39, 174, 96, 0.2); border-color: #27AE60; color: #DFF0D8; } /* Success */
    div[data-testid="stAlert"][data-baseweb="alert"][role="alert"].st-b7 { background-color: rgba(52, 152, 219, 0.2); border-color: #3498DB; color: #D6EAF8; } /* Info */
    div[data-testid="stAlert"][data-baseweb="alert"][role="alert"].st-b6 { background-color: rgba(231, 76, 60, 0.2); border-color: #E74C3C; color: #FADBD8; } /* Error */
    div[data-testid="stAlert"][data-baseweb="alert"][role="alert"].st-b5 { background-color: rgba(243, 156, 18, 0.2); border-color: #F39C12; color: #FCF3CF; } /* Warning */

    /* Chat Messages (Main Chat Area) */
    div[data-testid="stChatMessage"] { padding: 12px 15px; border-radius: 8px; margin-bottom: 10px; max-width: 85%; box-shadow: 0 1px 3px rgba(0,0,0,0.1); line-height: 1.5; }
    div[data-testid="stChatMessage"][data-testid*="avatar-assistant"] { background-color: #2C3E50; color: #EAEAEA; margin-left: 0; margin-right: auto; } /* Assistant */
    div[data-testid="stChatMessage"]:not([data-testid*="avatar-assistant"]) { background-color: #5DADE2; color: #FFFFFF; margin-right: 0; margin-left: auto; } /* User */

     /* Chat Messages (Screen Share Area - slightly different styling) */
    .screen-chat-container { /* Apply styles directly to the container */
         /* Add any specific container styles if needed */
    }
    .screen-chat-container div[data-testid="stChatMessage"] { max-width: 95%; margin-bottom: 8px; }
    .screen-chat-container div[data-testid="stChatMessage"][data-testid*="avatar-assistant"] { background-color: #34495E; } /* Darker assistant */
    .screen-chat-container div[data-testid="stChatMessage"]:not([data-testid*="avatar-assistant"]) { background-color: #5DADE2; } /* Same user */


    /* TTS Player and Download Buttons Styling */
    .stAudio { height: 45px; margin-top: 5px; filter: saturate(0.8) brightness(1.1); } /* Subtle style for audio */
    .download-buttons { display: flex; gap: 10px; margin-top: 8px; align-items: center;}
    .download-buttons .stDownloadButton button {
        font-size: 0.8em !important; padding: 5px 10px !important; min-height: 30px; /* Ensure buttons have minimum height */
        background-color: #4E6E81 !important; border-color: #4E6E81 !important;
        color: #FFFFFF !important; transition: background-color 0.2s ease, border-color 0.2s ease;
        display: flex; align-items: center; justify-content: center; /* Center text */
    }
    .download-buttons .stDownloadButton button:hover {
         background-color: #5DADE2 !important; border-color: #5DADE2 !important;
    }

    /* Style for context summary in sidebar */
    .context-summary {
        font-size: 0.9em;
        color: #BDC3C7;
        background-color: #2C3E50;
        padding: 10px;
        border-radius: 4px;
        margin-top: 10px;
        border: 1px dashed #4E6E81;
    }
    .context-summary strong { color: #A9CCE3; }
    .context-summary ul { list-style-type: none; padding-left: 5px; margin-bottom: 5px;}
    .context-summary li { margin-bottom: 3px; }

    /* Instructions Box Styling (from DocuNexus) */
    .instructions-box {
        background-color: rgba(44, 62, 80, 0.8); /* Slightly transparent dark blue */
        border: 1px solid #4E6E81;
        border-left: 5px solid #5DADE2; /* Accent color */
        padding: 15px 20px;
        margin: 15px 0;
        border-radius: 5px;
        color: #D5DBDB; /* Light text color */
        font-family: 'Roboto', sans-serif;
    }
    .instructions-box h3 {
        color: #A9CCE3; /* Lighter blue for headings */
        margin-top: 0;
        margin-bottom: 10px;
        border-bottom: 1px solid #4E6E81;
        padding-bottom: 5px;
    }
    .instructions-box ol, .instructions-box ul {
        padding-left: 20px;
        margin-bottom: 10px;
    }
    .instructions-box li {
        margin-bottom: 5px;
        line-height: 1.5;
    }
    .instructions-box p {
        margin-bottom: 10px;
        line-height: 1.5;
    }
    .instructions-box strong {
        color: #A9CCE3; /* Lighter blue for emphasis */
        font-weight: bold;
    }
    .instructions-box code {
        background-color: #1C2833; /* Darker code background */
        color: #FAD7A0; /* Light orange for code */
        padding: 2px 5px;
        border-radius: 3px;
        font-family: 'Inconsolata', monospace;
    }
    .instructions-box a {
        color: #85C1E9; /* Link color */
    }
    .instructions-box a:hover {
        color: #AED6F1;
    }
     /* Custom Button within Instructions Box */
    .instructions-box button {
        background-color: #5DADE2; color: #FFFFFF; border: 1px solid #5DADE2;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
        padding: 8px 15px; border-radius: 4px; cursor: pointer;
        font-family: 'Roboto', sans-serif; font-weight: bold;
        transition: background-color 0.2s ease, box-shadow 0.2s ease;
    }
    .instructions-box button:hover {
        background-color: #3498DB; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    /* Webcam/Screen Share Styling */
     .webrtc-container video {
          border: 2px solid #5DADE2;
          border-radius: 5px;
          width: 100%; /* Ensure video fills container */
          background-color: #17202A; /* Dark background for video area */
      }
     /* Status text below webcam/screen */
     .media-status {
         font-size: 0.9em;
         color: #A9CCE3;
         text-align: center;
         margin-top: 5px;
         min-height: 1.2em; /* Prevent layout shift */
     }

    /* +++ News Feed Styling +++ */
    .scrollable-tab-content {
        max-height: 800px; /* Adjust height as needed */
        overflow-y: auto;
        padding-right: 15px; /* Add padding for scrollbar */
        margin-top: 15px;
    }
    .tab-description {
        font-size: 1.05em;
        color: #A9CCE3;
        margin-bottom: 20px;
    }
    .news-item {
        border-bottom: 1px solid #4E6E81;
        padding-bottom: 15px;
        margin-bottom: 15px;
    }
    .news-item h3 {
        margin-top: 5px;
        margin-bottom: 5px;
    }
    .news-item h3 a {
        font-size: 1.1em;
        font-weight: bold;
    }
    .news-item p {
        font-size: 0.95em;
        color: #BDC3C7;
        line-height: 1.5;
    }
    .news-date {
        font-size: 0.85em;
        color: #85929E;
    }
    /* --- End of News Feed Styling --- */

</style>
    """,
    unsafe_allow_html=True,
)

# +++ URLs for External Knowledge +++
TERMS_URL = "https://worldmovers.net/terms-and-conditions"
PDF_URL = "https://storage.googleapis.com/wzukusers/user-14326606/documents/fc43554019b84a74b3f500e1a4ef2b33/ARE%20YOU%20NEW.pdf"
IMPORTER_DOCX_PATH = "data/importer.docx" # <--- ADDED FILE PATH

# +++ End of URLs and Paths +++

# --- Configuration for Google Cloud Run ---
# Load all secrets from environment variables.
# In Cloud Run, these will be securely injected from Secret Manager.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT_STR = os.environ.get("SMTP_PORT")
# +++ Add NewsAPI Key Configuration +++
NEWSAPI_API_KEY = os.environ.get("NEWSAPI_API_KEY")


# --- Validation and Setup ---

# Create a list of any variables that were not found.
missing_vars = []
if not GEMINI_API_KEY:
    missing_vars.append("GEMINI_API_KEY")
if not SENDER_EMAIL:
    missing_vars.append("SENDER_EMAIL")
if not SENDER_PASSWORD:
    missing_vars.append("SENDER_PASSWORD")
if not SMTP_SERVER:
    missing_vars.append("SMTP_SERVER")
if not SMTP_PORT_STR:
    missing_vars.append("SMTP_PORT")
# Note: NEWSAPI_API_KEY is optional, so we don't add it to missing_vars.
# The News Feed mode will handle its absence gracefully.

# If the list is not empty, display an error and stop the application.
if missing_vars:
    st.error(f"🚨 **Cloud Config Error:** The following environment variable(s) are not set: {', '.join(missing_vars)}. Please ensure they are correctly configured in your Google Cloud Run service.", icon="⚙️")
    st.stop()

# --- Type Conversion and Final Configuration ---

try:
    # Convert SMTP_PORT to an integer.
    SMTP_PORT = int(SMTP_PORT_STR)

    # Configure the Gemini API client.
    genai.configure(api_key=GEMINI_API_KEY)

    # Placeholder for Azure Keys if you add Azure modes later
    azure_enabled = False # Keep Azure disabled for now unless configured

    # Optional: Display a success message for easier debugging.
    # st.success("Application configured successfully.")

except ValueError:
    st.error(f"🚨 **Cloud Config Error:** The SMTP_PORT environment variable ('{SMTP_PORT_STR}') must be a valid number.", icon="⚙️")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during service configuration: {e}")
    st.stop()


# --- Select the Gemini Model (Ensure it's Multimodal) ---
# Updated recommended model as of late 2024 / early 2025
MODEL_NAME = "gemini-2.5-flash-preview-05-20" # Check Google AI documentation for the latest recommended multimodal model
DISPLAY_MODEL_NAME = "gemini-2.5-flash-preview-05-20" # User-friendly name
# Vision model for image-specific tasks if needed (often same as base multimodal)
VISION_MODEL_NAME = MODEL_NAME
DEEP_THINK_MODEL_NAME = MODEL_NAME # Use the same capable model

# --- System Prompt (Updated for importer.docx) ---
SYSTEM_PROMPT = f"""
You are an advanced AI-Agent assistant for World Movers Phils Inc. (worldmovers.net / worldmovers.com.ph), powered by Einstein Studio (BYOM). You can interact with users through text chat, analyze uploaded documents/images, understand voice commands, analyze live camera feeds, and interpret shared screen content.

**Identity:** "I am an AI agent for World Movers Phils Inc., designed to assist with logistics inquiries using text, voice, image, and screen analysis."

**Knowledge Base:** You have access to the following internal documents:
1.  The official World Movers Terms and Conditions (from worldmovers.net).
2.  A document titled 'ARE YOU NEW.pdf' (guidance for new clients).
3.  An internal document named 'importer.docx' (containing specific procedures, data, or importer-related information). 

Use this information FIRST when answering relevant questions about policies, procedures, terms, or internal data. State the source if directly quoting or summarizing (e.g., "According to the Terms and Conditions...", "Based on the 'ARE YOU NEW.pdf' document...", "As per the {os.path.basename(IMPORTER_DOCX_PATH)} file...").

**Primary Goal:** Assist users professionally and efficiently with their logistics needs for World Movers, utilizing the provided context (text, files, images, voice transcript, camera/screen feed), **internal knowledge base documents (Terms, PDF, importer.docx)** appropriately.

**Core Capabilities based on Interaction Mode:**
- **Chat Assistant Mode:** Answer service questions (Air/Sea/Domestic Freight, Customs, Warehousing, Trucking), **answer questions based on the internal knowledge base (Terms & Conditions, 'ARE YOU NEW.pdf', 'importer.docx')**, initiate quote requests by gathering details (Origin, Destination, Cargo Info, Contact), provide general support. Refer to context from sidebar uploads/captures **and the internal knowledge base**.
- **Document/Image Analysis Mode:** Analyze uploaded documents (PDF, DOCX, TXT) or images (JPG, PNG, WEBP, etc.) based on the user's query. Extract information, summarize, compare, answer questions about the content. State the source ("Based on the uploaded PDF..."). (Note: This mode primarily focuses on *user-uploaded* files, less on the internal base.)
- **Voice Command Mode:** Transcribe the user's spoken command and respond accordingly, potentially drawing on the **internal knowledge base** if relevant to the command.
- **Live Webcam Analysis Mode:** Describe objects/scenes relevant to logistics. (Less likely to use internal docs).
- **Screen Analysis Mode:** Analyze the user's shared screen based on their questions. (Less likely to use internal docs).
- **Take Picture Analysis Mode:** Analyze a captured picture based on the user's prompt. (Less likely to use internal docs).

**Quote Handling Procedure:**
1.  Gather necessary details (Service, Origin, Destination, Cargo Description [commodity, weight, dimensions/volume], Contact Person/Email/Phone).
2.  Summarize collected info clearly.
3.  State you will **attempt to forward the request to the World Movers quoting team via email.**
4.  **Do NOT list recipient emails.** Use phrasing like: "I will forward this to our quoting team..."

**AI Thoughts / Reasoning:** When performing analysis or answering complex questions (especially using internal docs), add your reasoning under '***AI Thoughts:***'.

**Limitations:**
- Cannot perform actions outside the World Movers domain.
- Cannot guarantee real-time data access (e.g., live tracking) unless searching web.
- Cannot provide binding quotes (human team does).
- Email forwarding may fail. Inform the user if it does.
- Analysis quality depends on input quality.
- **Knowledge from internal documents (Terms, PDF, importer.docx) is based on the text extracted at the start of the session and may not reflect instantaneous updates to source files/URLs.**

**Tone:** Professional, helpful, clear, concise. Reference sources when using internal knowledge.
"""


# --- Initialize the Generative Models ---
try:
    # Generation Config (Adjust as needed)
    generation_config = genai.types.GenerationConfig(
        temperature=0.7,
        # max_output_tokens=8192, # Uncomment and set if needed for Pro 1.5
        # top_p=0.9, # Optional sampling parameters
        # top_k=40   # Optional sampling parameters
    )
    # Safety Settings (Adjust cautiously - loosening can allow harmful content)
    # Using default safety settings is recommended unless specific issues arise
    safety_settings = {
        # Example: Block more strictly for harassment
        # genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        # Default: BLOCK_MEDIUM_AND_ABOVE for HATE_SPEECH, SEXUALLY_EXPLICIT, DANGEROUS_CONTENT
    }

    # Initialize the model instance
    model = genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    # Use the same configured model instance for different conceptual tasks
    vision_model = model
    deep_think_model = model

except Exception as e:
    st.error(f"Fatal Error: Could not initialize Google Gemini model ({MODEL_NAME}). Please check API key, model name, and configuration. Details: {e}")
    st.stop()

# --- RTC Configuration for WebRTC ---
RTC_CONFIG = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})

# --- Helper Functions ---

# +++ Functions to Fetch and Process External Knowledge +++
# ... (fetch_url_content and fetch_and_process_pdf remain the same) ...

@st.cache_data(ttl=3600) # Cache fetched data for 1 hour to avoid refetching constantly
def fetch_url_content(url):
    """Fetches and extracts text content from a generic URL (HTML)."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        # Check content type - simple check for HTML
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            # If it's plain text, return it directly
            if 'text/plain' in content_type:
                return response.text
            return f"[Error: URL {url} did not return HTML or plain text content (Content-Type: {content_type})]"

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Attempt to find the main content area ---
        # Inspect worldmovers.net/terms-and-conditions (April 2025 view)
        # The main content seems to be within <div class="page-content">
        main_content = soup.find('div', class_='page-content')

        # Fallbacks if the primary selector fails
        if not main_content:
             main_content = soup.find('article')
        if not main_content:
             main_content = soup.find('main')
        if not main_content:
            main_content = soup.body # Last resort, likely includes noise

        if main_content:
            # Remove common noise like headers, footers, navs, scripts, styles, forms
            for element in main_content(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'button', 'input', 'select', 'textarea']):
                element.decompose()
            # Get text, trying to preserve paragraphs and clean up whitespace
            text = main_content.get_text(separator='\n', strip=True)
            # Further clean up excessive newlines
            text = '\n'.join(line for line in text.splitlines() if line.strip())
            if not text:
                return f"[Error: Extracted text from main content area of {url} was empty after cleaning]"
            return text
        else:
            # This case should be rare if soup.body is used as fallback
            return f"[Error: Could not find any main content area or body in HTML structure of {url}]"

    except requests.exceptions.Timeout:
        return f"[Error fetching URL {url}: Connection timed out]"
    except requests.exceptions.RequestException as e:
        return f"[Error fetching URL {url}: {e}]"
    except Exception as e:
        return f"[Error processing HTML from {url}: {e}]"

@st.cache_data(ttl=3600) # Cache fetched data for 1 hour
def fetch_and_process_pdf(url):
    """Fetches a PDF from a URL and extracts text using existing function."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=45) # Longer timeout for potentially larger PDFs
        response.raise_for_status()

        # Check content type - simple check for PDF
        if 'application/pdf' not in response.headers.get('Content-Type', '').lower():
             return f"[Error: URL {url} did not return PDF content (Content-Type: {response.headers.get('Content-Type', 'N/A')})]"

        # Use the existing PDF extraction function
        pdf_text = extract_text_from_pdf(response.content) # Assumes it takes bytes
        if not pdf_text or pdf_text.startswith("[Error") or pdf_text.startswith("[Info: No text"):
             # Return the specific info/error message from the extractor
             return pdf_text if pdf_text else "[Error: Unknown error extracting text from the PDF]"
        return pdf_text
    except requests.exceptions.Timeout:
         return f"[Error fetching PDF {url}: Connection timed out]"
    except requests.exceptions.RequestException as e:
        return f"[Error fetching PDF {url}: {e}]"
    except Exception as e:
        # Catch errors from extract_text_from_pdf or other issues
        return f"[Error processing PDF from {url}: {e}]"
# +++ Function to Load Local DOCX +++
# No caching needed here as it's read once per session into state
def load_local_docx_content(file_path):
    """Reads and extracts text from a local DOCX file."""
    try:
        # Check if file exists first
        if not os.path.exists(file_path):
             return f"[Error: Local document not found at path: {file_path}]"
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        if not file_bytes:
            return f"[Info: Local document '{os.path.basename(file_path)}' is empty]"
        # Reuse the existing docx extraction function
        docx_text = extract_text_from_docx(file_bytes)
        # Return the extracted text or the error/info message from the extractor
        return docx_text
    except FileNotFoundError:
         return f"[Error: Local document not found at path: {file_path}]"
    except IOError as e:
        return f"[Error: Could not read local document '{os.path.basename(file_path)}': {e}]"
    except Exception as e:
        # Catch potential errors from extract_text_from_docx or other issues
        return f"[Error processing local document '{os.path.basename(file_path)}': {type(e).__name__} - {e}]"

# --- News Feed Helper Function ---
@st.cache_data(ttl=1800) # Cache for 30 minutes
def fetch_news_from_newsapi(api_key, keywords):
    """
    Fetches news from NewsAPI for a list of keywords and performs
    a very basic sentiment analysis.
    """
    if not newsapi_available:
        return [{"type": "error", "content": "NewsAPI library not installed."}]
    if not api_key:
        return [{"type": "error", "content": "NewsAPI API key is not configured."}]

    newsapi = NewsApiClient(api_key=api_key)
    query_string = " OR ".join(f'"{k}"' for k in keywords)

    try:
        # Fetch top headlines or everything - 'everything' is better for specific keywords
        all_articles = newsapi.get_everything(
            q=query_string,
            language='en',
            sort_by='publishedAt',
            page_size=30 # Get a decent number of articles to filter through
        )

        if all_articles['status'] != 'ok':
            return [{"type": "error", "content": f"NewsAPI Error: {all_articles.get('message', 'Unknown error')}"}]

        processed_articles = []
        for article in all_articles['articles']:
            # Simple sentiment analysis based on keywords in title/description
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = title + " " + description
            
            # Define simple keyword sets for sentiment
            positive_words = ['success', 'launch', 'partnership', 'growth', 'adopt', 'positive', 'benefit', 'innovate']
            negative_words = ['issue', 'concern', 'regulation', 'risk', 'decline', 'problem', 'hack', 'scam', 'lawsuit', 'volatile']
            
            sentiment_score = 0
            for word in positive_words:
                if word in content:
                    sentiment_score += 1
            for word in negative_words:
                if word in content:
                    sentiment_score -= 1
            
            # Assign emoji based on score
            if sentiment_score > 0:
                sentiment = '🟢' # Positive
            elif sentiment_score < 0:
                sentiment = '🔴' # Negative
            else:
                sentiment = '⚪' # Neutral
            
            processed_articles.append({
                'title': article.get('title', 'No Title'),
                'link': article.get('url', '#'),
                'snippet': article.get('description', 'No snippet available.'),
                'date': article.get('publishedAt', 'Date unavailable').split('T')[0], # Just the date part
                'sentiment': sentiment
            })

        return processed_articles

    except Exception as e:
        return [{"type": "error", "content": f"Failed to fetch news: {e}"}]

# +++ End of Knowledge Loading Functions +++
# +++ End of new functions +++

# --- Document Processing ---
def extract_text_from_pdf(file_bytes):
    """Safely extracts text from PDF bytes using pypdf."""
    text = ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            # Attempt decryption with an empty password (common for owner-level protection)
            decrypt_status = reader.decrypt('')
            if decrypt_status == pypdf.PasswordType.NOT_DECRYPTED:
                # Failed with empty password, might need user password
                return "[Error: PDF is encrypted and requires a password]"
            elif decrypt_status == pypdf.PasswordType.INCORRECT_PASSWORD:
                # Should not happen with empty string, but handle defensively
                return "[Error: PDF encrypted - internal decryption issue]"
            # If OWNER_PASSWORD or USER_PASSWORD, proceed

        num_pages = len(reader.pages)
        for i, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            except Exception as page_err:
                # Log error for specific page but continue
                print(f"Warning: Could not extract text from PDF page {i+1}/{num_pages}: {page_err}")
                text += f"[Warning: Could not extract text from page {i+1}]\n"

        return text.strip() if text else "[Info: No text extracted from PDF (possibly image-based or empty)]"

    except pypdf.errors.PdfReadError as pdf_err:
        # More specific error for invalid PDF files
        return f"[Error: Invalid or corrupted PDF file - {pdf_err}]"
    except FileNotFoundError: # Should not happen with BytesIO, but safety
        return "[Error: PDF file not found (internal error with BytesIO)]"
    except Exception as e:
        # General catch-all for other pypdf or unexpected errors
        return f"[Error reading PDF: {type(e).__name__} - {e}]"

def extract_text_from_docx(file_bytes):
    """Safely extracts text from DOCX bytes using python-docx."""
    try:
        doc = DocxDocument(io.BytesIO(file_bytes))
        text_parts = []
        # Extract text from paragraphs
        for para in doc.paragraphs:
            if para.text.strip(): # Only add paragraphs with content
                text_parts.append(para.text)
        # Optionally, extract text from tables (basic implementation)
        for table in doc.tables:
            for row in table.rows:
                row_text = "\t".join(cell.text.strip() for cell in row.cells) # Join cells with tabs
                if row_text: # Only add non-empty rows
                    text_parts.append(row_text)

        text = "\n".join(text_parts) # Join all parts with newlines
        return text if text else "[Info: No text extracted from DOCX (empty or no text content)]"
    except ImportError:
        # Should be caught by initial checks, but good fallback
        return "[Error: DOCX processing failed - `python-docx` library not installed]"
    except Exception as e:
        # Catch errors like invalid docx format (e.g., from zipfile errors)
        return f"[Error reading DOCX: {type(e).__name__} - {e}]"

# --- Robust File Handler ---
def handle_document_upload(uploaded_file):
    """
    Handles reading content from various uploaded document types.
    Returns a dictionary: {"type": "text/image/error", "name": ..., "content": ..., "mime_type": ...}
    Content for text is string, for image is PIL Image object.
    """
    if not uploaded_file:
        return {"name": "None", "type": "error", "content": "[Error: No file provided]", "mime_type": None}

    content_data = {"name": uploaded_file.name, "type": "error", "content": "Unprocessed", "mime_type": uploaded_file.type}
    file_extension = os.path.splitext(uploaded_file.name)[1].lower() if uploaded_file.name else ""
    file_bytes = None # Read only once if needed

    try:
        file_bytes = uploaded_file.getvalue()
        if not file_bytes:
            return {**content_data, "type": "error", "content": f"[Error: Uploaded file '{uploaded_file.name}' is empty]"}

        # --- Text Documents ---
        if file_extension == ".txt":
            try:
                # Try common encodings robustly
                text = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = file_bytes.decode('latin-1')
                except UnicodeDecodeError:
                     text = file_bytes.decode('ascii', errors='ignore') # Final fallback
            content_data.update({"type": "text", "content": text if text else "[Info: Empty TXT file]"})

        elif file_extension == ".pdf":
            text = extract_text_from_pdf(file_bytes)
            content_data.update({"type": "text", "content": text})
            # Keep type as 'text' even for errors/info, the content string indicates the issue
            if "[Error" in text:
                content_data["type"] = "error" # Or maybe keep as text and let caller check? Let's mark as error.

        elif file_extension == ".docx":
            text = extract_text_from_docx(file_bytes)
            content_data.update({"type": "text", "content": text})
            if "[Error" in text:
                content_data["type"] = "error" # Mark as error

        # --- Images ---
        elif file_extension in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".heic", ".heif"]: # Added HEIC/HEIF
            try:
                img = Image.open(io.BytesIO(file_bytes))
                # Basic validation: Check if image dimensions are reasonable
                if img.width > 0 and img.height > 0:
                    # Ensure image is in a format Gemini accepts (e.g., RGB)
                    # Gemini 1.5 Pro supports various formats, conversion might not always be needed,
                    # but RGB is safe. Check docs if specific format issues arise.
                    if img.mode not in ['RGB', 'RGBA', 'L']: # Accept RGB, RGBA, Grayscale (L)
                         img = img.convert('RGB') # Convert others to RGB
                    content_data.update({"type": "image", "content": img})
                else:
                    content_data.update({"type": "error", "content": f"[Error: Invalid image dimensions (0 width or height) for {uploaded_file.name}]"})
            except UnidentifiedImageError:
                 content_data.update({"type": "error", "content": f"[Error: Cannot identify image file format for {uploaded_file.name}]"})
            except Exception as img_err:
                content_data.update({"type": "error", "content": f"[Error: Cannot load image {uploaded_file.name}: {type(img_err).__name__} - {img_err}]"})

        # --- Add other types as needed (CSV, XLSX using pandas - ensure libraries are checked) ---
        # elif file_extension == ".csv" and pandas_available:
        #     try:
        #         uploaded_file.seek(0) # Reset pointer
        #         df = pd.read_csv(io.BytesIO(file_bytes)) # Read from bytes
        #         content = df.to_string()
        #         content_data.update({"type": "text", "content": f"[CSV Content: {uploaded_file.name}]\n{content}"})
        #     except Exception as pd_err: content_data.update({"type": "error", "content": f"[CSV Error: {pd_err}]"})
        # elif file_extension == ".xlsx" and pandas_available and openpyxl_available:
        #      try:
        #          uploaded_file.seek(0)
        #          df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
        #          content = df.to_string()
        #          content_data.update({"type": "text", "content": f"[XLSX Content: {uploaded_file.name}]\n{content}"})
        #      except Exception as pd_err: content_data.update({"type": "error", "content": f"[XLSX Error: {pd_err}]"})

        else:
            content_data["content"] = f"[Error: Unsupported file type: '{file_extension}' or unknown type for '{uploaded_file.name}']"
            content_data["type"] = "error" # Ensure type is error

        return content_data

    except Exception as e:
        # Catch-all for unexpected errors during processing (e.g., getvalue() fails)
        content_data["content"] = f"[Error: General processing error for '{uploaded_file.name}': {type(e).__name__} - {e}]"
        content_data["type"] = "error" # Ensure type is error
        return content_data


# --- Audio Transcription (Needs SpeechRecognition library) ---
def transcribe_audio_bytes(audio_bytes_wav):
    """Transcribes WAV audio bytes using SpeechRecognition (Google Web Speech API)."""
    if not sr_available:
        return "[Error: SpeechRecognition library not installed. Voice input disabled.]"
    if not audio_bytes_wav:
        return "[Info: No audio data received for transcription]"

    r = sr.Recognizer()
    try:
        # Wrap the bytes in BytesIO for AudioFile compatibility
        with io.BytesIO(audio_bytes_wav) as wav_bytes_io:
             with sr.AudioFile(wav_bytes_io) as source:
                # Optional: Adjust for ambient noise (adds slight delay)
                # try:
                #     r.adjust_for_ambient_noise(source, duration=0.3)
                # except Exception as noise_err:
                #     print(f"Warning: adjust_for_ambient_noise failed: {noise_err}")

                # Configure recognizer parameters (adjust as needed)
                r.energy_threshold = 300 # Lower threshold might pick up quieter speech
                r.pause_threshold = 0.8 # Seconds of silence indicating end of phrase
                r.dynamic_energy_threshold = True # Adapt to changing noise levels

                # Record the audio data from the source
                audio_recorded = r.record(source)

        # Recognize using Google Web Speech API (requires internet)
        # Note: This has limitations (e.g., rate limits, privacy considerations)
        # Consider Whisper (offline or API) for more robust transcription if needed.
        text = r.recognize_google(audio_recorded, language='en-US') # Specify language if possible
        return text
    except sr.WaitTimeoutError:
        return "[Info: No speech detected in the audio within the timeout period]"
    except sr.UnknownValueError:
        return "[Info: Could not understand the audio - speech might be unclear or background noise too high]"
    except sr.RequestError as e:
        # Common issues: network connection, API key/quota issues (though Google Web Speech often doesn't need a key here)
        return f"[Error: Speech Recognition service request failed; {e}]"
    except Exception as e_rec:
        # Catch other potential errors during processing or recording
        return f"[Error during audio transcription: {type(e_rec).__name__} - {e_rec}]"

# --- Video/Audio Frame Processing Class (for WebRTC) ---
# Global variables for analysis throttling (simple approach)
last_analysis_time_webcam = 0
analysis_interval_webcam = 5 # Seconds between webcam analyses (adjust as needed)

last_analysis_time_screen = 0
analysis_interval_screen = 7 # Seconds between screen analyses (can be longer)

class VideoProcessor:
    """Processes video frames for webcam feed analysis."""
    def __init__(self, mode="webcam"):
        self.frame_count = 0
        self.interval = analysis_interval_webcam # Currently only webcam uses this periodic analysis
        self.mode = mode # 'webcam' or 'screen' (though screen uses callback now)
        self.is_analyzing = False # Prevent concurrent analyses
        print(f"VideoProcessor initialized for mode: {self.mode}") # Debug init

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        global last_analysis_time_webcam # Use global timer for webcam analysis

        # --- Perform analysis periodically ONLY for WEBCAM mode ---
        if self.mode == "webcam":
            current_time = time.time()
            # Check interval and if another analysis isn't already running
            if not self.is_analyzing and (current_time - last_analysis_time_webcam > self.interval):
                self.is_analyzing = True # Set flag
                last_analysis_time_webcam = current_time # Update global timer

                try:
                    img_pil = frame.to_image() # Convert frame to PIL Image
                    # Ensure image is in RGB (safe default)
                    if img_pil.mode != 'RGB':
                        img_pil = img_pil.convert('RGB')

                    # Update status immediately before blocking call
                    if "webcam_status" in st.session_state: # Check if key exists
                         st.session_state.webcam_status = "Analyzing frame..."
                    print(f"Analyzing webcam frame at {current_time:.2f}") # Debug timing

                    # Prepare contents (image + prompt)
                    prompt = "Describe the key objects, text, or activity visible in this image relevant to logistics (e.g., packages, labels, equipment, documents). If nothing relevant, describe the scene briefly. Include thoughts under '***AI Thoughts:***'."
                    contents = [prompt, img_pil]

                    # Use the globally initialized vision_model
                    response = vision_model.generate_content(
                        contents,
                        stream=False # Keep analysis simple, don't stream here
                    )
                    analysis_result_full = response.text
                    main_result = analysis_result_full
                    thoughts = ""

                    # Extract thoughts
                    if "***AI Thoughts:***" in analysis_result_full:
                        parts = analysis_result_full.split("***AI Thoughts:***", 1)
                        main_result = parts[0].strip()
                        thoughts = parts[1].strip()

                    # Update session state (check if keys exist first)
                    if "webcam_analysis_result" in st.session_state:
                        st.session_state.webcam_analysis_result = main_result
                    if "webcam_thoughts" in st.session_state:
                         st.session_state.webcam_thoughts = thoughts
                    if "webcam_status" in st.session_state:
                        st.session_state.webcam_status = f"Analysis complete ({time.strftime('%H:%M:%S')})"
                    print(f"Webcam analysis complete. Result snippet: {main_result[:50]}...") # Debug result

                except genai.types.generation_types.StopCandidateException as e:
                     # Handle blocked content during webcam analysis
                     print(f"Webcam analysis stopped by API: {e}")
                     if "webcam_status" in st.session_state: st.session_state.webcam_status = f"Analysis stopped by API ({time.strftime('%H:%M:%S')})"
                     if "webcam_analysis_result" in st.session_state: st.session_state.webcam_analysis_result = f"[Analysis Blocked by Safety Filter: {e}]"
                     if "webcam_thoughts" in st.session_state: st.session_state.webcam_thoughts = ""
                except Exception as e:
                     # Handle generic analysis errors
                     print(f"Webcam analysis failed: {type(e).__name__} - {e}")
                     if "webcam_status" in st.session_state: st.session_state.webcam_status = f"Analysis error ({time.strftime('%H:%M:%S')})"
                     if "webcam_analysis_result" in st.session_state: st.session_state.webcam_analysis_result = f"[Analysis Error: {type(e).__name__}]"
                     if "webcam_thoughts" in st.session_state: st.session_state.webcam_thoughts = ""
                finally:
                     self.is_analyzing = False # Reset flag whether success or failure

        # Return the original frame (or potentially annotated frame if desired later)
        return frame

# --- Screen Share Frame Callback ---
# Used for screen analysis mode to capture the frame when requested by chat
def screen_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    """Callback function to store the latest screen share frame in session state."""
    try:
        img = frame.to_image()
        # Ensure image is in RGB format for Gemini (safe default)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Store the PIL image in session state
        st.session_state.current_screen_frame_pil = img
        # Optional: Log capture time for debugging frequency, but can be noisy
        # print(f"Screen callback: Frame captured at {time.time():.2f}")
    except Exception as e:
        print(f"Error in screen_frame_callback converting frame: {type(e).__name__} - {e}")
        # Optionally clear the frame in session state on error to prevent using stale/bad data
        st.session_state.current_screen_frame_pil = None
    # Return the original frame for display by webrtc_streamer
    return frame


# --- Email Sending ---
def send_quote_request_email(quote_details, recipients):
    """Sends email using configured SMTP settings. Returns True on success, False on failure."""
    subject = "New Quote Request via AI-Agent Assistant"
    body = f"Quote Request Details:\n\n---\n{quote_details}\n---\n\nThis email was generated automatically by the World Movers AI-Agent Assistant."
    sender = SENDER_EMAIL
    password = SENDER_PASSWORD # Assumed to be an App Password if using Gmail/similar with 2FA
    message = MIMEText(body, 'plain', 'utf-8') # Ensure UTF-8 for broader character support
    message['Subject'] = subject
    message['From'] = f"World Movers AI-Agent <{sender}>" # Nicer From address
    message['To'] = ", ".join(recipients) # Correctly format recipient list

    # Use the globally defined SMTP_PORT (already validated as int)
    port_to_use = SMTP_PORT

    try:
        context = ssl.create_default_context() # Standard security practice
        server = None # Initialize server variable

        if port_to_use == 465: # Use SMTP_SSL for implicit SSL on port 465
            print(f"Attempting email send via SMTP_SSL: {SMTP_SERVER}:{port_to_use}")
            server = smtplib.SMTP_SSL(SMTP_SERVER, port_to_use, context=context, timeout=30) # Add timeout
            server.login(sender, password)
        elif port_to_use == 587: # Use SMTP for explicit TLS on port 587
             print(f"Attempting email send via SMTP (STARTTLS): {SMTP_SERVER}:{port_to_use}")
             server = smtplib.SMTP(SMTP_SERVER, port_to_use, timeout=30) # Add timeout
             server.ehlo() # Identify server
             server.starttls(context=context) # Upgrade to secure connection
             server.ehlo() # Re-identify after TLS
             server.login(sender, password)
        else:
             # This case should ideally be caught during initial config validation, but handle defensively
             error_msg = f"Unsupported SMTP port: {port_to_use}. Please configure secrets.toml with 465 (SSL) or 587 (TLS)."
             st.session_state.email_status_message = ("error", error_msg)
             print(f"ERROR: {error_msg}")
             return False

        # Send the email
        server.sendmail(sender, recipients, message.as_string())
        server.quit() # Close the connection gracefully

        # Set success message for display after rerun
        success_msg = f"Quote request details successfully emailed to the team ({', '.join(recipients)})!"
        st.session_state.email_status_message = ("success", success_msg)
        print(f"Email sent successfully to {', '.join(recipients)}")
        return True

    # Specific Exception Handling
    except smtplib.SMTPAuthenticationError as auth_err:
        error_msg = "Email Authentication Failed. Check sender email/password (use App Password if 2FA enabled) and account security settings (e.g., allow less secure apps - *not recommended*, App Passwords are safer)."
        st.session_state.email_status_message = ("error", error_msg)
        print(f"ERROR: SMTP Authentication Failed for {sender}. Details: {auth_err}")
        return False
    except smtplib.SMTPServerDisconnected:
         error_msg = f"Email Error: Server disconnected unexpectedly. Check server address ({SMTP_SERVER}) and port ({port_to_use})."
         st.session_state.email_status_message = ("error", error_msg)
         print(f"ERROR: SMTPServerDisconnected for {SMTP_SERVER}:{port_to_use}")
         return False
    except smtplib.SMTPException as smtp_err: # Catch broader SMTP issues
         error_msg = f"Email Error: An SMTP issue occurred. Check server/port/credentials. Details: {smtp_err}"
         st.session_state.email_status_message = ("error", error_msg)
         print(f"ERROR: SMTPException - {smtp_err}")
         return False
    except ssl.SSLError as ssl_err:
         error_msg = f"Email Error: SSL connection failed. Check port ({port_to_use}), server ({SMTP_SERVER}), and local SSL setup. Details: {ssl_err}"
         st.session_state.email_status_message = ("error", error_msg)
         print(f"ERROR: SSLError - {ssl_err}")
         return False
    except OSError as os_err: # Includes socket errors like ConnectionRefusedError, TimeoutError
        error_msg = f"Email Error: Network/OS issue connecting to {SMTP_SERVER}:{port_to_use}. Check address, port, network connectivity, and firewalls. Details: {os_err}"
        st.session_state.email_status_message = ("error", error_msg)
        print(f"ERROR: OSError (likely network-related) - {os_err}")
        return False
    except Exception as e:
        # Catch-all for other unexpected errors
        error_msg = f"An unexpected error occurred sending email: {type(e).__name__} - {e}"
        st.session_state.email_status_message = ("error", error_msg)
        print(f"ERROR sending email (unexpected): {e}")
        return False
    finally:
         # Ensure server connection is closed if it was established but failed before quit()
         if 'server' in locals() and server and hasattr(server, 'sock') and server.sock:
             try:
                 server.quit()
             except Exception: # Ignore errors during cleanup quit
                 pass

# --- TTS and Download Generation (generate_tts_audio, create_docx_download, create_pdf_download) ---
# Text-to-Speech
def generate_tts_audio(text):
    """Generates MP3 audio bytes from text using gTTS. Returns None on failure or if disabled."""
    if not gtts_available:
        # print("TTS generation skipped: gTTS library not available.") # Reduce console noise
        return None
    # Avoid generating TTS for errors, info messages, or empty/whitespace strings
    if not text or not isinstance(text, str) or text.strip() == "" or text.startswith(("[Error", "[Info", "[Analysis Blocked", "[Warning")):
        return None
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp.getvalue() # Return bytes directly
    except Exception as e:
        print(f"Error generating TTS: {type(e).__name__} - {e}")
        # Optionally inform the user via a non-blocking message if needed
        st.toast(f"Could not generate audio for response: {e}", icon="🔊")
        return None

# Download Generation
def create_docx_download(text):
    """Creates DOCX file bytes from text. Returns None on failure or empty text."""
    if not text or not isinstance(text, str) or text.strip() == "":
        return None
    try:
        doc = DocxDocument()
        # Add paragraphs, trying to preserve line breaks from the input text
        for paragraph_text in text.split('\n'):
             # Add paragraph even if it's empty to preserve spacing,
             # unless it's multiple empty lines maybe? Let's keep it simple.
             doc.add_paragraph(paragraph_text)
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        return bio.getvalue() # Return bytes
    except Exception as e:
        print(f"Error creating DOCX download: {type(e).__name__} - {e}")
        return None

def create_pdf_download(text):
    """Creates PDF file bytes from text using FPDF. Returns None on failure or empty text."""
    if not text or not isinstance(text, str) or text.strip() == "":
        return None
    try:
        pdf = FPDF()
        pdf.add_page()
        # Use a font that supports a wider range of characters if possible
        # DejaVu is a good option if installed/available, otherwise fall back to Helvetica/Arial
        try:
            pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True) # Requires .ttf file
            pdf.set_font("DejaVu", size=11)
        except RuntimeError:
            print("Warning: DejaVu font not found for PDF generation, falling back to Helvetica. Some characters might not render correctly.")
            pdf.set_font("Helvetica", size=11) # Standard fallback

        # Encode text safely for PDF generation
        # FPDF with TrueType fonts (uni=True) generally handles UTF-8 well,
        # but explicit encoding/decoding can sometimes help, though often not needed here.
        # safe_text = text.encode('latin-1', 'replace').decode('latin-1') # Less needed with UTF-8 fonts
        safe_text = text # Try direct UTF-8 first with TrueType font

        # Add text using multi_cell for automatic line breaks and full width
        pdf.multi_cell(0, 5, txt=safe_text) # w=0 means full width, h=5 is line height

        # Output PDF to bytes
        pdf_bytes = pdf.output(dest='S').encode('latin-1') # FPDF output 'S' returns latin-1 string, needs encoding
        return pdf_bytes
    except Exception as e:
        print(f"Error creating PDF download: {type(e).__name__} - {e}")
        return None

# --- Initialize Session State Variables ---
# Use a function to keep the initialization logic organized
def initialize_session_state():
    # General State
    defaults = {
        "current_mode": "🚚 Chat Assistant",
        "api_call_status": "",
        "trace_data": "{}", # Placeholder for API metadata/trace
        "send_email_flag": False,
        "email_content": "",
        "email_status_message": None, # Tuple (type: "success"|"error", message: str)
        "importer_docx_content": None, # <--- Make sure this line is correct

        # Chat Assistant Mode
        "messages": [{"role": "assistant", "content": "Welcome to World Movers! How can I help you with your Air, Sea, or Domestic shipping needs today? I can also answer questions based on our Terms & Conditions or guidance for new clients.", "audio_data": None, "id": 0}],
        "msg_id_counter": 1,
        "chat_context_files": [], # List of dicts from handle_document_upload
        "chat_context_image": None, # Stores PIL image object
        "last_chat_image_bytes": None, # Bytes of last processed camera image for chat
        "chat_camera_count": 0, # Key for camera input uniqueness

        # Document/Image Analysis Mode
        "analysis_files": [], # List of dicts from handle_document_upload
        "analysis_prompt": "", # Store the prompt that generated the current analysis
        "analysis_response": None, # Main text response
        "analysis_thoughts": None, # Extracted thoughts/reasoning
        "analysis_tts_audio": None, # Bytes for audio player
        "analysis_downloads": None, # Dict {"docx": bytes, "pdf": bytes}

        # Voice Command Mode
        "voice_transcription": "",
        # Voice mode reuses analysis_* state variables for its response display

        # Webcam Mode
        "webcam_status": "Idle",
        "webcam_analysis_result": "",
        "webcam_thoughts": "",
        "webcam_processor": None, # Stores the VideoProcessor instance

        # Screen Analysis Mode
        "screen_chat": [], # Separate chat history {"role": ..., "content": ..., "thoughts": ...}
        "current_screen_frame_pil": None, # Stores the latest PIL image from callback
        # Screen share mode uses callback, doesn't need separate processor state var

        # Take Picture Analysis Mode
        "picture_mode_image": None, # Stores PIL image object captured
        "last_picture_image_bytes": None, # Bytes of last processed camera image for picture mode
        "picture_mode_prompt": "", # Store prompt for this mode
        "picture_mode_count": 0, # Key for camera input uniqueness
        # This mode also reuses analysis_* state variables for results

        # External Knowledge Content
        "terms_content": None, # Initialize as None, fetch later
        "pdf_are_you_new_content": None, # Initialize as None, fetch later
        
        # --- Marketing Email Tool State ---
        "marketing_file_processed": False, # Flag if file is loaded and ready
        "marketing_dataframe": None, # To store the pandas DataFrame
        # List of dicts: {"email": ..., "first_name": ..., "last_name": ..., "company": ..., "name": ...}
        "marketing_recipients": [],
        "marketing_email_col": "Email", # Default column name
        "marketing_name_col": "Name", # Default column name (optional) - Can now be split
        "marketing_subject": "",
        "marketing_body": "",
        "marketing_send_status": None, # To store progress/results message
        "marketing_send_progress": 0.0, # Progress bar value
        "marketing_results": {"success": 0, "failed": 0, "errors": []}, # Store send results
        "marketing_uploaded_filename": None, # Store name of uploaded file
        # --- End Marketing Email Tool State ---

    }

    # Set defaults only if keys are not already in session state
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Add print statements for debugging initialization
    print("--- Initializing Session State ---")
    for key, value in defaults.items():
        if key not in st.session_state:
            print(f"Initializing missing key: {key}")
            st.session_state[key] = value
        # else: # Optional: Check existing value type
            # print(f"Key '{key}' already exists with value: {st.session_state[key]}")
    print("--- Initialization Complete ---")

# Call the initializer function at the start
initialize_session_state()

# +++ Load External and Internal Knowledge (runs once per session) +++
# Fetch URL content if not already loaded
# +++ Fetch and Store External Knowledge (run once per session using cache) +++
# Use st.session_state to store the fetched content after the first run
if "terms_content" not in st.session_state or st.session_state.terms_content is None:
    with st.spinner("Loading World Movers Terms & Conditions..."):
        fetched_terms = fetch_url_content(TERMS_URL)
        st.session_state.terms_content = fetched_terms # Store result (even if error string)
        if isinstance(fetched_terms, str) and fetched_terms.startswith("[Error"):
             # Display warning only once if fetch fails
             st.warning(f"⚠️ Failed to load Terms & Conditions. AI may lack knowledge on this topic. Details: {fetched_terms}", icon="📄")
             print(f"WARNING: Failed to load Terms & Conditions: {fetched_terms}") # Log warning
        elif fetched_terms:
             print(f"Successfully loaded Terms & Conditions ({len(fetched_terms)} chars).")

if "pdf_are_you_new_content" not in st.session_state or st.session_state.pdf_are_you_new_content is None:
    with st.spinner("Loading 'ARE YOU NEW.pdf' document..."):
        fetched_pdf = fetch_and_process_pdf(PDF_URL)
        st.session_state.pdf_are_you_new_content = fetched_pdf # Store result
        if isinstance(fetched_pdf, str) and (fetched_pdf.startswith("[Error") or fetched_pdf.startswith("[Info: No text")):
             st.warning(f"⚠️ Failed to load or process 'ARE YOU NEW.pdf'. AI may lack knowledge on this topic. Details: {fetched_pdf}", icon="📄")
             print(f"WARNING: Failed to load/process 'ARE YOU NEW.pdf': {fetched_pdf}") # Log warning
        elif fetched_pdf:
             print(f"Successfully loaded ARE YOU NEW.pdf ({len(fetched_pdf)} chars).")
         
# Load Local DOCX content if not already loaded
if "importer_docx_content" not in st.session_state or st.session_state.importer_docx_content is None:
    with st.spinner(f"Loading internal document ({os.path.basename(IMPORTER_DOCX_PATH)})..."):
        loaded_docx = load_local_docx_content(IMPORTER_DOCX_PATH)
        # Assign the loaded content (or error string) back to the session state key
        st.session_state.importer_docx_content = loaded_docx # Store result (text or error string)
        # Display warning only once if loading fails
        if isinstance(loaded_docx, str) and (loaded_docx.startswith("[Error") or loaded_docx.startswith("[Info:")):
             st.warning(f"⚠️ Failed to load or process '{os.path.basename(IMPORTER_DOCX_PATH)}'. AI knowledge may be incomplete. Details: {loaded_docx}", icon="📄")
             print(f"WARNING: Failed to load/process '{IMPORTER_DOCX_PATH}': {loaded_docx}") # Log warning
        elif loaded_docx:
             print(f"Successfully loaded {IMPORTER_DOCX_PATH} ({len(loaded_docx)} chars).")
        else:
            # Handle case where load_local_docx_content might return None unexpectedly
             print(f"Warning: Loading '{IMPORTER_DOCX_PATH}' returned None or empty value.")
             # Ensure state is not left as None if load failed silently
             if st.session_state.importer_docx_content is None:
                  st.session_state.importer_docx_content = "[Error: Loading failed silently]"

# +++ End of Knowledge Loading +++

# +++ End of Fetch and Store +++


# --- Streamlit App Layout ---

# Sidebar
with st.sidebar:
    st.image("https://i.imgur.com/uQbFgaS.png", width=150, caption="World Movers Phils Inc.")
    st.title("World Movers AI-Agent")
    st.markdown("---")

    # --- Library Availability Check (Already done during import) ---
    # You can add visual indicators here if desired, but messages were printed via st.sidebar.caption

    # --- Mode Selection ---
    
    modes = ["🚚 Chat Assistant", "📊 Doc/Image Analysis"]
    # Conditionally add modes requiring specific libraries
    if sr_available and audiorecorder_available:
        modes.append("🎤 Voice Command")
    if webrtc_available: # Assumes 'av' is also available if webrtc is
        modes.extend(["👁️ Live Webcam", "💻 Screen Analysis", "📸 Take Picture Analysis"])
    # --- Add Marketing Mode ---
    if pandas_available: # Only add if pandas is installed
        modes.append("📧 Marketing Email Tool")
    # +++ Add News Feed Mode +++
    if newsapi_available:
        modes.append("📰 News Feed")
    # +++ INSERT NEW MODE HERE +++
    #modes.append("🛠️ Freight Calculators") # New mode
    modes.append("🧮 Basic Estimators") # <--- NEW LINE TO ADD
    modes.append("🚁 Drone Operations Simulation") # <--- NEW LINE TO ADD

    # Use session state for the currently selected mode index
    try:
        # Ensure current_mode is valid, reset if not
        if st.session_state.current_mode not in modes:
            st.session_state.current_mode = modes[0]
        current_index = modes.index(st.session_state.current_mode)
    except ValueError:
        current_index = 0 # Default to first mode if index fails
        st.session_state.current_mode = modes[0] # Reset state

    # Define callback to update the main state variable when radio changes
    def update_mode():
        st.session_state.current_mode = st.session_state.current_mode_radio

    selected_mode = st.radio(
        "Select Interaction Mode:",
        modes,
        index=current_index,
        key="current_mode_radio", # Use a different key for the widget itself
        on_change=update_mode # Callback updates the primary state var
    )
    st.markdown("---")

    # --- Context Input Area (Only for Chat Assistant Mode) ---
    if st.session_state.current_mode == "🚚 Chat Assistant":
        st.subheader("Add Context (Optional)")
        # Use a dynamic key for file uploader to allow re-uploading the same file name after removal
        uploader_key_chat = f"chat_uploader_{len(st.session_state.chat_context_files)}"
        uploaded_files_chat = st.file_uploader(
            "Upload Doc/Image:",
            type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "webp", "bmp", "gif", "heic", "heif"], # Match handle_document_upload
            accept_multiple_files=True,
            key=uploader_key_chat,
            help="Add files for the AI to consider in the chat."
        )
        # Use dynamic key for camera based on counter
        camera_key_chat = f"chat_camera_{st.session_state.get('chat_camera_count', 0)}"
        captured_image_data_chat = None
        if webrtc_available: # Only show camera if library is available
            captured_image_data_chat = st.camera_input(
                "Take Picture:",
                key=camera_key_chat,
                help="Add a picture from your camera to the chat context."
                )
        else:
            st.caption("Camera input disabled (requires `streamlit-webrtc`).")


        # --- Process uploads for chat context ---
        if uploaded_files_chat:
            with st.spinner("Processing uploads..."):
                new_files_processed = False
                current_names = [f.get("name") for f in st.session_state.chat_context_files]
                files_to_add = [] # Process in batch
                for file in uploaded_files_chat:
                    if file.name not in current_names:
                        print(f"Processing chat context file: {file.name}") # Debug
                        processed_data = handle_document_upload(file)
                        files_to_add.append(processed_data)
                        new_files_processed = True
                    # else: print(f"Skipping already processed file: {file.name}") # Debug
                if files_to_add:
                    st.session_state.chat_context_files.extend(files_to_add)
                if new_files_processed:
                    st.rerun() # Rerun to update sidebar and clear uploader

        # --- Process camera capture for chat context ---
        if captured_image_data_chat:
            new_image_bytes = captured_image_data_chat.getvalue()
            # Check if the bytes are different from the last processed image *or* if it's the first image
            if new_image_bytes != st.session_state.get('last_chat_image_bytes'):
                with st.spinner("Processing picture..."):
                    try:
                        print("Processing new chat context picture.") # Debug
                        img_chat = Image.open(io.BytesIO(new_image_bytes))
                        # Ensure RGB format (safe default)
                        if img_chat.mode not in ['RGB', 'RGBA', 'L']:
                            img_chat = img_chat.convert('RGB')

                        st.session_state.chat_context_image = img_chat # Store the PIL image
                        st.session_state.last_chat_image_bytes = new_image_bytes # Store bytes

                        # Increment counter to ensure camera widget gets a new key next time (helps reset)
                        st.session_state.chat_camera_count = st.session_state.get('chat_camera_count', 0) + 1
                        st.rerun() # Rerun to update context display and clear camera widget state
                    except UnidentifiedImageError:
                         st.error("Failed to identify image format. Please use a standard format (JPG, PNG, etc.).")
                         st.session_state.chat_context_image = None
                         st.session_state.last_chat_image_bytes = None
                    except Exception as e:
                        st.error(f"Failed to process captured image: {e}")
                        st.session_state.chat_context_image = None
                        st.session_state.last_chat_image_bytes = None # Reset bytes on error

        # --- Clear context image if camera input becomes None (user cleared it) ---
        # Check *after* processing potential new image
        if captured_image_data_chat is None and st.session_state.get('last_chat_image_bytes') is not None:
             # If camera input is now None, but we had processed an image before, clear the state
             print("Camera input cleared by user, resetting chat image context.") # Debug
             st.session_state.chat_context_image = None
             st.session_state.last_chat_image_bytes = None
             # Increment counter to reset camera widget key on next run
             st.session_state.chat_camera_count = st.session_state.get('chat_camera_count', 0) + 1
             st.rerun() # Rerun needed to update sidebar display


        # --- Display chat context summary ---
        st.markdown("---")
        st.subheader("Current Chat Context")
        has_context = False

        # Display file context
        if st.session_state.chat_context_files:
            has_context = True
            # Use columns for better layout with remove buttons
            for i, ctx in enumerate(st.session_state.chat_context_files):
                col1, col2 = st.columns([0.85, 0.15]) # Adjust ratio as needed
                with col1:
                    icon = "📄" if ctx["type"] == "text" else "🖼️" if ctx["type"] == "image" else "❓"
                    status_color = "#E74C3C" if ctx["type"] == "error" else ("#F39C12" if "[Info:" in str(ctx.get("content","")) else "#BDC3C7")
                    status_text = ""
                    tooltip = ctx['name'] # Default tooltip is filename
                    content_preview = ""
                    if ctx["type"] == "error":
                        status_text = " (Error)"
                        tooltip = f"{ctx['name']} - Error: {ctx.get('content', 'Unknown error')}"
                    elif "[Info:" in str(ctx.get("content","")):
                        status_text = " (Info)"
                        tooltip = f"{ctx['name']} - Info: {ctx.get('content', 'No details')}"
                    elif ctx["type"] == "text":
                        content_preview = f" ({len(ctx.get('content', ''))} chars)"
                        tooltip = f"{ctx['name']} - Text Document"
                    elif ctx["type"] == "image":
                         # content_preview = f" ({ctx['content'].width}x{ctx['content'].height})" if ctx.get('content') else ""
                         tooltip = f"{ctx['name']} - Image File"


                    display_name = ctx['name'][:25] + '...' if len(ctx['name']) > 25 else ctx['name'] # Truncate long names
                    st.markdown(f"<span style='font-size: 0.9em; color: {status_color};' title='{tooltip}'>{icon} {display_name}{status_text}{content_preview}</span>", unsafe_allow_html=True)
                with col2:
                     remove_key = f"remove_chat_file_{i}_{ctx['name']}" # Unique key
                     if st.button("✖️", key=remove_key, help=f"Remove {ctx['name']}", use_container_width=True):
                         print(f"Removing chat context file: {ctx['name']}") # Debug
                         # Remove the item safely by index
                         removed_item = st.session_state.chat_context_files.pop(i)
                         # Optionally do something with removed_item if needed
                         st.rerun()
            st.markdown("---") # Separator after files

        # Display image context (from camera)
        if st.session_state.chat_context_image:
            has_context = True
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                 # Show thumbnail preview
                 st.image(st.session_state.chat_context_image, width=60, caption="Cam Capture")
                 # st.markdown(f"<span style='font-size: 0.9em; color: #BDC3C7;' title='Captured Image'>🖼️ Camera Capture</span>", unsafe_allow_html=True)
            with col2:
                 if st.button("✖️", key="remove_chat_image", help="Remove captured image", use_container_width=True):
                     print("Removing chat context image.") # Debug
                     st.session_state.chat_context_image = None
                     st.session_state.last_chat_image_bytes = None # Also clear bytes marker
                     st.session_state.chat_camera_count = st.session_state.get('chat_camera_count', 0) + 1 # Ensure camera key changes
                     st.rerun()
            st.markdown("---") # Separator after image

        # Display if no context
        if not has_context:
            st.caption("No context files or pictures added.")

        # Button to clear all context
        if has_context:
            # st.markdown("---") # Separator before clear button
            if st.button("Clear All Chat Context", key="clear_chat_ctx_btn", help="Remove all uploaded files and captured pictures from context"):
                print("Clearing all chat context.") # Debug
                st.session_state.chat_context_files = []
                st.session_state.chat_context_image = None
                st.session_state.last_chat_image_bytes = None
                st.session_state.chat_camera_count = st.session_state.get('chat_camera_count', 0) + 1 # Increment to reset camera widget
                st.rerun()

# --- Main Application Area ---

# Extract the mode name for the title
mode_display_name = st.session_state.current_mode.split(' ', 1)[-1] # Get text after first emoji+space
st.title(f"🚚 World Movers AI-Agent - {mode_display_name} Mode")
st.caption(f"Powered by Gemini AGI | Made by MiChaelinzo [GitHub](http://github.com/michaelinzo/) | worldmovers.net / worldmovers.com.ph | Powered By: Google Cloud Platform | Cloud Run | Gemini API")

# --- Display Email Status Message ---
# Check if the message exists and display it once, then clear it
if st.session_state.get("email_status_message"):
    msg_type, msg_text = st.session_state.email_status_message
    if msg_type == "success":
        st.success(msg_text, icon="✅")
    else: # Error
        st.error(msg_text, icon="🚨")
    # Clear the message after displaying it so it doesn't reappear on next rerun
    st.session_state.email_status_message = None

# --- Mode: Chat Assistant ---
if st.session_state.current_mode == "🚚 Chat Assistant":
    st.info("Ask questions about World Movers services, request quotes, or discuss context from the sidebar and internal knowledge (Terms, New Client PDF, Importer Doc).") # Updated info

    # Display chat messages from history
    for message in st.session_state.messages:
        avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
        # Use the unique message ID for keys within the message block
        unique_msg_key_prefix = f"msg_{message.get('id', f'init_{time.time()}')}" # Add timestamp for initial msg key safety

        with st.chat_message(message["role"], avatar=avatar):
            # Use st.write for potential markdown/HTML rendering if needed, but sanitize
            st.markdown(message["content"], unsafe_allow_html=False) # Safer default

            # Add TTS and Download buttons only for assistant messages with valid content
            if message["role"] == "assistant":
                # Ensure content exists and isn't an error/info placeholder before adding buttons
                msg_content = message.get("content", "")
                is_valid_content = msg_content and not msg_content.startswith(("[Error", "[Info", "[Analysis Blocked", "[Warning"))

                if is_valid_content:
                    # --- TTS Audio Player ---
                    audio_bytes = message.get("audio_data") # Check if pre-generated audio exists
                    if audio_bytes is None and gtts_available: # Try generating if not stored and lib available
                        # Generate TTS and store it back in the message *if* successful
                        generated_audio = generate_tts_audio(msg_content)
                        if generated_audio:
                            message["audio_data"] = generated_audio # Store for future reruns
                            audio_bytes = generated_audio

                    # Display audio player if bytes exist
                    if audio_bytes:
                        try:
                            st.audio(audio_bytes, format='audio/mp3', start_time=0)
                        except Exception as audio_err:
                            st.caption(f"Audio playback unavailable: {audio_err}")

                    # --- Download Buttons ---
                    st.markdown('<div class="download-buttons">', unsafe_allow_html=True)
                    col_dl_1, col_dl_2, col_dl_spacer = st.columns([1, 1, 4]) # Adjust spacing if needed

                    # Create downloads (functions return None if content is invalid/empty)
                    docx_bytes = create_docx_download(msg_content)
                    pdf_bytes = create_pdf_download(msg_content)

                    with col_dl_1:
                        if docx_bytes:
                            st.download_button(
                                label="DOCX",
                                data=docx_bytes,
                                file_name=f"WM_Chat_{message.get('id', 0)}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"{unique_msg_key_prefix}_docx_dl",
                                help="Download response as DOCX"
                                )
                        # else: st.caption("DOCX N/A") # Optional: Show if download not possible

                    with col_dl_2:
                        if pdf_bytes:
                            st.download_button(
                                label="PDF",
                                data=pdf_bytes,
                                file_name=f"WM_Chat_{message.get('id', 0)}.pdf",
                                mime="application/pdf",
                                key=f"{unique_msg_key_prefix}_pdf_dl",
                                help="Download response as PDF"
                                )
                        # else: st.caption("PDF N/A") # Optional

                    st.markdown('</div>', unsafe_allow_html=True)

    # --- React to user input ---
    if prompt := st.chat_input("Ask your question here..."):
        # 1. Append user message to history with a unique ID
        user_msg_id = st.session_state.msg_id_counter
        st.session_state.messages.append({"role": "user", "content": prompt, "id": user_msg_id})
        st.session_state.msg_id_counter += 1
        # Rerun immediately to display the user's message
        st.rerun()

    # --- Generate AI response if the last message is from the user ---
    if st.session_state.messages[-1]["role"] == "user":
        last_user_prompt = st.session_state.messages[-1]["content"]
        print(f"User prompt received: {last_user_prompt[:100]}...") # Debug

        # 2. Prepare context for Gemini API (using Parts API structure)
        api_contents = [] # Build a list of Parts (text, image)
        context_description_parts = [] # Build a human-readable description of context provided

        # +++ PREPEND EXTERNAL KNOWLEDGE FROM SESSION STATE +++
        terms_text = st.session_state.get("terms_content")
        pdf_text = st.session_state.get("pdf_are_you_new_content")
        importer_text = st.session_state.get("importer_docx_content") # <--- Get importer content
        external_knowledge_parts = []
        knowledge_added = False

        # Add Terms and Conditions if successfully loaded
        if isinstance(terms_text, str) and terms_text and not terms_text.startswith("[Error"):
            external_knowledge_parts.append(f"--- Start: World Movers Terms & Conditions ---\n{terms_text}\n--- End: World Movers Terms & Conditions ---")
            context_description_parts.append("the World Movers Terms & Conditions")
            knowledge_added = True
        # Add 'ARE YOU NEW.pdf' content if successfully loaded
        if isinstance(pdf_text, str) and pdf_text and not pdf_text.startswith("[Error") and not pdf_text.startswith("[Info: No text"):
            external_knowledge_parts.append(f"--- Start: Document 'ARE YOU NEW.pdf' ---\n{pdf_text}\n--- End: Document 'ARE YOU NEW.pdf' ---")
            context_description_parts.append("the 'ARE YOU NEW.pdf' document")
            knowledge_added = True
        # --- Add importer.docx content ---
        if isinstance(importer_text, str) and importer_text and not importer_text.startswith(("[Error", "[Info:")):
            api_contents.append(f"--- Start: Internal Document ({os.path.basename(IMPORTER_DOCX_PATH)}) ---\n{importer_text}\n--- End: Internal Document ---")
            context_description_parts.append(f"the internal '{os.path.basename(IMPORTER_DOCX_PATH)}' document")
            internal_knowledge_added = True
        # --- End Add importer.docx content ---

        if knowledge_added:
            # Add the combined external knowledge as the *first* text part(s)
            api_contents.extend(external_knowledge_parts) # Add knowledge strings directly
            print(f"Prepended external knowledge ({len(external_knowledge_parts)} part(s)) to API prompt.") # Debug
            api_contents.append("\n\n---\n\n") # Add separator

        # Add text context from sidebar uploaded files
        uploaded_text_context_parts = []
        for ctx in st.session_state.chat_context_files:
             # Include only successfully processed text files
             if ctx["type"] == "text" and isinstance(ctx.get("content"), str) and ctx["content"] and not ctx["content"].startswith(("[Error", "[Info")):
                uploaded_text_context_parts.append(f"--- Context from Uploaded File: {ctx['name']} ---\n{ctx['content']}\n--- End {ctx['name']} ---")
                context_description_parts.append(f"uploaded text file '{ctx['name']}'")
        if uploaded_text_context_parts:
            # Add the combined text context as subsequent text part(s)
            api_contents.extend(uploaded_text_context_parts) # Add file content strings
            api_contents.append("\n\n---\n\n") # Add separator

        # Check for image context (captured camera OR uploaded image from sidebar)
        image_to_send = None
        image_source_description = ""
        # Prioritize camera image if both exist
        if st.session_state.chat_context_image and isinstance(st.session_state.chat_context_image, Image.Image):
            image_to_send = st.session_state.chat_context_image
            image_source_description = "the captured picture"
            context_description_parts.append(image_source_description)
        else: # Check uploaded files if no camera image
            # Find the *first* valid image in the context files
            for ctx in st.session_state.chat_context_files:
                 if ctx["type"] == "image" and isinstance(ctx.get("content"), Image.Image):
                    image_to_send = ctx["content"]
                    image_source_description = f"the uploaded image '{ctx['name']}'"
                    context_description_parts.append(image_source_description)
                    break # Send only the first valid image found in uploads

        # Construct the final prompt text, including context description
        context_description = ""
        if context_description_parts:
            # Create a clearer description of all context provided
            context_summary = "Using the following context: " + ", ".join(context_description_parts) + ". Please answer the user's query.\n\n"
            context_description = context_summary

        # Add the actual user query, clearly separated and formatted
        final_prompt_text = f"{context_description}--- User Query ---\n{last_user_prompt}\n--- End User Query ---"
        api_contents.append(final_prompt_text) # Append the final prompt string as a text part

        # Add the image data as a separate Part if available
        if image_to_send:
            try:
                 # Add the PIL image object directly as a Part
                 api_contents.append(image_to_send)
                 print(f"Appended image context ({image_source_description}) to API prompt.") # Debug
            except Exception as e:
                 # Handle error if image can't be added (very rare with PIL for Gemini)
                 st.warning(f"Could not prepare image '{image_source_description}' for API request: {e}. Proceeding without image.", icon="🖼️")
                 # Add error message to chat? Or just log? Let's log and maybe add simple chat message.
                 assist_msg_id = st.session_state.msg_id_counter
                 st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"[Warning: Failed to process image context '{image_source_description}'. AI response may not consider the image.]",
                    "audio_data": None, "id": assist_msg_id
                 })
                 st.session_state.msg_id_counter += 1
                 # Don't necessarily need to rerun here, just proceed with text


        # --- Optional: Token Limit Check (Conceptual) ---
        # Gemini 1.5 Pro has a large context window (1M tokens default, up to 2M)
        # Simple length check is less critical but useful for huge inputs.
        # total_estimated_chars = sum(len(part) for part in api_contents if isinstance(part, str))
        # print(f"Estimated total prompt chars: {total_estimated_chars}")
        # if total_estimated_chars > 800000: # Rough check (well below 1M tokens)
        #    st.warning("Warning: Combined context and prompt is very large. Response might be slow or encounter issues.", icon="⚠️")

        # 3. Send message(s) to Gemini
        try:
            with st.spinner(f"Thinking with World Movers AI/AGI-Agent..."):
                 # Use generate_content with the list of Parts
                 print(f"Sending {len(api_contents)} parts to Gemini API ({MODEL_NAME}).") # Debug: Check parts count
                 # Example: Log types of parts being sent for debugging complex cases
                 # for i, part in enumerate(api_contents): print(f" Part {i}: {type(part)}")

                 response = model.generate_content(
                     api_contents, # List of [str, str, Image, str] or similar structure
                     stream=False # Keep simple for basic chat display
                 )

                 # Process response, handle potential errors or empty response
                 if response and response.text:
                     assistant_response = response.text
                     st.session_state.api_call_status = f"🤖 AI-Agent Assistant responded ({time.strftime('%H:%M:%S')})"

                     # Generate TTS immediately for faster audio availability
                     # Store generated audio directly in the message dict for persistence across reruns
                     audio_bytes = generate_tts_audio(assistant_response)

                     # Add Assistant Response to chat history
                     assist_msg_id = st.session_state.msg_id_counter
                     st.session_state.messages.append({
                         "role": "assistant",
                         "content": assistant_response,
                         "audio_data": audio_bytes, # Store pre-generated audio bytes (or None)
                         "id": assist_msg_id
                     })
                     st.session_state.msg_id_counter += 1

                     # --- Check for Quote Forwarding Trigger ---
                     keywords_indicating_quote_ready = ["forward this information", "send these details", "forwarding this to our team", "forwarding the request", "quoting team", "pass this to the team", "email this quote request"]
                     positive_phrasing = ["will now attempt", "i will now forward", "i will forward", "i'll send this"]
                     # Check if keywords and positive intent are present
                     if any(keyword in assistant_response.lower() for keyword in keywords_indicating_quote_ready) and \
                        any(phrase in assistant_response.lower() for phrase in positive_phrasing):
                         print("Quote forwarding trigger detected in chat response.") # Debug
                         st.session_state.send_email_flag = True
                         # Prepare email content (more structured)
                         context_summary_email = "None"
                         if context_description_parts:
                              context_summary_email = "; ".join(context_description_parts) # Use semicolon for clarity

                         st.session_state.email_content = (
                            f"Mode: Chat Assistant\n"
                            f"User Query: {last_user_prompt}\n\n"
                            f"Context Provided by User: {context_summary_email}\n\n"
                            f"AI Response Triggering Email Send:\n---\n{assistant_response}\n---"
                         )
                         # Don't rerun here, let the email flag be checked at the end of the script

                 else:
                     # Handle cases where the API returns an empty or invalid response
                     st.error("Assistant response was empty or invalid.", icon="❓")
                     assistant_response = "[Error: Received empty response from AI]"
                     st.session_state.api_call_status = f"❌ Empty Response ({time.strftime('%H:%M:%S')})"
                     # Add error message to chat history
                     assist_msg_id = st.session_state.msg_id_counter
                     st.session_state.messages.append({"role": "assistant", "content": assistant_response, "id": assist_msg_id, "audio_data": None})
                     st.session_state.msg_id_counter += 1


                 # Rerun to display the assistant's response (or error) and check email flag
                 st.rerun()

        except genai.types.generation_types.StopCandidateException as e:
             # Handle blocked content specifically (safety filters)
             error_msg = f"Response stopped: The prompt or generated response may have been blocked due to safety settings ({e.reason}). Please try rephrasing or modifying context."
             st.error(error_msg, icon="🚫")
             print(f"ERROR: StopCandidateException - Reason: {e.reason}")
             st.session_state.api_call_status = f"❌ Response Blocked ({time.strftime('%H:%M:%S')})"
             # Add specific error message to chat history
             assist_msg_id = st.session_state.msg_id_counter
             st.session_state.messages.append({"role": "assistant", "content": f"[Error: Response blocked by safety filter - {e.reason}]", "id": assist_msg_id, "audio_data": None})
             st.session_state.msg_id_counter += 1
             st.rerun() # Rerun to display the error message

        except Exception as e:
             # Handle other API or processing errors (network, config, internal Gemini issues)
             error_msg = f"An error occurred generating the response: {type(e).__name__} - {e}"
             st.error(error_msg, icon="🔥")
             print(f"ERROR during chat generation/processing: {type(e).__name__} - {e}")
             st.session_state.api_call_status = f"❌ Error ({time.strftime('%H:%M:%S')})"
             assist_msg_id = st.session_state.msg_id_counter
             # Add a user-friendly error message to chat
             st.session_state.messages.append({"role": "assistant", "content": f"[Error: {type(e).__name__} occurred while generating response. Please check connection or try again.]", "id": assist_msg_id, "audio_data": None})
             st.session_state.msg_id_counter += 1
             st.rerun() # Rerun to display the error message


# --- Mode: Document/Image Analysis ---
elif st.session_state.current_mode == "📊 Doc/Image Analysis":
    st.info("Upload documents (PDF, DOCX, TXT) or images (JPG, PNG, WEBP, etc.), then ask specific questions about their content.")

    # File Uploader for this mode
    analysis_uploader_key = f"analysis_uploader_{len(st.session_state.analysis_files)}"
    uploaded_analysis_files = st.file_uploader(
        "Upload Files for Analysis:",
        type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "webp", "bmp", "gif", "heic", "heif"], # Match handle_document_upload
        accept_multiple_files=True,
        key=analysis_uploader_key,
        help="Select one or more files to analyze."
    )

    # Process and store uploaded files for analysis
    if uploaded_analysis_files:
        with st.spinner("Processing files..."):
            newly_processed = False
            current_names = [f['name'] for f in st.session_state.analysis_files]
            files_to_add = []
            for file in uploaded_analysis_files:
                if file.name not in current_names:
                    print(f"Processing analysis file: {file.name}") # Debug
                    processed_data = handle_document_upload(file)
                    files_to_add.append(processed_data)
                    newly_processed = True
            if files_to_add:
                st.session_state.analysis_files.extend(files_to_add)
            if newly_processed:
                 # Clear previous analysis results when new files are added/processed
                 st.session_state.analysis_response = None
                 st.session_state.analysis_thoughts = None
                 st.session_state.analysis_tts_audio = None
                 st.session_state.analysis_downloads = None
                 st.session_state.api_call_status = ""
                 st.rerun() # Rerun to update display and clear uploader

    # Display files ready for analysis and allow removal
    files_valid_for_analysis = [] # Keep track of files usable for analysis API call
    if st.session_state.analysis_files:
        st.markdown("---")
        st.subheader("Files Ready for Analysis:")
        cols_per_row = 3 # Adjust based on screen width / preference
        cols = st.columns(cols_per_row)
        col_idx = 0

        # Iterate over a copy to allow safe removal from original list
        current_analysis_files = list(st.session_state.analysis_files)

        for i, file_info in enumerate(current_analysis_files):
             with cols[col_idx % cols_per_row]:
                file_name = file_info.get("name", f"File_{i}")
                file_type = file_info.get("type", "unknown")
                content = file_info.get("content")
                # Use container with border for better visual grouping
                with st.container(border=True):
                    # Display filename prominently
                    display_name = file_name[:30] + '...' if len(file_name) > 30 else file_name
                    st.markdown(f"**{display_name}**")

                    is_valid = False # Flag if file is suitable for sending to API
                    if file_type == "text":
                        if isinstance(content, str) and content and not content.startswith(("[Error", "[Info")):
                            # Show short preview, indicate validity
                            st.text_area(f"preview_{i}", content[:150]+"...", height=80, disabled=True, key=f"text_prev_{i}_{file_name}", help="Text preview (first 150 chars)")
                            st.caption("✅ Ready for Analysis")
                            is_valid = True
                        elif isinstance(content, str) and content.startswith("[Info"):
                             st.info(content, icon="ℹ️") # Show info message (e.g., empty file)
                             st.caption("⚠️ Not suitable for analysis")
                        else: # Includes errors or empty content
                             st.error(content or "[Error: Empty or unreadable text file]", icon="❌")
                             st.caption("⚠️ Error during processing")
                    elif file_type == "image":
                        if isinstance(content, Image.Image):
                            st.image(content, use_container_width=True, caption="Image Preview")
                            st.caption("✅ Ready for Analysis")
                            is_valid = True
                        else: # Should be caught by handle_document_upload, but safety check
                             st.error(content or "[Error: Invalid image file data]", icon="❌")
                             st.caption("⚠️ Error loading image")
                    elif file_type == "error":
                         st.error(content or "[Error: Unknown processing error]", icon="❌")
                         st.caption("⚠️ Error during processing")
                    else: # Should not happen with current types, but fallback
                         st.warning(f"Unprocessed or unsupported file type ({file_type})", icon="❓")
                         st.caption("⚠️ Cannot analyze")

                    if is_valid:
                        files_valid_for_analysis.append(file_info) # Add valid file to list for API call

                    # Button to remove file from analysis list
                    remove_key = f"remove_analysis_file_{i}_{file_name}" # Unique key
                    if st.button("Remove", key=remove_key, help=f"Remove {file_name} from analysis list", use_container_width=True):
                        # Find and remove the file from the *original* session state list
                        original_index = -1
                        for idx, item in enumerate(st.session_state.analysis_files):
                            # Simple match by name - assumes names are unique in one upload batch
                            if item.get('name') == file_name:
                                original_index = idx
                                break
                        if original_index != -1:
                            print(f"Removing analysis file: {st.session_state.analysis_files[original_index]['name']}") # Debug
                            st.session_state.analysis_files.pop(original_index)
                        else:
                             print(f"Error: Could not find file {file_name} to remove in session state.") # Debug
                        # Clear results associated with previous analysis runs if files change
                        st.session_state.analysis_response = None
                        st.session_state.analysis_thoughts = None
                        st.session_state.analysis_tts_audio = None
                        st.session_state.analysis_downloads = None
                        st.session_state.api_call_status = ""
                        st.rerun() # Rerun to reflect removal and clear results display

             col_idx += 1 # Move to next column
        st.markdown("---") # Separator after file display grid

    # Prompt area and submit button
    analysis_prompt_input = st.text_area(
        "Your Question / Analysis Request:",
        height=150,
        key="analysis_prompt_widget", # Use separate key for widget
        placeholder="e.g., Summarize the key points from the PDF.\nWhat is the address on the label in the image?\nCompare the contents of DocumentA.docx and ReportB.pdf.\nExtract all invoice numbers from the uploaded files.",
        help="Ask the AI to analyze the content of the valid files listed above."
        # value=st.session_state.get("analysis_prompt", "") # Keep prompt after rerun if analysis fails? Maybe not.
    )
    analysis_prompt_input = analysis_prompt_input.strip() # Clean prompt

    submit_analysis = st.button(
        "Analyze Content",
        type="primary",
        disabled=(not files_valid_for_analysis or not analysis_prompt_input), # Disable if no valid files or no prompt
        key="submit_analysis_btn"
        )

    if submit_analysis:
        # Clear previous results *before* starting new analysis
        st.session_state.analysis_response = None
        st.session_state.analysis_thoughts = None
        st.session_state.analysis_tts_audio = None
        st.session_state.analysis_downloads = None
        st.session_state.api_call_status = "⏳ Preparing analysis request..."
        st.session_state.analysis_prompt = analysis_prompt_input # Store the prompt that triggered this run

        # Prepare API contents (list of Parts)
        api_contents_analysis = []
        file_names_analyzed = [] # Keep track for email/logging

        # Combine text content first, adding markers
        combined_text = ""
        for file_info in files_valid_for_analysis:
            if file_info["type"] == "text":
                combined_text += f"--- Content from File: {file_info['name']} ---\n{file_info['content']}\n\n"
                file_names_analyzed.append(file_info['name'])
        if combined_text:
             api_contents_analysis.append(combined_text.strip()) # Add combined text as one Part

        # Add images, potentially interleaving with text prompt
        images_added_count = 0
        for file_info in files_valid_for_analysis:
            if file_info["type"] == "image" and isinstance(file_info["content"], Image.Image):
                # You might add a text marker BEFORE the image if context is crucial,
                # but often just adding image parts works well. Gemini 1.5 handles multi-image well.
                # Example marker (optional): api_contents_analysis.append(f"(Image Reference: {file_info['name']})")
                api_contents_analysis.append(file_info["content"]) # Append the PIL Image object directly
                if file_info['name'] not in file_names_analyzed:
                    file_names_analyzed.append(file_info['name'])
                images_added_count += 1

        # Add the user's request/prompt *last* (or maybe after text, before images? Test needed)
        # Let's put it last for clarity.
        prompt_with_request = analysis_prompt_input
        # Add request for thoughts if not explicitly asked
        if "thought" not in analysis_prompt_input.lower() and "reasoning" not in analysis_prompt_input.lower():
            prompt_with_request += "\n\n(Also, please explain your analysis steps or reasoning process under the heading '***AI Thoughts:***')"
        api_contents_analysis.append(f"\n\n**User Request:**\n{prompt_with_request}")


        print(f"Submitting analysis request for files: {', '.join(file_names_analyzed)} ({images_added_count} image(s)). Prompt: {analysis_prompt_input[:100]}...") # Debug

        # Call Gemini API within a spinner context
        with st.spinner("Analyzing content with World Movers AI-Agent..."):
            try:
                response = model.generate_content(
                    api_contents_analysis, # Send the list of Parts
                    stream=False # Keep simple for analysis mode display
                )
                # Process response
                if response and response.text:
                    full_response_text = response.text
                    main_response = full_response_text
                    thoughts_text = ""

                    # Extract thoughts using the specified heading
                    if "***AI Thoughts:***" in full_response_text:
                        try:
                            parts = full_response_text.split("***AI Thoughts:***", 1)
                            main_response = parts[0].strip()
                            thoughts_text = parts[1].strip()
                        except Exception as split_err:
                            print(f"Note: Found '***AI Thoughts:***' but couldn't split response text cleanly: {split_err}") # Debug log
                            # Keep full response if split fails, maybe add note about thoughts
                            main_response = full_response_text # Fallback
                            thoughts_text = "[AI Thoughts section found but could not be extracted separately]"

                    st.session_state.analysis_response = main_response
                    st.session_state.analysis_thoughts = thoughts_text
                    st.session_state.analysis_tts_audio = generate_tts_audio(main_response)
                    st.session_state.analysis_downloads = {
                        "docx": create_docx_download(main_response),
                        "pdf": create_pdf_download(main_response)
                    }
                    st.session_state.api_call_status = f"✅ Analysis complete ({time.strftime('%H:%M:%S')})"

                    # --- Check for Quote Forwarding Trigger in Analysis ---
                    keywords_indicating_quote_ready = ["forward this information", "send these details", "forwarding this to our team", "forwarding the request", "quoting team", "pass this to the team", "email this quote request"]
                    positive_phrasing = ["will now attempt", "i will now forward", "i will forward", "i'll send this"]
                    if any(keyword in main_response.lower() for keyword in keywords_indicating_quote_ready) and \
                       any(phrase in main_response.lower() for phrase in positive_phrasing):
                        print("Quote forwarding trigger detected in analysis response.") # Debug
                        st.session_state.send_email_flag = True
                        st.session_state.email_content = (
                           f"Mode: Document/Image Analysis\n"
                           f"User Analysis Request: {st.session_state.analysis_prompt}\n\n"
                           f"Files Analyzed: {', '.join(file_names_analyzed)}\n\n"
                           f"AI Response Triggering Send:\n---\n{main_response}\n---\n"
                           f"\nAI Thoughts (if available):\n{thoughts_text if thoughts_text else 'N/A'}\n---"
                        )
                        # Let flag be checked at end of script
                else:
                    # Handle empty/invalid response from API
                    st.error("Analysis resulted in an empty response from the AI.", icon="❓")
                    st.session_state.analysis_response = "[Error: Received empty response from AI]"
                    st.session_state.analysis_thoughts = None
                    st.session_state.api_call_status = f"❌ Empty Response ({time.strftime('%H:%M:%S')})"


                # Rerun needed to display results (or empty response error) and check email flag
                st.rerun()

            except genai.types.generation_types.StopCandidateException as e:
                error_msg = f"Analysis stopped: The content or request might have been blocked by safety filters ({e.reason})."
                st.error(error_msg, icon="🚫")
                st.session_state.analysis_response = f"[Error: Response blocked by API safety filter - {e.reason}]"
                st.session_state.analysis_thoughts = None
                st.session_state.api_call_status = f"❌ Analysis Blocked ({time.strftime('%H:%M:%S')})"
                st.rerun() # Rerun to display the blocked message
            except Exception as e:
                error_msg = f"Analysis failed: {type(e).__name__} - {e}"
                st.error(error_msg, icon="🔥")
                st.session_state.analysis_response = f"[Error during analysis: {type(e).__name__}]"
                st.session_state.analysis_thoughts = None
                st.session_state.api_call_status = f"❌ Analysis Error ({time.strftime('%H:%M:%S')})"
                st.rerun() # Rerun to display the error


    # --- Display results from analysis (using analysis state vars) ---
    # This block displays results AFTER the analysis API call is complete (or failed) and state is set
    if st.session_state.analysis_response:
        st.markdown("---")
        st.subheader(f"Analysis Result for Request:")
        # Show the prompt that generated this result for context
        st.caption(f"> {st.session_state.analysis_prompt}")
        st.markdown("---")

        # Display the main response text
        st.markdown(st.session_state.analysis_response) # Use markdown for potential formatting

        # Display AI thoughts if they were extracted
        if st.session_state.analysis_thoughts:
            with st.expander("🤖 AI Thoughts/Reasoning", expanded=False): # Start collapsed
                st.markdown(st.session_state.analysis_thoughts) # Use markdown here too

        # Display TTS audio player if audio was generated
        if st.session_state.analysis_tts_audio:
            try:
                st.audio(st.session_state.analysis_tts_audio, format="audio/mp3")
            except Exception as audio_err:
                st.caption(f"Audio playback unavailable: {audio_err}")

        # Display download buttons if download data exists
        if st.session_state.analysis_downloads:
            st.markdown('<div class="download-buttons">', unsafe_allow_html=True)
            col_dl_1, col_dl_2, col_dl_spacer = st.columns([1, 1, 4])
            dl_data = st.session_state.analysis_downloads # Assign for clarity

            with col_dl_1:
                # Add safety check for key existence and non-None value
                if dl_data and dl_data.get("docx"):
                    st.download_button(
                        label="DOCX",
                        data=dl_data["docx"],
                        file_name=f"WM_Analysis_Result.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="analysis_docx_dl",
                        help="Download analysis result as DOCX"
                    )
            with col_dl_2:
                 if dl_data and dl_data.get("pdf"):
                    st.download_button(
                        label="PDF",
                        data=dl_data["pdf"],
                        file_name=f"WM_Analysis_Result.pdf",
                        mime="application/pdf",
                        key="analysis_pdf_dl",
                        help="Download analysis result as PDF"
                    )
            st.markdown('</div>', unsafe_allow_html=True)

        # Display final API status (success/error message from the analysis attempt)
        st.caption(st.session_state.api_call_status)


# --- Mode: Voice Command ---
elif st.session_state.current_mode == "🎤 Voice Command":
    if not sr_available or not audiorecorder_available:
        st.error("Voice command mode requires `SpeechRecognition` and `streamlit-audiorecorder` libraries. Please install them (`pip install SpeechRecognition streamlit-audiorecorder`) and restart.")
    else:
        st.info("Click the record button, speak your command clearly, then click stop. Your command will be transcribed and processed.")

        # Audio Recorder Widget - ensure it captures WAV format for SpeechRecognition
        audio_bytes_wav = audiorecorder("▶️ Record Command", "⏹️ Stop Recording", key='audio_recorder_main')

        if audio_bytes_wav:
            # Display the recorded audio player for confirmation
            st.audio(audio_bytes_wav, format="audio/wav") # Assume audiorecorder provides WAV

            # Clear previous results before processing new command
            st.session_state.voice_transcription = ""
            st.session_state.analysis_response = None # Reusing analysis state vars
            st.session_state.analysis_thoughts = None
            st.session_state.analysis_tts_audio = None
            st.session_state.analysis_downloads = None
            st.session_state.api_call_status = "⏳ Transcribing audio..."

            # --- Transcription ---
            with st.spinner("Transcribing your command..."):
                transcription = transcribe_audio_bytes(audio_bytes_wav)
                st.session_state.voice_transcription = transcription # Store transcription result (even if error/info)

            # --- Process the transcription result ---
            # Check if transcription was successful (i.e., produced text and not an error/info message)
            if transcription and not transcription.startswith(("[Error", "[Info")):
                st.success("Transcription Complete:")
                st.write(f"> _{transcription}_") # Display successful transcription
                st.session_state.api_call_status = "⏳ Processing command..."

                # --- Call Gemini with the transcribed text ---
                # Reusing the analysis state variables for response display simplicity
                voice_prompt = transcription
                prompt_with_request = voice_prompt
                # Add request for thoughts if not explicitly asked in voice command
                if "thought" not in voice_prompt.lower() and "reasoning" not in voice_prompt.lower():
                    prompt_with_request += "\n\n(Please also explain your thoughts/reasoning process under '***AI Thoughts:***')"

                api_contents_voice = [prompt_with_request] # Simple text prompt derived from voice

                with st.spinner("Processing your command with World Movers AI/AGI-Agent..."):
                     try:
                         # Use the main text model instance
                         response = model.generate_content(
                             api_contents_voice,
                             stream=False # Keep simple
                         )
                         # Process response
                         if response and response.text:
                             full_response_text = response.text
                             main_response = full_response_text
                             thoughts_text = ""
                             # Extract thoughts if present
                             if "***AI Thoughts:***" in full_response_text:
                                 try:
                                     parts = full_response_text.split("***AI Thoughts:***", 1)
                                     main_response = parts[0].strip(); thoughts_text = parts[1].strip()
                                 except Exception as split_err:
                                     print(f"Note: Failed to split thoughts in voice response: {split_err}")
                                     main_response = full_response_text; thoughts_text = "[Could not extract thoughts]"

                             # Store results in analysis state vars for display below
                             st.session_state.analysis_response = main_response
                             st.session_state.analysis_thoughts = thoughts_text
                             st.session_state.analysis_tts_audio = generate_tts_audio(main_response)
                             st.session_state.analysis_downloads = {"docx": create_docx_download(main_response),"pdf": create_pdf_download(main_response)}
                             st.session_state.api_call_status = f"✅ Voice command processed ({time.strftime('%H:%M:%S')})"

                             # Check for Quote trigger from voice command response
                             keywords_indicating_quote_ready = ["forward this information", "send these details", "forwarding this to our team", "forwarding the request", "quoting team", "pass this to the team", "email this quote request"]
                             positive_phrasing = ["will now attempt", "i will now forward", "i will forward", "i'll send this"]
                             if any(keyword in main_response.lower() for keyword in keywords_indicating_quote_ready) and \
                                any(phrase in main_response.lower() for phrase in positive_phrasing):
                                  print("Quote forwarding trigger detected in voice response.") # Debug
                                  st.session_state.send_email_flag = True
                                  st.session_state.email_content = (
                                      f"Mode: Voice Command\n"
                                      f"User Voice Command (Transcribed): {voice_prompt}\n\n"
                                      f"AI Response Triggering Send:\n---\n{main_response}\n---\n"
                                      f"\nAI Thoughts (if available):\n{thoughts_text if thoughts_text else 'N/A'}\n---"
                                      )
                                  # Let flag be checked at end of script
                         else:
                              # Handle empty response from API
                              st.error("Processing resulted in an empty response from the AI.", icon="❓")
                              st.session_state.analysis_response = "[Error: Received empty response from AI]"
                              st.session_state.api_call_status = f"❌ Empty Response ({time.strftime('%H:%M:%S')})"

                     except genai.types.generation_types.StopCandidateException as e:
                         error_msg = f"Processing stopped: The command or response might be blocked by safety filters ({e.reason})."
                         st.error(error_msg, icon="🚫")
                         st.session_state.analysis_response = f"[Error: Response blocked by API safety filter - {e.reason}]"
                         st.session_state.analysis_thoughts = None
                         st.session_state.api_call_status = f"❌ Processing Blocked ({time.strftime('%H:%M:%S')})"
                     except Exception as e:
                         error_msg = f"Processing failed: {type(e).__name__} - {e}"
                         st.error(error_msg, icon="🔥")
                         st.session_state.analysis_response = f"[Error during processing: {type(e).__name__}]"
                         st.session_state.analysis_thoughts = None
                         st.session_state.api_call_status = f"❌ Processing Error ({time.strftime('%H:%M:%S')})"
                     # No rerun here, let results display below in the same run

            else:
                 # Handle transcription failure or info message (e.g., "Could not understand audio")
                 st.warning(f"Transcription Result: {transcription}", icon="⚠️")
                 st.session_state.api_call_status = f"⚠️ Transcription issue ({time.strftime('%H:%M:%S')})"
                 # Ensure no leftover results from previous runs are displayed
                 st.session_state.analysis_response = None
                 st.session_state.analysis_thoughts = None
                 st.session_state.analysis_tts_audio = None
                 st.session_state.analysis_downloads = None


        # --- Display results from voice command (uses analysis state vars) ---
        # This block displays results AFTER transcription and (attempted) processing is complete
        if st.session_state.analysis_response: # Only display if a response (even error msg) was generated
            st.markdown("---")
            st.subheader("Response to Voice Command:")
            # Show the transcription that led to this response
            if st.session_state.voice_transcription and not st.session_state.voice_transcription.startswith(("[Error", "[Info")):
                st.caption(f"> _{st.session_state.voice_transcription}_")
            elif st.session_state.voice_transcription: # Show info/error transcription if that's what we have
                 st.caption(f"> Transcription attempt: {st.session_state.voice_transcription}")

            st.markdown("---")
            # Display the main response (or error message stored in analysis_response)
            st.markdown(st.session_state.analysis_response)

            # Display thoughts if available
            if st.session_state.analysis_thoughts:
                with st.expander("🤖 AI Thoughts/Reasoning", expanded=False):
                    st.markdown(st.session_state.analysis_thoughts)

            # Display TTS if available
            if st.session_state.analysis_tts_audio:
                try:
                    st.audio(st.session_state.analysis_tts_audio, format="audio/mp3")
                except Exception as audio_err:
                     st.caption(f"Audio playback unavailable: {audio_err}")

            # Display Downloads if available
            if st.session_state.analysis_downloads:
                 st.markdown('<div class="download-buttons">', unsafe_allow_html=True)
                 col_dl_1, col_dl_2, col_dl_spacer = st.columns([1, 1, 4])
                 dl_data = st.session_state.analysis_downloads

                 with col_dl_1:
                     if dl_data and dl_data.get("docx"):
                         st.download_button(
                             label="DOCX", data=dl_data["docx"],
                             file_name="WM_VoiceCommand_Response.docx",
                             mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             key="voice_docx_dl", help="Download response as DOCX"
                             )
                 with col_dl_2:
                     if dl_data and dl_data.get("pdf"):
                         st.download_button(
                             label="PDF", data=dl_data["pdf"],
                             file_name="WM_VoiceCommand_Response.pdf",
                             mime="application/pdf", key="voice_pdf_dl", help="Download response as PDF"
                            )
                 st.markdown('</div>', unsafe_allow_html=True)

            # Display final status message
            st.caption(st.session_state.api_call_status)

        elif st.session_state.voice_transcription: # Case: Transcription finished but no analysis_response (e.g., transcription error)
            # Display only the status which should indicate the transcription issue
             st.caption(st.session_state.api_call_status)


# --- Mode: Live Webcam Analysis ---
elif st.session_state.current_mode == "👁️ Live Webcam":
    if not webrtc_available:
        st.error("Webcam mode requires `streamlit-webrtc` and `av` libraries. Please install them (`pip install streamlit-webrtc av`) and restart.")
    else:
        st.info(f"The AI will periodically analyze the webcam feed (approx. every {analysis_interval_webcam}s). Results appear below the feed.")
        # Instructions Box
        st.markdown(f"""
        <div class="instructions-box">
            <h3>How to Use Live Webcam Analysis</h3>
            <ol>
                <li>Click <strong>'Start'</strong> below the video area.</li>
                <li>Allow your browser permission to access the webcam when prompted.</li>
                <li>Point the camera at items relevant to logistics (packages, labels, equipment).</li>
                <li>The AI automatically analyzes the feed every ~{analysis_interval_webcam} seconds (analysis itself takes time).</li>
                <li>The latest analysis result and AI thoughts (if any) will appear below the video feed.</li>
                <li>Click <strong>'Stop'</strong> to end the stream and analysis.</li>
            </ol>
            <p><strong>Notes:</strong> Requires a working webcam. Analysis quality depends heavily on lighting, camera focus, and resolution. Results are periodic, not instantaneous.</p>
        </div>
        """, unsafe_allow_html=True)

        # Initialize VideoProcessor instance in session state if it doesn't exist
        if "webcam_processor" not in st.session_state or st.session_state.webcam_processor is None:
            print("Initializing Webcam VideoProcessor") # Debug
            st.session_state.webcam_processor = VideoProcessor(mode="webcam")

        # WebRTC Streamer Component for Webcam
        webrtc_ctx_webcam = webrtc_streamer(
            key="webcam_live_analysis",
            mode=WebRtcMode.SENDRECV, # Send frames, receive them back (processor analyzes on send path)
            rtc_configuration=RTC_CONFIG,
            # Provide a factory function that returns the processor instance from session state
            video_processor_factory=lambda: st.session_state.webcam_processor,
            media_stream_constraints={"video": True, "audio": False}, # Request video only
            async_processing=True, # Essential for non-blocking UI
            # Use custom HTML attributes for styling from CSS
            video_html_attrs={"class": "webrtc-container", "autoPlay": True, "controls": False, "muted": True}
        )

        # Display Status and Results Below the Feed
        # Determine status based on webrtc state and session state status variable
        status_display = "Idle" # Default
        if webrtc_ctx_webcam.state.playing:
            status_display = st.session_state.get('webcam_status', 'Streaming...') # Show analysis status if streaming
        else:
             status_display = "Stopped" # Explicitly stopped

        st.markdown(f"<div class='media-status'>Status: {status_display}</div>", unsafe_allow_html=True)

        # Display the latest analysis result if available (and stream is/was playing)
        # Keep showing last result even after stop? Let's do that.
        latest_result = st.session_state.get("webcam_analysis_result")
        if latest_result:
            st.markdown("---")
            st.subheader("Latest Webcam Analysis")
            # Check if the result indicates an error or blockage
            if latest_result.startswith(("[Error", "[Analysis Blocked", "[Analysis Error")):
                 st.warning(latest_result, icon="⚠️") # Use warning for errors/blocks
            else:
                 st.markdown(latest_result) # Display normal result

            # Display thoughts if available and not empty
            latest_thoughts = st.session_state.get("webcam_thoughts")
            if latest_thoughts:
                with st.expander("🤖 AI Thoughts/Reasoning", expanded=False):
                    st.markdown(latest_thoughts)

        # Add a note if stopped but results are shown
        if not webrtc_ctx_webcam.state.playing and latest_result:
             st.caption("Stream stopped. Last analysis result shown above.")


# --- Mode: Screen Analysis ---
elif st.session_state.current_mode == "💻 Screen Analysis":
    if not webrtc_available:
         st.error("Screen Analysis mode requires `streamlit-webrtc` and `av` libraries. Please install them (`pip install streamlit-webrtc av`) and restart.")
    else:
        st.info("Share your screen (tab, window, or full screen), then use the chat box below the feed to ask specific questions about the shared content.")
        # Instructions Box
        st.markdown("""
        <div class="instructions-box">
            <h3>How to Use Screen Analysis</h3>
            <ol>
                <li>Click <strong>'Start'</strong> below the video area.</li>
                <li>Your browser will prompt you to choose what to share (a specific <strong>Window</strong> or <strong>Tab</strong> is usually best for clarity, or select <strong>Entire Screen</strong>).</li>
                <li>Once sharing starts and content is visible in the feed, use the <strong>chat box below the feed</strong> to ask questions.</li>
                <li>The AI analyzes the <em>current screen frame</em> when you submit your question.</li>
                <li>Analysis results appear in the chat history below.</li>
                <li>Click <strong>'Stop'</strong> to end screen sharing.</li>
            </ol>
            <p><strong>Notes:</strong> Works best in modern browsers (Chrome, Edge, Firefox recommended). Quality depends on shared content resolution and network speed. Analysis is triggered by your questions.</p>
        </div>
        """, unsafe_allow_html=True)

        # --- WebRTC Streamer for Screen Share ---
        # Mode is SENDONLY, analysis happens based on chat input using stored frame from callback
        webrtc_ctx_screen = webrtc_streamer(
            key="screen_share_analysis",
            mode=WebRtcMode.SENDONLY, # Only send the screen frames
            rtc_configuration=RTC_CONFIG,
            media_stream_constraints={
                "video": {
                    "displaySurface": "monitor", # Common setting, allows choosing tab/window/screen
                    "width": {"ideal": 1920, "max": 1920}, # Request good resolution
                    "height": {"ideal": 1080, "max": 1080},
                    "frameRate": {"ideal": 5, "max": 10} # Low framerate is sufficient for analysis
                    },
                "audio": False # No audio needed for analysis
            },
            # No video processor needed here, using callback
            video_frame_callback=screen_frame_callback, # Stores frame in st.session_state.current_screen_frame_pil
            async_processing=True,
            # Use custom HTML attributes for styling
            video_html_attrs={"class": "webrtc-container", "autoPlay": True, "controls": False, "muted": True}
        )

        # Display Status Below Feed
        screen_status = "Stopped"
        if webrtc_ctx_screen.state.playing:
             # Check if the callback has successfully stored a frame yet
             if st.session_state.get('current_screen_frame_pil') is None:
                  screen_status = "Starting stream, waiting for frame..."
             else:
                  screen_status = "Sharing Active - Ready for questions below"
        st.markdown(f"<div class='media-status'>Status: {screen_status}</div>", unsafe_allow_html=True)

        # --- Screen Analysis Chat Interface ---
        st.markdown("---")
        st.subheader("Ask About Shared Screen Content")

        # Define chat container with specific styling class and fixed height
        chat_container = st.container(height=400, border=True)
        with chat_container:
            # Apply custom class styling wrapper if needed (already in CSS)
            # chat_container.markdown('<div class="screen-chat-container">', unsafe_allow_html=True)

            # Display screen chat history within the container
            for i, msg in enumerate(st.session_state.screen_chat):
                avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"], avatar=avatar):
                    # Display main content
                    st.markdown(msg["content"], unsafe_allow_html=False) # Use False for safety
                    # Display thoughts in an expander for assistant messages
                    if msg["role"] == "assistant" and msg.get("thoughts"):
                        with st.expander("AI Thoughts", expanded=False): # Keep collapsed
                            st.markdown(msg["thoughts"]) # Use markdown for thoughts too

            # Close the custom div if used
            # chat_container.markdown('</div>', unsafe_allow_html=True)

        # Input for screen analysis chat - disable if not actively sharing and frame available
        screen_prompt_disabled = not (webrtc_ctx_screen.state.playing and st.session_state.get('current_screen_frame_pil') is not None)
        screen_prompt_placeholder = "What should I analyze on the screen?" if not screen_prompt_disabled else "Start sharing and wait for frame..."

        screen_prompt = st.chat_input(
            placeholder=screen_prompt_placeholder,
            key="screen_chat_input_widget",
            disabled=screen_prompt_disabled,
            # on_submit=lambda: st.session_state.update(api_call_status="") # Clear status on new input? Maybe not needed.
        )

        # --- Process User Input (if provided and valid) ---
        if screen_prompt:
            # Double-check if frame is available before proceeding (should match disabled state)
            if st.session_state.get('current_screen_frame_pil') is None:
                st.error("⚠️ Cannot analyze: Screen frame not captured or stream inactive. Ensure sharing is active.", icon="🖼️")
            else:
                # Add user message to screen chat history
                st.session_state.screen_chat.append({"role": "user", "content": screen_prompt})
                # Clear previous analysis status for screen chat
                st.session_state.api_call_status = "⏳ Preparing screen analysis..."
                # Rerun to display user message in chat and trigger AI analysis logic below
                st.rerun()

        # --- Trigger AI Analysis (if last message is from user and frame exists) ---
        # Check if the last message was from the user to trigger AI response
        if st.session_state.screen_chat and st.session_state.screen_chat[-1]["role"] == "user":
            last_user_query_screen = st.session_state.screen_chat[-1]["content"]
            current_frame_to_analyze = st.session_state.get('current_screen_frame_pil')

            # Ensure we still have a frame to analyze (user might stop sharing between runs)
            if current_frame_to_analyze is not None:
                 with st.spinner("Analyzing shared screen content..."):
                    try:
                        analysis_prompt_screen = last_user_query_screen
                        # Add request for thoughts
                        if "thought" not in analysis_prompt_screen.lower() and "reasoning" not in analysis_prompt_screen.lower():
                            analysis_prompt_screen += "\n\n(Please also explain your thoughts/reasoning process under '***AI Thoughts:***')"

                        # Prepare API contents (prompt text + PIL image)
                        contents_screen = [analysis_prompt_screen, current_frame_to_analyze]

                        # Use the vision model instance
                        response = vision_model.generate_content(
                            contents_screen,
                            stream=False # Keep simple for chat display
                        )

                        # Process response
                        if response and response.text:
                            full_response_text = response.text
                            main_response = full_response_text
                            thoughts_text = ""
                            # Extract thoughts if present
                            if "***AI Thoughts:***" in full_response_text:
                                 try:
                                     parts = full_response_text.split("***AI Thoughts:***", 1)
                                     main_response = parts[0].strip(); thoughts_text = parts[1].strip()
                                 except Exception as split_err:
                                     print(f"Note: Failed to split thoughts in screen response: {split_err}")
                                     main_response = full_response_text; thoughts_text = "[Could not extract thoughts]"

                            # Add assistant response (including thoughts) to screen chat history
                            st.session_state.screen_chat.append({
                                "role": "assistant",
                                "content": main_response,
                                "thoughts": thoughts_text # Store thoughts separately
                            })
                            st.session_state.api_call_status = f"✅ Screen analyzed ({time.strftime('%H:%M:%S')})"
                        else:
                            # Handle empty API response
                            st.error("Screen analysis resulted in an empty response from the AI.", icon="❓")
                            st.session_state.screen_chat.append({"role": "assistant", "content": "[Error: Received empty response from AI]", "thoughts": ""})
                            st.session_state.api_call_status = f"❌ Empty Response ({time.strftime('%H:%M:%S')})"

                        # Rerun to display the assistant's response in the chat container
                        st.rerun()

                    except genai.types.generation_types.StopCandidateException as e:
                        error_msg = f"Screen analysis stopped: Content might be blocked by safety filters ({e.reason})."
                        st.error(error_msg, icon="🚫")
                        st.session_state.screen_chat.append({"role": "assistant", "content": f"[Error: Response blocked by API safety filter - {e.reason}]", "thoughts": ""})
                        st.session_state.api_call_status = f"❌ Screen Analysis Blocked ({time.strftime('%H:%M:%S')})"
                        st.rerun() # Rerun to display error in chat
                    except Exception as e:
                        error_msg = f"Screen analysis failed: {type(e).__name__} - {e}"
                        st.error(error_msg, icon="🔥")
                        st.session_state.screen_chat.append({"role": "assistant", "content": f"[Error during screen analysis: {type(e).__name__}]", "thoughts": ""})
                        st.session_state.api_call_status = f"❌ Screen Analysis Error ({time.strftime('%H:%M:%S')})"
                        st.rerun() # Rerun to display error in chat
            else:
                # This case might happen if user stops sharing exactly between prompt submission and analysis run
                st.warning("Screen sharing stopped or frame became unavailable before analysis could run.", icon="⚠️")
                st.session_state.api_call_status = "⚠️ Screen unavailable for analysis."
                # Optionally add a message to chat? Or just rely on the warning.
                # st.session_state.screen_chat.append({"role": "assistant", "content": "[Info: Screen sharing stopped before analysis could complete.]", "thoughts": ""})
                # st.rerun() # Rerun to show the warning/chat message

        # Display API status below chat (e.g., for errors shown via st.error)
        # Could refine this to only show if needed
        # if st.session_state.api_call_status and ("❌" in st.session_state.api_call_status or "⚠️" in st.session_state.api_call_status):
        #      st.caption(st.session_state.api_call_status)


# --- Mode: Take Picture Analysis ---
elif st.session_state.current_mode == "📸 Take Picture Analysis":
    if not webrtc_available:
        st.error("Take Picture mode requires `streamlit-webrtc` and `av` libraries for camera access. Please install them (`pip install streamlit-webrtc av`) and restart.")
    else:
        st.info("Capture a picture using your camera below, then ask a question about its content.")
        # Use a dynamic key for the camera input widget to allow reset
        picture_capture_key = f"picture_mode_cam_{st.session_state.get('picture_mode_count', 0)}"
        captured_picture_data = st.camera_input(
            "Take Picture for Analysis",
            key=picture_capture_key,
            help="Use your webcam to capture an image. The AI will analyze it based on your question."
            )

        # --- Process newly captured picture ---
        if captured_picture_data:
            new_pic_bytes = captured_picture_data.getvalue()
            # Check if new bytes are different from last processed OR if no image was processed before
            if new_pic_bytes != st.session_state.get('last_picture_image_bytes'):
                with st.spinner("Processing picture..."):
                    try:
                        print("Processing new picture for analysis mode.") # Debug
                        img = Image.open(io.BytesIO(new_pic_bytes))
                        # Ensure RGB format (safe default)
                        if img.mode not in ['RGB', 'RGBA', 'L']:
                            img = img.convert('RGB')

                        st.session_state.picture_mode_image = img # Store PIL Image
                        st.session_state.last_picture_image_bytes = new_pic_bytes # Store bytes marker

                        # Increment counter for camera key reset on next interaction
                        st.session_state.picture_mode_count = st.session_state.get('picture_mode_count', 0) + 1

                        # IMPORTANT: Clear results and prompt from any *previous* picture analysis run
                        st.session_state.analysis_response = None
                        st.session_state.analysis_thoughts = None
                        st.session_state.analysis_tts_audio = None
                        st.session_state.analysis_downloads = None
                        st.session_state.api_call_status = ""
                        st.session_state.picture_mode_prompt = "" # Clear prompt field for new image

                        st.rerun() # Rerun immediately to display the new image and clear old results

                    except UnidentifiedImageError:
                         st.error("Failed to identify image format. Please capture a standard format (JPG, PNG, etc.).")
                         st.session_state.picture_mode_image = None
                         st.session_state.last_picture_image_bytes = None
                    except Exception as e:
                        st.error(f"Failed to process captured picture: {e}")
                        st.session_state.picture_mode_image = None
                        st.session_state.last_picture_image_bytes = None

        # --- Clear state if camera input becomes None (user clears picture) ---
        if captured_picture_data is None and st.session_state.get('last_picture_image_bytes') is not None:
             print("Camera input cleared by user, resetting picture analysis state.")
             st.session_state.picture_mode_image = None
             st.session_state.last_picture_image_bytes = None
             # Also clear results and prompt associated with the cleared picture
             st.session_state.analysis_response = None
             st.session_state.analysis_thoughts = None
             st.session_state.analysis_tts_audio = None
             st.session_state.analysis_downloads = None
             st.session_state.api_call_status = ""
             st.session_state.picture_mode_prompt = ""
             # Increment counter to reset camera widget key on next run
             st.session_state.picture_mode_count = st.session_state.get('picture_mode_count', 0) + 1
             st.rerun() # Rerun to update UI

        # --- UI for Analysis (Only if an Image is successfully loaded and stored) ---
        current_image_pil = st.session_state.get("picture_mode_image") # Get image from state
        if current_image_pil and isinstance(current_image_pil, Image.Image):
            # Display the captured image prominently
            st.image(current_image_pil, caption="Image captured - Ready for analysis", use_container_width=False, width=400) # Adjust width as needed
            st.markdown("---")

            # --- Prompt Input Area ---
            # Use session state to store the prompt value *before* the API call
            picture_prompt_input = st.text_area(
                "Ask about this picture:",
                height=100,
                key="picture_mode_prompt_widget", # Unique key for the widget
                # Keep the prompt value in the text area if analysis was triggered
                value=st.session_state.get("picture_mode_prompt", ""),
                placeholder="e.g., What type of shipping label is this?\nIdentify the item in the box.\nRead the text near the top right corner."
            )
            # Update session state immediately as user types (or retrieve on button press)
            # Let's update state only when button is pressed for simplicity
            # st.session_state.picture_mode_prompt = picture_prompt_input.strip() # Removed immediate update


            # --- Submit Button ---
            submit_picture_analysis = st.button(
                "Analyze Picture",
                type="primary",
                # Disable button ONLY if the prompt text area is empty
                disabled=(not picture_prompt_input or not picture_prompt_input.strip()),
                key="submit_picture_analysis_btn"
                )

            # --- API Call Logic (Triggered by Button Click) ---
            if submit_picture_analysis:
                # Store the current prompt text in session state *now*
                st.session_state.picture_mode_prompt = picture_prompt_input.strip()

                # Clear previous analysis display state before starting new analysis
                st.session_state.analysis_response = None
                st.session_state.analysis_thoughts = None
                st.session_state.analysis_tts_audio = None
                st.session_state.analysis_downloads = None
                st.session_state.api_call_status = "⏳ Analyzing picture..." # Set status for spinner
                st.rerun() # Rerun immediately to show the spinner and proceed to analysis execution block


        # --- Execute Analysis (if status indicates pending analysis) ---
        # This block runs *after* the rerun triggered by the button click + status set
        if st.session_state.api_call_status == "⏳ Analyzing picture...":
             # Retrieve the necessary data from session state again
             prompt_to_analyze = st.session_state.get("picture_mode_prompt", "")
             image_to_analyze = st.session_state.get("picture_mode_image") # Should still be the same image

             if prompt_to_analyze and image_to_analyze and isinstance(image_to_analyze, Image.Image):
                # Prepare API contents (prompt + image)
                prompt_with_request = prompt_to_analyze
                if "thought" not in prompt_with_request.lower() and "reasoning" not in prompt_with_request.lower():
                    prompt_with_request += "\n\n(Please also explain your thoughts/reasoning process under '***AI Thoughts:***')"

                api_contents_picture = [prompt_with_request, image_to_analyze] # Text prompt first, then image

                # Call Gemini API - No spinner needed here, was shown before rerun
                try:
                    response = vision_model.generate_content(
                         api_contents_picture,
                         stream=False
                    )
                    # Process response, extract thoughts, set state variables for display
                    if response and response.text:
                        full_response_text = response.text
                        main_response = full_response_text; thoughts_text = ""
                        if "***AI Thoughts:***" in full_response_text:
                             try:
                                 parts = full_response_text.split("***AI Thoughts:***", 1)
                                 main_response = parts[0].strip(); thoughts_text = parts[1].strip()
                             except Exception as split_err:
                                 print(f"Note: Failed to split thoughts in picture response: {split_err}")
                                 main_response = full_response_text; thoughts_text = "[Could not extract thoughts]"

                        st.session_state.analysis_response = main_response
                        st.session_state.analysis_thoughts = thoughts_text
                        st.session_state.analysis_tts_audio = generate_tts_audio(main_response)
                        st.session_state.analysis_downloads = {"docx": create_docx_download(main_response),"pdf": create_pdf_download(main_response)}
                        st.session_state.api_call_status = f"✅ Picture analysis complete ({time.strftime('%H:%M:%S')})"
                    else:
                         st.error("Picture analysis resulted in an empty response from the AI.", icon="❓")
                         st.session_state.analysis_response = "[Error: Received empty response from AI]"
                         st.session_state.api_call_status = f"❌ Empty Response ({time.strftime('%H:%M:%S')})"

                    st.rerun() # Rerun AGAIN to display the results (or empty error)

                except genai.types.generation_types.StopCandidateException as e:
                    error_msg = f"Picture analysis stopped: Content might be blocked by safety filters ({e.reason})."
                    st.error(error_msg, icon="🚫")
                    st.session_state.analysis_response = f"[Error: Response blocked by API safety filter - {e.reason}]"
                    st.session_state.analysis_thoughts = None
                    st.session_state.api_call_status = f"❌ Analysis Blocked ({time.strftime('%H:%M:%S')})"
                    st.rerun() # Rerun to show error message in display area
                except Exception as e:
                    error_msg = f"Picture analysis failed: {type(e).__name__} - {e}"
                    st.error(error_msg, icon="🔥")
                    st.session_state.analysis_response = f"[Error during picture analysis: {type(e).__name__}]"
                    st.session_state.analysis_thoughts = None
                    st.session_state.api_call_status = f"❌ Analysis Error ({time.strftime('%H:%M:%S')})"
                    st.rerun() # Rerun to show error message in display area
             else:
                 # Should not happen if button was enabled, but handle defensively
                 st.warning("Error: Missing prompt or image for analysis. Please capture image and enter prompt.", icon="⚠️")
                 st.session_state.api_call_status = "⚠️ Error: Missing data."
                 # Don't rerun here, let the warning show


        # --- Display results from Picture Analysis (uses analysis state vars) ---
        # This block runs *after* the analysis attempt and subsequent rerun completes
        # It displays the results stored in session state by the execution block above
        if st.session_state.analysis_response:
            st.markdown("---")
            st.subheader("Picture Analysis Result:")
            # Display the prompt that led to this result for context
            st.caption(f"> {st.session_state.get('picture_mode_prompt', 'N/A')}")
            st.markdown("---")
            # Display main response
            st.markdown(st.session_state.analysis_response)
            # Display thoughts
            if st.session_state.analysis_thoughts:
                with st.expander("🤖 AI Thoughts/Reasoning", expanded=False):
                    st.markdown(st.session_state.analysis_thoughts)
            # Display TTS
            if st.session_state.analysis_tts_audio:
                try:
                    st.audio(st.session_state.analysis_tts_audio, format="audio/mp3")
                except Exception as audio_err:
                    st.caption(f"Audio playback unavailable: {audio_err}")
            # Display Downloads
            if st.session_state.analysis_downloads:
                st.markdown('<div class="download-buttons">', unsafe_allow_html=True)
                col_dl_1, col_dl_2, col_dl_spacer = st.columns([1, 1, 4])
                dl_data = st.session_state.analysis_downloads
                with col_dl_1:
                     if dl_data and dl_data.get("docx"):
                        st.download_button(
                            label="DOCX", data=dl_data["docx"],
                            file_name="WM_Picture_Analysis.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="pic_docx_dl", help="Download result as DOCX"
                        )
                with col_dl_2:
                     if dl_data and dl_data.get("pdf"):
                         st.download_button(
                            label="PDF", data=dl_data["pdf"],
                            file_name="WM_Picture_Analysis.pdf",
                            mime="application/pdf",
                            key="pic_pdf_dl", help="Download result as PDF"
                        )
                st.markdown('</div>', unsafe_allow_html=True)

            # Display final status message
            st.caption(st.session_state.api_call_status)
# --- PREVIOUS CODE FOR OTHER MODES (Chat, Doc/Image Analysis, etc.) ---
# --- (Previous mode blocks) ---

# --- +++ NEW MODE: News Feed +++ ---
elif st.session_state.current_mode == "📰 News Feed":
    st.header("📰 Latest Logistics and Freight Forwarding News")
    st.markdown("<p class='tab-description'>Recent news with AI-powered sentiment analysis, fetched from NewsAPI.</p>", unsafe_allow_html=True)
    
    # --- Check for NewsAPI library availability ---
    if not newsapi_available:
        st.error("The News Feed mode requires the `newsapi-python` library. Please install it (`pip install newsapi-python`) and restart the application.")
    else:
        # Wrapper for scrollable content
        st.markdown('<div class="scrollable-tab-content">', unsafe_allow_html=True)

        st.caption(f"News fetched around {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. Data cached for ~30 mins.")

        news_keywords = [
            # Company and Region Specific
            "World Movers Phils",
            "Philippines logistics",
            "Manila port",
            
    
            # Core Logistics Services
            "freight forwarding",
            "supply chain management",
            "air cargo",
            "ocean freight",
            "customs brokerage",
    
            # Major Industry Topics
            "freight rates",
            "shipping industry trends",
            "port congestion",
            "logistics technology"
        ]
        st.info(f"**Searching NewsAPI for keywords:** `{', '.join(news_keywords)}`")

        news_refresh_disabled = not NEWSAPI_API_KEY
        news_refresh_tooltip = "NewsAPI Key is missing in environment variables." if news_refresh_disabled else "Fetch latest news (clears cache)"

        if st.button("🔄 Refresh News Feed", key="refresh_news_btn", disabled=news_refresh_disabled, help=news_refresh_tooltip):
            # Clear all data cache, which includes the news feed function's cache
            st.cache_data.clear()
            st.success("News cache cleared. Fetching fresh results...", icon="🔄")
            st.rerun()

        if news_refresh_disabled:
            st.warning("News feed is disabled. Please configure the `NEWSAPI_API_KEY` environment variable in your Cloud Run service.", icon="🔒")
        else:
            with st.spinner("📰 Loading news feed from NewsAPI & analyzing sentiment..."):
                news_items = fetch_news_from_newsapi(NEWSAPI_API_KEY, news_keywords)

            # Check for errors returned by the fetch function
            if news_items and isinstance(news_items[0], dict) and news_items[0].get("type") == "error":
                st.error(f"Could not fetch news: {news_items[0].get('content', 'Unknown error')}", icon="🔥")
            elif news_items:
                st.markdown(f"Found **{len(news_items)}** relevant news articles:")
                st.markdown("---")
                for item in news_items:
                    sentiment = item.get('sentiment', '⚪')
                    st.markdown(f"""
                    <div class="news-item">
                        <h3>{sentiment} <a href="{item['link']}" target="_blank" title="{item.get('snippet', 'Click to read more')}">{item['title']}</a></h3>
                        <p>{item.get('snippet', 'No snippet available.')}</p>
                        <div class="news-date">📅 Published: {item.get('date', 'Date unavailable')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.caption("Sentiment (🟢/⚪/🔴) is AI-generated based on simple keyword analysis and is approximate.")
            else:
                st.info("No recent news items found matching the keywords.")

        # Close the scrollable content wrapper
        st.markdown('</div>', unsafe_allow_html=True)
# --- +++ END OF NEW MODE +++ ---


# --- +++ NEW MODE: Drone Operations Simulation +++ ---
elif st.session_state.current_mode == "🚁 Drone Operations Simulation":
    st.title("🚁 Drone Operations Simulation")

    if not pandas_available:
        st.error("This Drone Operations Simulation mode requires the `pandas` library to display maps. Please ensure it is installed.")
    else:
        st.warning(
            "**Disclaimer:** This is a **visual simulation** for conceptual purposes only. "
            "It does not control real drones or reflect live operational data. "
            "All drone movements and statuses are simulated within this application."
        )
        st.markdown("---")

        # Initialize simulated drone data in session state if it doesn't exist
        if 'sim_drones' not in st.session_state:
            st.session_state.sim_drones = {
                "Alpha-001": {
                    "name": "Alpha-001", "status": "Idle", "battery_pct": 98,
                    "current_lat": 14.5547, "current_lon": 121.0244, # Manila (example base)
                    "base_lat": 14.5547, "base_lon": 121.0244,
                    "target_lat": None, "target_lon": None, "target_name": None,
                    "color": [255, 0, 0, 160], # RGBA for st.map marker color (Red)
                    "size": 1000 # Size for st.map marker
                },
                "Beta-007": {
                    "name": "Beta-007", "status": "Idle", "battery_pct": 95,
                    "current_lat": 14.5580, "current_lon": 121.0200, # Near Manila base
                    "base_lat": 14.5580, "base_lon": 121.0200,
                    "target_lat": None, "target_lon": None, "target_name": None,
                    "color": [0, 0, 255, 160], # Blue
                    "size": 1000
                },
                "Gamma-042": {
                    "name": "Gamma-042", "status": "Idle", "battery_pct": 99,
                    "current_lat": 14.5500, "current_lon": 121.0280, # Another spot
                    "base_lat": 14.5500, "base_lon": 121.0280,
                    "target_lat": None, "target_lon": None, "target_name": None,
                    "color": [0, 255, 0, 160], # Green
                    "size": 1000
                }
            }
            # Initial map view settings
            st.session_state.drone_map_center_lat = 14.5547
            st.session_state.drone_map_center_lon = 121.0244
            st.session_state.drone_map_zoom = 11

        # --- Helper function for simulation ---
        def simulate_drone_step(drone_id, step_fraction=0.15):
            drone = st.session_state.sim_drones[drone_id]
            if drone["status"] == "Deploying to Target" and drone["target_lat"] is not None:
                # Move towards target
                delta_lat = drone["target_lat"] - drone["current_lat"]
                delta_lon = drone["target_lon"] - drone["current_lon"]
                drone["current_lat"] += delta_lat * step_fraction
                drone["current_lon"] += delta_lon * step_fraction
                drone["battery_pct"] = max(0, drone["battery_pct"] - 2) # Simulate battery drain

                # Check if close to target
                if abs(drone["current_lat"] - drone["target_lat"]) < 0.0005 and \
                   abs(drone["current_lon"] - drone["target_lon"]) < 0.0005:
                    drone["status"] = "At Target"
                    drone["current_lat"] = drone["target_lat"] # Snap to target
                    drone["current_lon"] = drone["target_lon"]
            elif drone["status"] == "Returning to Base":
                # Move towards base
                delta_lat = drone["base_lat"] - drone["current_lat"]
                delta_lon = drone["base_lon"] - drone["current_lon"]
                drone["current_lat"] += delta_lat * step_fraction
                drone["current_lon"] += delta_lon * step_fraction
                drone["battery_pct"] = max(0, drone["battery_pct"] - 1)

                # Check if close to base
                if abs(drone["current_lat"] - drone["base_lat"]) < 0.0005 and \
                   abs(drone["current_lon"] - drone["base_lon"]) < 0.0005:
                    drone["status"] = "Idle"
                    drone["current_lat"] = drone["base_lat"] # Snap to base
                    drone["current_lon"] = drone["base_lon"]
                    drone["target_lat"], drone["target_lon"], drone["target_name"] = None, None, None
                    drone["battery_pct"] = min(100, drone["battery_pct"] + 15) # Simulate some recharge/swap at base

            st.session_state.sim_drones[drone_id] = drone # Update state

        # --- UI Layout ---
        col_controls, col_map = st.columns([1, 2])

        with col_controls:
            st.subheader("Drone Control Panel")
            selected_drone_id = st.selectbox(
                "Select Drone:",
                options=list(st.session_state.sim_drones.keys()),
                format_func=lambda x: st.session_state.sim_drones[x]["name"] + f" (Status: {st.session_state.sim_drones[x]['status']})"
            )

            if selected_drone_id:
                drone = st.session_state.sim_drones[selected_drone_id]
                st.write(f"**Name:** {drone['name']}")
                st.write(f"**Status:** {drone['status']}")
                st.write(f"**Battery:** {drone['battery_pct']}%")
                st.write(f"**Current Location:** {drone['current_lat']:.4f}, {drone['current_lon']:.4f}")
                if drone["target_name"]:
                    st.write(f"**Target:** {drone['target_name']} ({drone['target_lat']:.4f}, {drone['target_lon']:.4f})")

                st.markdown("---")
                st.markdown("#### Mission Assignment")
                new_target_name = st.text_input("Target Name/Description", key=f"target_name_{selected_drone_id}", value=drone.get("target_name",""))
                new_target_lat = st.number_input("Target Latitude", format="%.6f", key=f"target_lat_{selected_drone_id}", value=drone.get("target_lat") or drone["current_lat"] + 0.01)
                new_target_lon = st.number_input("Target Longitude", format="%.6f", key=f"target_lon_{selected_drone_id}", value=drone.get("target_lon") or drone["current_lon"] + 0.01)

                deploy_disabled = drone["status"] not in ["Idle"] or drone["battery_pct"] < 20
                if st.button("🚀 Deploy to Target", key=f"deploy_{selected_drone_id}", disabled=deploy_disabled):
                    if drone["battery_pct"] < 20:
                        st.error("Cannot deploy: Low battery!")
                    else:
                        drone["target_name"] = new_target_name
                        drone["target_lat"] = new_target_lat
                        drone["target_lon"] = new_target_lon
                        drone["status"] = "Deploying to Target"
                        st.session_state.sim_drones[selected_drone_id] = drone
                        st.success(f"{drone['name']} deploying to {new_target_name or 'coordinates'}.")
                        st.rerun()

                step_disabled = drone["status"] not in ["Deploying to Target", "Returning to Base"]
                if st.button("✈️ Simulate Flight Step", key=f"step_{selected_drone_id}", disabled=step_disabled):
                    simulate_drone_step(selected_drone_id)
                    st.rerun()
                
                return_disabled = drone["status"] in ["Idle", "Returning to Base"]
                if st.button("🏠 Return to Base", key=f"return_{selected_drone_id}", disabled=return_disabled):
                    drone["status"] = "Returning to Base"
                    st.session_state.sim_drones[selected_drone_id] = drone
                    st.info(f"{drone['name']} returning to base.")
                    st.rerun()

                if drone["battery_pct"] < 20 and drone["status"] != "Idle":
                    st.warning(f"Low battery for {drone['name']}! Consider returning to base.")

        with col_map:
            st.subheader("Live Drone Map (Simulated)")

            map_data_points = []
            # Add current drone locations
            for drone_id, drone_info in st.session_state.sim_drones.items():
                map_data_points.append({
                    "lat": drone_info["current_lat"],
                    "lon": drone_info["current_lon"],
                    "color": drone_info["color"], # Use the drone's specific color
                    "size": drone_info["size"] * (1.5 if drone_id == selected_drone_id else 1.0) # Highlight selected
                })
                # Add target marker if drone is deployed and has a target
                if drone_info["status"] in ["Deploying to Target", "At Target"] and \
                   drone_info["target_lat"] is not None and drone_info["target_lon"] is not None:
                    map_data_points.append({
                        "lat": drone_info["target_lat"],
                        "lon": drone_info["target_lon"],
                        "color": [255, 165, 0, 120], # Orange, semi-transparent for target
                        "size": 600 # Smaller marker for target
                    })

            if map_data_points:
                df_map = pd.DataFrame(map_data_points)
                # Center map on selected drone or general area
                if selected_drone_id and st.session_state.sim_drones[selected_drone_id]["status"] != "Idle":
                    center_lat = st.session_state.sim_drones[selected_drone_id]["current_lat"]
                    center_lon = st.session_state.sim_drones[selected_drone_id]["current_lon"]
                else:
                    center_lat = st.session_state.drone_map_center_lat
                    center_lon = st.session_state.drone_map_center_lon
                
                # Simple way to set a reasonable zoom based on whether a target is active
                current_zoom = st.session_state.drone_map_zoom
                if selected_drone_id and st.session_state.sim_drones[selected_drone_id]["target_lat"] is not None:
                    # Calculate rough distance to target to adjust zoom - very basic
                    drone = st.session_state.sim_drones[selected_drone_id]
                    dist_sq = (drone["current_lat"] - drone["target_lat"])**2 + (drone["current_lon"] - drone["target_lon"])**2
                    if dist_sq > 0.01: # Further away
                        current_zoom = 9
                    elif dist_sq > 0.001:
                        current_zoom = 10
                    else: # Closer
                        current_zoom = 12


                st.map(df_map, latitude=center_lat, longitude=center_lon, zoom=current_zoom, color='color', size='size')
            else:
                st.map(pd.DataFrame({'lat': [st.session_state.drone_map_center_lat], 'lon': [st.session_state.drone_map_center_lon]}), zoom=st.session_state.drone_map_zoom)

            st.caption("Red/Blue/Green markers are drones. Orange markers indicate active targets. Selected drone is larger.")
            if st.button("Reset All Drones & View", key="reset_drones_map"):
                del st.session_state.sim_drones # This will trigger re-initialization on next run
                st.rerun()

# --- +++ NEW MODE: Freight Calculators +++ ---
elif st.session_state.current_mode == "🛠️ Freight Calculators":
    st.info("Access various freight calculation tools provided by Freightos. Note: These are external tools embedded for convenience.")
    st.markdown("""
    <div class="instructions-box">
        <h3>Freight Calculation Tools</h3>
        <p>
            Use the tabs below to access different calculators for estimating freight rates, transit times, import duties, container shipping costs, and emissions.
            These tools are provided by <a href="https://www.freightos.com/freight-resources/" target="_blank">Freightos</a>.
            For the best experience or more advanced features, please visit their website directly.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # URLs for the calculators (as provided in the prompt)
    freight_rate_url = "https://www.freightos.com/freight-resources/freight-rate-free-calculator/"
    transit_time_url = "https://www.freightos.com/freight-resources/transit-time-calculator/"
    import_duty_url = "https://www.freightos.com/freight-resources/import-duty-calculator/"
    container_cost_url = "https://www.freightos.com/freight-resources/container-shipping-cost-calculator-free-tool/"
    emissions_url = "https://www.freightos.com/freight-resources/emissions-calculator/"

    tab_titles = [
        "Freight Rate",
        "Transit Time",
        "Import Duty",
        "Container Cost",
        "Emissions"
    ]
    calculator_urls = [
        freight_rate_url,
        transit_time_url,
        import_duty_url,
        container_cost_url,
        emissions_url
    ]
    calculator_names = [
        "Freight Rate Calculator",
        "Transit Time Calculator",
        "Import Duty Calculator",
        "Container Shipping Cost Calculator",
        "Logistics Emissions Calculator"
    ]

    # Create tabs for each calculator
    tabs = st.tabs(tab_titles)

    for i, tab in enumerate(tabs):
        with tab:
            st.subheader(f"{calculator_names[i]}")
            st.markdown(f"""
                <p>
                    Use the embedded calculator below or <a href="{calculator_urls[i]}" target="_blank">visit the full {calculator_names[i]} on Freightos.com</a>.
                </p>
            """, unsafe_allow_html=True)
            
            # Embed the calculator using an iframe
            # Note: Some sites might block embedding via iframe (X-Frame-Options header)
            # If embedding fails, the user will still have the direct link.
            try:
                st.components.v1.iframe(calculator_urls[i], height=800, scrolling=True)
            except Exception as e:
                st.warning(f"Could not embed the calculator due to website restrictions or an error. Please use the direct link above. Error: {e}")
            
            st.markdown(f"<br><p style='text-align:center;'><a href='{calculator_urls[i]}' target='_blank' class='stButton'><button>Open {calculator_names[i]} in new tab</button></a></p>", unsafe_allow_html=True)

# --- FOLLOWING CODE FOR OTHER MODES OR FOOTER ---
# --- (Previous mode blocks) ---
# --- +++ NEW MODE: Basic Estimators +++ ---
elif st.session_state.current_mode == "🧮 Basic Estimators":
    st.title("🧮 Basic Logistics Estimators")
    st.warning(
        "**Disclaimer:** These are highly simplified estimators for illustrative purposes only. "
        "They do **not** use real-time data, comprehensive industry databases, or complex algorithms. "
        "**Do not use these for actual shipping, financial, or planning decisions.** "
        "Consult with World Movers Phils Inc. directly for accurate quotes and information."
    )
    st.markdown("---")

    # --- Create tabs for each simplified estimator ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Volume & Volumetric Weight",
        "⏱️ Simple Transit Time Idea",
        "💰 Basic Duty Idea",
        "💨 Rough Emissions Idea"
    ])

    # --- Tab 1: Basic Volume & Volumetric Weight Calculator ---
    with tab1:
        st.subheader("📦 Basic Volume & Volumetric Weight Estimator")
        st.caption("Calculates total cubic meters (CBM) and a simplified volumetric weight.")
        st.markdown("""
            **How it works (Simplified):**
            - **CBM:** (Length x Width x Height of one package) x Number of packages.
            - **Volumetric Weight (Air):** Total CBM x 167 (standard IATA factor for kg/CBM, or L*W*H(cm)/6000 per package).
            - **Volumetric Weight (LCL Sea):** Total CBM x 1000 (common factor for kg/CBM, or L*W*H(cm)/1000 per package).
            Freight charges are often based on the greater of actual weight or volumetric weight.
        """)

        col1_vol, col2_vol = st.columns(2)
        with col1_vol:
            st.markdown("#### Package Details")
            length_cm = st.number_input("Length per package (cm)", min_value=0.1, value=50.0, step=0.1, key="len_cm")
            width_cm = st.number_input("Width per package (cm)", min_value=0.1, value=40.0, step=0.1, key="wid_cm")
            height_cm = st.number_input("Height per package (cm)", min_value=0.1, value=30.0, step=0.1, key="hei_cm")
            num_packages = st.number_input("Number of identical packages", min_value=1, value=1, step=1, key="num_pack")

        cbm_per_package = (length_cm / 100) * (width_cm / 100) * (height_cm / 100)
        total_cbm = cbm_per_package * num_packages

        # Volumetric weight calculation (standard IATA for air: L*W*H in cm / 6000 = kg)
        vol_weight_air_per_package_kg = (length_cm * width_cm * height_cm) / 6000
        total_vol_weight_air_kg = vol_weight_air_per_package_kg * num_packages

        # Volumetric weight for LCL (common: 1 CBM = 1000 kg, or L*W*H in cm / 1000 = kg for LCL rule of thumb)
        vol_weight_lcl_per_package_kg = (length_cm * width_cm * height_cm) / 1000
        total_vol_weight_lcl_kg = vol_weight_lcl_per_package_kg * num_packages


        with col2_vol:
            st.markdown("#### Estimated Results")
            st.metric(label="Total Cubic Meters (CBM)", value=f"{total_cbm:.3f} m³")
            st.markdown("---")
            st.metric(label="Total Volumetric Weight (Air Freight Approx.)", value=f"{total_vol_weight_air_kg:.2f} kg")
            st.caption("(Based on L*W*H(cm)/6000 per package)")
            st.markdown("---")
            st.metric(label="Total Volumetric Weight (LCL Sea Freight Approx.)", value=f"{total_vol_weight_lcl_kg:.2f} kg")
            st.caption("(Based on L*W*H(cm)/1000 per package, or 1 CBM = 1000kg rule)")

        st.info("Note: Actual chargeable weight will be the greater of the total actual gross weight and the relevant total volumetric weight.")

    # --- Tab 2: Simplified Transit Time Estimator ---
    with tab2:
        st.subheader("⏱️ Simple Transit Time Idea")
        st.caption("A very basic estimation based on user-provided distance and speed.")
        st.markdown("""
            **How it works (Highly Simplified):**
            - Time = Distance / Average Speed.
            - **This ignores all real-world factors:** Port congestion, customs clearance, vessel schedules, direct vs. transshipment, weather, specific routes, waiting times, loading/unloading, inland transit, etc.
            - **You must provide the distance and an average speed.**
        """)
        origin_text = st.text_input("Origin (e.g., Port of Shanghai)", key="tt_origin", placeholder="For reference only")
        destination_text = st.text_input("Destination (e.g., Port of Long Beach)", key="tt_dest", placeholder="For reference only")
        distance_km = st.number_input("Assumed Direct Distance (km)", min_value=1.0, value=10000.0, step=100.0, key="tt_dist")
        avg_speed_kmh = st.number_input("Assumed Average Speed (km/h)", min_value=1.0, value=25.0, step=1.0, help="Ocean vessel avg speed ~20-40 km/h (10-20 knots). Air cargo ~800-900 km/h. Truck ~60-80 km/h.", key="tt_speed")

        if avg_speed_kmh > 0:
            estimated_hours = distance_km / avg_speed_kmh
            estimated_days = estimated_hours / 24
            st.metric(label="Estimated Transit (Hours - Continuous Travel)", value=f"{estimated_hours:.1f} hours")
            st.metric(label="Estimated Transit (Days - Continuous Travel)", value=f"{estimated_days:.1f} days")
        else:
            st.error("Average speed must be greater than 0.")

        st.error("**Critical Disclaimer:** This is a purely theoretical calculation based on your inputs. Actual transit times will vary significantly and are much more complex.")

    # --- Tab 3: Basic Import Duty Idea ---
    with tab3:
        st.subheader("💰 Basic Import Duty Idea")
        st.caption("Calculates a duty amount based on a flat percentage of goods value. **Highly inaccurate for real duties.**")
        st.markdown("""
            **How it works (Extremely Simplified):**
            - Estimated Duty = Value of Goods x (Assumed Duty Rate % / 100).
            - **This completely ignores:**
                - Specific Harmonized System (HS) codes for products (which determine actual rates).
                - Country of origin and destination (rates vary hugely).
                - Free Trade Agreements or preferential tariffs.
                - Anti-dumping duties, countervailing duties.
                - VAT, GST, Sales Tax, Excise Tax, or other local taxes.
                - Incoterms (which affect the dutiable value).
            - **This is for illustrative purposes ONLY to show a percentage calculation.**
        """)
        goods_value = st.number_input("Declared Value of Goods (e.g., in USD)", min_value=0.0, value=1000.0, step=10.0, key="duty_val")
        assumed_duty_rate_percent = st.number_input("Assumed Flat Duty Rate (%)", min_value=0.0, value=5.0, max_value=100.0, step=0.1, key="duty_rate")

        estimated_duty = goods_value * (assumed_duty_rate_percent / 100)
        st.metric(label=f"Estimated Duty Amount (at {assumed_duty_rate_percent}%)", value=f"{estimated_duty:.2f}")
        st.error("**Critical Disclaimer:** This is NOT a real import duty calculation. Actual duties are highly complex and depend on many factors not included here. Consult a customs broker or World Movers for accurate duty information.")

    # --- Tab 4: Rough Emissions Idea ---
    with tab4:
        st.subheader("💨 Rough Emissions Idea")
        st.caption("A very basic CO2e estimation based on mode, distance, weight, and assumed factors. **For conceptual illustration only.**")
        st.markdown("""
            **How it works (Highly Simplified):**
            - Estimated CO2e = Distance (km) x Cargo Weight (tons) x Assumed Emission Factor (g CO2e/ton-km).
            - **This ignores many critical factors:** Specific vessel/aircraft/vehicle efficiency, fuel type, actual route, load factors, empty running, different types of emissions (NOx, SOx), calculation methodologies (e.g., GLEC Framework), etc.
            - **Emission factors provided are EXTREMELY rough averages and vary widely.**
        """)

        distance_km_em = st.number_input("Travel Distance (km)", min_value=1.0, value=1000.0, step=10.0, key="em_dist")
        cargo_weight_ton = st.number_input("Cargo Weight (tons)", min_value=0.01, value=1.0, step=0.1, key="em_weight")
        mode_options = {
            "Sea (Average Container Ship)": 15,  # Example g CO2e/ton-km (varies hugely: 3 to 100+)
            "Air (Average Cargo Plane)": 500, # Example g CO2e/ton-km (varies hugely: 400-1200+)
            "Road (Average Truck)": 60       # Example g CO2e/ton-km (varies hugely: 20-200+)
        }
        selected_mode_em = st.selectbox("Select Transport Mode (with example factors)", options=list(mode_options.keys()), key="em_mode")
        assumed_emission_factor = st.number_input(
            "Assumed Emission Factor (g CO2e/ton-km)",
            min_value=0.1,
            value=float(mode_options[selected_mode_em]), # Set default based on selection
            step=0.1,
            help="These are VERY rough average values. Actual factors differ significantly based on many variables.",
            key="em_factor"
        )

        estimated_co2e_grams = distance_km_em * cargo_weight_ton * assumed_emission_factor
        estimated_co2e_kg = estimated_co2e_grams / 1000
        estimated_co2e_tons = estimated_co2e_kg / 1000

        st.metric(label="Estimated CO2e (Kilograms)", value=f"{estimated_co2e_kg:.2f} kg CO₂e")
        st.metric(label="Estimated CO2e (Tons)", value=f"{estimated_co2e_tons:.3f} tons CO₂e")
        st.error("**Critical Disclaimer:** This is a highly simplified and potentially inaccurate emissions estimate. Actual emissions depend on numerous complex factors. For precise calculations, use specialized tools and methodologies (e.g., GLEC Framework).")

# --- (Following code: e.g., Handle Email Sending, Footer, API Status, etc.) ---
# --- +++ NEW MODE: Marketing Email Tool +++ ---
elif st.session_state.current_mode == "📧 Marketing Email Tool":
    if not pandas_available:
        st.error("Marketing Email Tool requires the `pandas` library. Please install it (`pip install pandas openpyxl`) and restart.")
    else:
        st.info("Upload an Excel/CSV file OR manually enter contacts below. Then, compose your email or use the AI to help generate content.") # Updated info
        st.warning("""
        **⚠️ Important Considerations & Warnings:**
        *   **Permissions:** Ensure you have explicit consent (opt-in) to email contacts. Comply with anti-spam laws (e.g., CAN-SPAM, GDPR).
        *   **Rate Limits:** Sending many emails quickly via standard SMTP can get your account flagged. Use cautiously.
        *   **Deliverability:** Direct SMTP sending may have lower deliverability.
        *   **No Unsubscribe:** This tool does not automatically handle unsubscribes.
        *   **Use Responsibly:** Misuse can harm your sender reputation.
        """, icon="🚨")

        col_file, col_manual = st.columns(2)

        # --- Column 1: File Upload ---
        with col_file:
            st.subheader("Option 1: Upload File")
            uploaded_marketing_file = st.file_uploader(
                "Upload Contact List (Excel or CSV):",
                type=["xlsx", "xls", "csv"],
                key="marketing_uploader",
                accept_multiple_files=False,
                help="File should contain columns for Email Address and optionally Name/Company."
            )

            if uploaded_marketing_file:
                if st.session_state.get("marketing_uploaded_filename") != uploaded_marketing_file.name:
                    with st.spinner(f"Processing '{uploaded_marketing_file.name}'..."):
                        try:
                            file_ext = os.path.splitext(uploaded_marketing_file.name)[1].lower()
                            if file_ext in ['.xlsx', '.xls']:
                                df = pd.read_excel(uploaded_marketing_file, engine='openpyxl' if file_ext == '.xlsx' else None)
                            elif file_ext == '.csv':
                                try:
                                     df = pd.read_csv(uploaded_marketing_file, encoding='utf-8')
                                except UnicodeDecodeError:
                                     df = pd.read_csv(uploaded_marketing_file, encoding='latin-1')

                            st.session_state.marketing_dataframe = df
                            st.session_state.marketing_uploaded_filename = uploaded_marketing_file.name
                            st.session_state.marketing_file_processed = True
                            st.session_state.marketing_recipients = []
                            email_col_guess = next((col for col in df.columns if 'email' in col.lower()), None)
                            fname_col_guess = next((col for col in df.columns if 'first' in col.lower() and 'name' in col.lower()), None)
                            lname_col_guess = next((col for col in df.columns if 'last' in col.lower() and 'name' in col.lower()), None)
                            company_col_guess = next((col for col in df.columns if 'company' in col.lower() or 'organization' in col.lower()), None)
                            name_col_guess = next((col for col in df.columns if col.lower() == 'name' and col != fname_col_guess and col != lname_col_guess), None)

                            if not email_col_guess:
                                 st.error("Could not automatically detect an 'Email' column in the uploaded file. Please check the file or enter manually.")
                                 st.session_state.marketing_file_processed = False
                            else:
                                extracted_count = 0
                                for index, row in df.iterrows():
                                    email = str(row[email_col_guess]).strip()
                                    if email and "@" in email and "." in email.split('@')[-1]:
                                        first_name = str(row[fname_col_guess]).strip() if fname_col_guess and pd.notna(row[fname_col_guess]) else ""
                                        last_name = str(row[lname_col_guess]).strip() if lname_col_guess and pd.notna(row[lname_col_guess]) else ""
                                        company = str(row[company_col_guess]).strip() if company_col_guess and pd.notna(row[company_col_guess]) else ""
                                        full_name = f"{first_name} {last_name}".strip()
                                        if not full_name and name_col_guess and pd.notna(row[name_col_guess]):
                                             full_name = str(row[name_col_guess]).strip()
                                        st.session_state.marketing_recipients.append({
                                            "email": email, "first_name": first_name, "last_name": last_name,
                                            "company": company, "name": full_name if full_name else "Valued Customer"
                                        })
                                        extracted_count += 1
                                st.success(f"Loaded {extracted_count} valid contacts from '{uploaded_marketing_file.name}'.")
                                st.session_state.marketing_send_status = None
                                st.session_state.marketing_results = {"success": 0, "failed": 0, "errors": []}
                                st.session_state.marketing_send_progress = 0.0
                                st.rerun()
                        except ImportError as ie:
                            if 'openpyxl' in str(ie).lower():
                                st.error("Processing `.xlsx` requires `openpyxl`. Please install it (`pip install openpyxl`) and restart.")
                            else:
                                st.error(f"Error reading file (check library installation): {ie}")
                            st.session_state.marketing_file_processed = False
                            st.session_state.marketing_uploaded_filename = None
                        except Exception as e:
                            st.error(f"Error processing file: {e}")
                            st.session_state.marketing_file_processed = False
                            st.session_state.marketing_uploaded_filename = None

        # --- Column 2: Manual Entry Form ---
        with col_manual:
            st.subheader("Option 2: Add Manually")
            with st.form("manual_contact_form", clear_on_submit=True):
                manual_email = st.text_input("Email Address*", key="manual_email_in")
                manual_fname = st.text_input("First Name", key="manual_fname_in")
                manual_lname = st.text_input("Last Name", key="manual_lname_in")
                manual_company = st.text_input("Company Name", key="manual_company_in")
                submitted_manual = st.form_submit_button("➕ Add Contact to List")

                if submitted_manual:
                    email_to_add = manual_email.strip()
                    is_valid_email = email_to_add and "@" in email_to_add and "." in email_to_add.split('@')[-1]
                    already_exists = any(rec["email"].lower() == email_to_add.lower() for rec in st.session_state.marketing_recipients)
                    if not is_valid_email:
                        st.error("Please enter a valid Email Address.", icon="📧")
                    elif already_exists:
                         st.warning(f"Email '{email_to_add}' already exists in the list.", icon="⚠️")
                    else:
                        first_name = manual_fname.strip()
                        last_name = manual_lname.strip()
                        company = manual_company.strip()
                        full_name = f"{first_name} {last_name}".strip()
                        st.session_state.marketing_recipients.append({
                            "email": email_to_add, "first_name": first_name, "last_name": last_name,
                            "company": company, "name": full_name if full_name else "Valued Customer"
                        })
                        st.success(f"Added '{email_to_add}' to the list.")

        st.markdown("---")
        st.subheader("Current Recipient List")
        if st.session_state.marketing_recipients:
            display_df = pd.DataFrame(st.session_state.marketing_recipients)[["email", "name", "company"]]
            st.dataframe(display_df, height=200)
            st.caption(f"Total recipients: {len(st.session_state.marketing_recipients)}")
            if st.button("🗑️ Clear Entire Recipient List", key="clear_recipients_btn"):
                 st.session_state.marketing_recipients = []
                 st.session_state.marketing_uploaded_filename = None
                 st.session_state.marketing_file_processed = False
                 st.warning("Recipient list cleared.")
                 st.rerun()
        else:
            st.caption("No recipients loaded or added yet.")

        st.markdown("---")

        # +++ AI Email Content Generation Section +++
        st.subheader("🤖 AI-Powered Email Content Generation")

        # Initialize session state for AI prompt and generation status if not present
        if "ai_email_generation_prompt" not in st.session_state:
            st.session_state.ai_email_generation_prompt = ""
        if "ai_email_generation_status" not in st.session_state:
            st.session_state.ai_email_generation_status = None # Can be None, "generating", "success", "error"

        st.session_state.ai_email_generation_prompt = st.text_area(
            "Describe the email you want the AI to create:",
            value=st.session_state.ai_email_generation_prompt,
            height=120,
            key="ai_email_prompt_input",
            help="E.g., 'A welcome email for new subscribers, mention our key services.', 'A promotional email for a 20% discount on air freight this weekend, highlight urgency and benefits like speed and reliability.'"
        )

        if st.button("✨ Generate Email Content with AI", key="generate_ai_email_btn", disabled=not st.session_state.ai_email_generation_prompt.strip()):
            st.session_state.ai_email_generation_status = "generating"
            # Clear previous AI success/error messages here to avoid showing old ones during generation
            # if "ai_generation_message" in st.session_state:
            #     del st.session_state.ai_generation_message
            st.rerun()

        # Display AI generation status messages (success/error)
        ai_gen_status = st.session_state.get("ai_email_generation_status")
        if ai_gen_status == "success":
            st.success("AI has generated the email content below. You can now edit it.", icon="🎉")
            st.session_state.ai_email_generation_status = None # Reset status after showing message
        elif isinstance(ai_gen_status, str) and ai_gen_status.startswith("error:"):
            st.error(f"AI content generation failed: {ai_gen_status.replace('error: ', '')}", icon="🔥")
            st.session_state.ai_email_generation_status = None # Reset status

        # AI Generation Logic (runs after button click + rerun if status is "generating")
        if st.session_state.get("ai_email_generation_status") == "generating":
            user_ai_prompt = st.session_state.ai_email_generation_prompt
            
            gemini_prompt_for_email = f"""
            You are a helpful marketing assistant for World Movers Phils Inc.
            Based on the user's request, generate a compelling marketing email.
            The output MUST include a "Subject:" line and a "Body:" line.
            The body should be suitable for marketing and can use personalization placeholders like {{name}}, {{first_name}}, {{last_name}}, or {{company}}.

            Format the response EXACTLY like this:
            Subject: [The email subject you generate]

            Body:
            [The email body you generate. Make it professional and engaging.]

            User's request: "{user_ai_prompt}"
            """
            
            with st.spinner("🤖 AI is drafting your email... Please wait a moment."):
                try:
                    # Ensure 'model' is the correct globally initialized Gemini model instance
                    response = model.generate_content(gemini_prompt_for_email)
                    generated_text_orig = response.text
                    generated_text = generated_text_orig.strip()
                    
                    parsed_subject = ""
                    parsed_body = ""

                    lines = generated_text.split('\n')
                    subject_line_index = -1
                    body_marker_line_index = -1

                    for i, line in enumerate(lines):
                        if line.lower().startswith("subject:"):
                            parsed_subject = line[len("subject:"):].strip()
                            subject_line_index = i
                            break 
                    for i, line in enumerate(lines):
                        if line.lower().startswith("body:"):
                            body_marker_line_index = i
                            if i + 1 < len(lines):
                                parsed_body = "\n".join(lines[i+1:]).strip()
                            break
                    
                    if parsed_subject and not parsed_body:
                        if subject_line_index != -1 and subject_line_index + 1 < len(lines):
                            start_body_line = subject_line_index + 1
                            if lines[start_body_line].strip() == "" and start_body_line + 1 < len(lines):
                                start_body_line += 1
                            parsed_body = "\n".join(lines[start_body_line:]).strip()
                    elif not parsed_subject and parsed_body:
                        if body_marker_line_index > 0:
                            potential_subject_lines = lines[:body_marker_line_index]
                            for line_subj in potential_subject_lines:
                                if line_subj.strip():
                                    parsed_subject = line_subj.strip()
                                    break
                        if not parsed_subject: parsed_subject = "AI Generated (Review Subject)"
                    elif not parsed_subject and not parsed_body and generated_text_orig.strip():
                        st.warning("AI response format was unclear. Attempting basic split.", icon="⚠️")
                        all_lines_orig = generated_text_orig.strip().split('\n')
                        parsed_subject = all_lines_orig[0].strip()
                        if len(all_lines_orig) > 1: parsed_body = "\n".join(all_lines_orig[1:]).strip()
                        else: parsed_body = parsed_subject
                    if not parsed_subject and generated_text_orig.strip():
                        parsed_subject = "AI Generated (Review Subject)"

                    st.session_state.marketing_subject = parsed_subject
                    st.session_state.marketing_body = parsed_body
                    st.session_state.ai_email_generation_status = "success"
                    st.rerun()

                except Exception as e:
                    st.session_state.ai_email_generation_status = f"error: {str(e)}"
                    st.rerun()
        # +++ End of AI Email Content Generation Section +++

        st.markdown("---")
        st.subheader("Compose or Edit Your Email Campaign") # Renamed for clarity

        # Email Subject and Body fields will be populated by AI or user input
        email_conf_col1, email_conf_col2 = st.columns([1,2]) 
        with email_conf_col1:
             st.session_state.marketing_subject = st.text_input(
                "Email Subject:",
                value=st.session_state.get("marketing_subject", ""), 
                key="marketing_subject_input" # Original key
            )

        st.session_state.marketing_body = st.text_area(
            "Email Body (Use {name}, {first_name}, {last_name}, or {company} for personalization):",
            height=300, # Increased height for better editing
            value=st.session_state.get("marketing_body", ""), 
            key="marketing_body_input" # Original key
        )

        st.markdown("---")
        send_disabled = not all([
            st.session_state.marketing_recipients,
            st.session_state.marketing_subject.strip(), # Ensure subject is not just whitespace
            st.session_state.marketing_body.strip()    # Ensure body is not just whitespace
        ])

        if st.button("🚀 Send Marketing Emails", disabled=send_disabled, type="primary", key="send_marketing_email_btn"):
            st.session_state.marketing_send_status = "⏳ Preparing to send..." # Original status for sending
            st.session_state.marketing_results = {"success": 0, "failed": 0, "errors": []}
            st.session_state.marketing_send_progress = 0.0
            st.rerun()

        current_send_status = st.session_state.get("marketing_send_status")
        if isinstance(current_send_status, str) and current_send_status.startswith("⏳"): # Original sending logic
            recipients_to_send = st.session_state.marketing_recipients
            total_recipients = len(recipients_to_send)
            subject_to_send = st.session_state.marketing_subject # Use state var
            body_template_to_send = st.session_state.marketing_body # Use state var
            results = st.session_state.marketing_results

            st.markdown("---")
            st.subheader("Sending Progress...")
            progress_bar = st.progress(st.session_state.marketing_send_progress)
            status_text_area = st.empty() 

            def send_single_marketing_email(recipient_dict, subject_email, body_template_email): # Renamed params
                sender = SENDER_EMAIL
                password = SENDER_PASSWORD
                port_to_use = SMTP_PORT
                recipient_email_addr = recipient_dict['email']
                try:
                    body_final = body_template_email.format_map(recipient_dict)
                except Exception:
                     body_final = body_template_email.replace("{name}", recipient_dict.get("name", "Valued Customer")) # Basic fallback
                message = MIMEText(body_final, 'plain', 'utf-8')
                message['Subject'] = subject_email
                message['From'] = f"World Movers AI-Agent <{sender}>"
                message['To'] = recipient_email_addr
                try:
                    context = ssl.create_default_context()
                    server = None
                    if port_to_use == 465:
                        server = smtplib.SMTP_SSL(SMTP_SERVER, port_to_use, context=context, timeout=20)
                        server.login(sender, password)
                    elif port_to_use == 587:
                        server = smtplib.SMTP(SMTP_SERVER, port_to_use, timeout=20)
                        server.starttls(context=context)
                        server.login(sender, password)
                    else: return False, f"Unsupported SMTP port {port_to_use}"
                    server.sendmail(sender, [recipient_email_addr], message.as_string())
                    server.quit()
                    return True, "Success"
                except smtplib.SMTPRecipientsRefused as e_smtp_rec: return False, f"Recipient refused: {e_smtp_rec.recipients}"
                except smtplib.SMTPAuthenticationError: return False, "SMTP Auth Error"
                except smtplib.SMTPServerDisconnected: return False, "SMTP Server Disconnected"
                except smtplib.SMTPException as smtp_err_gen: return False, f"SMTP Error: {smtp_err_gen}"
                except ssl.SSLError as ssl_err_send: return False, f"SSL Error: {ssl_err_send}"
                except OSError as os_err_send: return False, f"Network/OS Error: {os_err_send}"
                except Exception as e_send: return False, f"Unexpected Error: {type(e_send).__name__}"
                finally:
                    if 'server' in locals() and server and hasattr(server, 'sock') and server.sock:
                        try: server.quit()
                        except: pass
            
            send_delay_seconds = 2 
            start_index = int(st.session_state.marketing_send_progress * total_recipients)
            for i in range(start_index, total_recipients):
                recipient_data = recipients_to_send[i]
                email_address_current = recipient_data['email']
                status_text_area.info(f"Sending {i+1}/{total_recipients} to {email_address_current}...")
                success_flag, msg_status = send_single_marketing_email(recipient_data, subject_to_send, body_template_to_send)
                if success_flag:
                    results["success"] += 1
                    status_text_area.info(f"✅ Sent {i+1}/{total_recipients} to {email_address_current}")
                else:
                    results["failed"] += 1
                    results["errors"].append({"email": email_address_current, "error": msg_status})
                    status_text_area.warning(f"⚠️ Failed {i+1}/{total_recipients} for {email_address_current}: {msg_status}")
                st.session_state.marketing_send_progress = (i + 1) / total_recipients
                progress_bar.progress(st.session_state.marketing_send_progress)
                time.sleep(send_delay_seconds) 
            st.session_state.marketing_send_status = "✅ Sending Complete!"
            st.session_state.marketing_results = results
            st.rerun()

        final_send_status_check = st.session_state.get("marketing_send_status")
        if isinstance(final_send_status_check, str) and final_send_status_check == "✅ Sending Complete!": # Original result display
             st.markdown("---")
             st.subheader("Sending Results")
             results_final = st.session_state.marketing_results
             st.success(f"Emails Sent Successfully: {results_final['success']}")
             st.warning(f"Emails Failed: {results_final['failed']}")
             if results_final["errors"]:
                 with st.expander("Show Failed Emails and Errors"):
                     st.dataframe(pd.DataFrame(results_final["errors"]))

# --- +++ End of NEW Marketing Email Tool Mode +++ ---

# --- Handle Email Sending After Rerun (Existing Logic for Quote Requests) ---
# ... (keep existing email flag check for quote requests) ...

# --- Footer ---
# ... (keep existing footer) ...

# --- API Status / Trace (Optional Debug Info) ---
# ... (keep existing debug info) ...

# --- Handle Email Sending After Rerun (Common Logic Outside Mode Blocks) ---
# Check the flag *after* all mode logic has potentially set it during its run
if st.session_state.get("send_email_flag", False):
    print("Email flag is set after main logic, attempting to send...") # Debug
    # Hardcoded recipients as per system prompt instructions - consider making configurable if needed
    recipients = ["wilma_sg@yahoo.com", "wilma@worldmovers.com.ph", "info.wmlogistics@gmail.com"]
    email_content_to_send = st.session_state.get("email_content", "[Error: Email content was missing in session state]")

    # Call the email function (it now sets the success/error message in session state)
    with st.spinner("Forwarding request to World Movers team..."):
        email_sent_successfully = send_quote_request_email(email_content_to_send, recipients)

    # Clear the flag and content *immediately* after attempting send (success or fail)
    # to prevent accidental resending on subsequent unrelated reruns.
    st.session_state.send_email_flag = False
    # Use pop to remove the key safely, defaulting to None if already gone
    st.session_state.pop("email_content", None)

    # Rerun *one more time* to display the success/error message set by the send_quote_request_email function
    # This message was stored in st.session_state.email_status_message
    st.rerun()


# --- Footer ---
st.markdown("---")
st.markdown(f"""
<div style="font-size: 0.9em; color: #BDC3C7; text-align: center;">
    AI-Agent Assistant for World Movers Phils Inc. | Powered by Gemini AGI<br>
    For official quotes and tracking, please contact directly via
    <a href="https://worldmovers.net/" target="_blank">worldmovers.net</a> /
    <a href="https://worldmovers.com.ph/" target="_blank">worldmovers.com.ph</a>
</div>
""", unsafe_allow_html=True)

# --- API Status / Trace (Optional Debug Info) ---
st.markdown("---")
status_col, trace_col = st.columns([3, 1])
with status_col:
    # Display the last recorded API call status (set by various modes)
    last_api_status = st.session_state.get("api_call_status")
    if last_api_status:
        if "✅" in last_api_status: st.success(last_api_status, icon="✅")
        elif "❌" in last_api_status: st.error(last_api_status, icon="❌")
        elif "⚠️" in last_api_status: st.warning(last_api_status, icon="⚠️")
        elif "⏳" in last_api_status: st.info(last_api_status, icon="⏳") # Show pending status if relevant
        else: st.caption(last_api_status) # Generic caption for other statuses
with trace_col:
     # Display trace data if it was captured (currently placeholder)
     # This would typically hold API response metadata if implemented
     last_trace_data = st.session_state.get("trace_data")
     if last_trace_data and last_trace_data != "{}":
          with st.expander("Last Query Trace (Debug)"):
               try:
                    # Attempt to pretty print if it's valid JSON
                    st.json(json.loads(last_trace_data))
               except (json.JSONDecodeError, TypeError):
                    # Show as plain text if not valid JSON or not string
                    st.code(str(last_trace_data), language=None)
     # else:
     #      st.caption("No trace data.") # Optional: Indicate lack of trace data 
