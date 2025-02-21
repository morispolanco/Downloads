import streamlit as st
import requests
import os
import json

# Configurar la API key desde las variables de entorno
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Función para obtener respuesta del modelo usando la API REST
def get_response(prompt):
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
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
        
        response = requests.post(
            f"{API_URL}?key={API_KEY}",
            headers=headers,
            json=payload
        )
        
        # Verificar si la solicitud fue exitosa
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error procesando la respuesta: {str(e)}"

# Configuración de la interfaz de Streamlit
st.title("Chat General con Gemini 2.0 Flash")
st.write("Pregunta lo que quieras y obtén respuestas generadas por IA")

# Inicializar el historial del chat en la sesión
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada del usuario
if prompt := st.chat_input("Escribe tu mensaje aqui..."):
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    # Agregar mensaje al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Obtener y mostrar respuesta del asistente
    with st.chat_message("assistant"):
        response = get_response(prompt)
        st.markdown(response)
    # Agregar respuesta al historial
    st.session_state.messages.append({"role": "assistant", "content": response})
