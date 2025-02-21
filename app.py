import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Gemini API configuration
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def generate_response(prompt):
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 1,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "text/plain"
        }
    }
    
    try:
        response = requests.post(f"{API_URL}?key={API_KEY}", headers=headers, json=data)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error: {str(e)}"

# Main UI
st.title("🤖 Gemini Chatbot")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        response = generate_response(prompt)
        st.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Add a sidebar with information
with st.sidebar:
    st.title("About")
    st.info("""
    This chatbot uses Google's Gemini API to generate responses.
    Please ensure you have set your GEMINI_API_KEY in the .env file.
    """)