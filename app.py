import streamlit as st
import requests
import os
import json
import speech_recognition as sr
from io import BytesIO
from google.cloud import speech
import duckduckgo_search

# Configurar las claves API desde variables de entorno
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CLOUD_CREDENTIALS = os.getenv("GOOGLE_CLOUD_CREDENTIALS")  # JSON credentials como string
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Configurar cliente de Google Speech-to-Text con credenciales desde variable de entorno
if GOOGLE_CLOUD_CREDENTIALS:
    with open("gcloud-credentials.json", "w") as f:
        f.write(GOOGLE_CLOUD_CREDENTIALS)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcloud-credentials.json"
speech_client = speech.SpeechClient()

# Función para obtener respuesta del modelo Gemini
def get_gemini_response(prompt):
    try:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 1,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,
                "responseMimeType": "text/plain"
            }
        }
        response = requests.post(f"{API_URL}?key={GEMINI_API_KEY}", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error procesando la respuesta: {str(e)}"

# Función para búsqueda web
def web_search(query):
    try:
        results = duckduckgo_search.DDGS().text(query, max_results=3)
        summary = "\n".join([f"- {r['title']}: {r['body'][:100]}..." for r in results])
        return f"Resultados de búsqueda web:\n{summary}"
    except Exception as e:
        return f"Error en la búsqueda web: {str(e)}"

# Función para reconocimiento de voz local
def recognize_speech_local():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        st.write("Ajustando al ruido ambiental...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        st.write("Escuchando... Habla ahora.")
        try:
            audio = recognizer.listen(source, timeout=5)
            st.write("Procesando audio...")
            text = recognizer.recognize_google(audio, language="es-ES")
            return text
        except sr.WaitTimeoutError:
            return "No se detectó voz en 5 segundos"
        except sr.UnknownValueError:
            return "No se pudo entender el audio"
        except sr.RequestError as e:
            return f"Error en el servicio: {str(e)}"

# Función para procesar archivo de audio subido
def recognize_speech_uploaded(audio_file):
    try:
        audio_content = audio_file.read()
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="es-ES"
        )
        response = speech_client.recognize(config=config, audio=audio)
        if response.results:
            return response.results[0].alternatives[0].transcript
        return "No se detectó voz en el archivo"
    except Exception as e:
        return f"Error procesando el archivo: {str(e)}"

# Configuración de la interfaz de Streamlit
st.title("Chat General con Gemini 2.0 Flash")
st.write("Pregunta por texto, voz local, archivo de audio o búsqueda web")

# Inicializar el historial del chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Opciones de entrada
col1, col2, col3 = st.columns(3)
with col1:
    use_mic = st.button("Hablar (Micrófono local)")
with col2:
    use_web = st.button("Búsqueda Web")
with col3:
    uploaded_file = st.file_uploader("Subir audio", type=["wav", "mp3"], label_visibility="collapsed")

# Entrada de texto
prompt = st.chat_input("Escribe tu mensaje aquí o usa las opciones arriba...")

# Procesar entrada
if prompt or use_mic or uploaded_file or use_web:
    input_text = None
    
    # Micrófono local
    if use_mic:
        input_text = recognize_speech_local()
    
    # Archivo subido
    elif uploaded_file:
        input_text = recognize_speech_uploaded(uploaded_file)
    
    # Texto escrito
    elif prompt:
        input_text = prompt
    
    if input_text:
        # Mostrar entrada del usuario
        with st.chat_message("user"):
            st.markdown(input_text)
        st.session_state.messages.append({"role": "user", "content": input_text})
        
        # Procesar respuesta
        with st.chat_message("assistant"):
            if use_web:
                response = web_search(input_text)
            else:
                response = get_gemini_response(input_text)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
    elif use_mic or uploaded_file:
        st.warning(input_text)
