import streamlit as st
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")

def get_token():
    headers = {
        'Ocp-Apim-Subscription-Key': speech_key
    }
    response = requests.post(f'https://{service_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken', headers=headers)
    return response.text

def transcribe_audio(audio_data, progress_bar):
    """
    Transcribe the audio file using Azure Speech-to-Text REST API.
    """
    try:
        # Get the access token
        access_token = get_token()

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'audio/mp3'  # Adjust if needed for WAV files
        }

        params = {
            'language': 'en-US',
            'format': 'detailed'
        }

        # Make the API request
        response = requests.post(
            f'https://{service_region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1',
            params=params,
            headers=headers,
            data=audio_data
        )

        if response.status_code == 200:
            result = response.json()
            transcription = result['DisplayText'] if 'DisplayText' in result else "No transcription available."
        else:
            transcription = f"Error: {response.status_code} - {response.text}"

        progress_bar.progress(1.0)
        
    except Exception as e:
        transcription = f"An error occurred: {str(e)}"

    return transcription

def main():
    st.title("Audio Transcription App")

    if not speech_key or not service_region:
        st.error("Azure Speech to Text credentials are not properly configured. Please check your .env file.")
        return

    uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3"])

    if uploaded_file is not None:
        if st.button("Transcribe"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("Transcribing..."):
                audio_data = uploaded_file.getvalue()
                transcription = transcribe_audio(audio_data, progress_bar)
            
            status_text.text("Transcription completed!")
            st.success("Transcription completed!")
            st.text_area("Transcription", transcription, height=300)

            st.download_button(
                label="Download Transcription",
                data=transcription,
                file_name="transcription.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    main()
