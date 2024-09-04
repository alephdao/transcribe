import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import time
from dotenv import load_dotenv
import io

# Load environment variables from .env file
load_dotenv()

speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")

def is_valid_audio_file(file):
    """Check if the file is a valid audio file."""
    try:
        with open(file.name, "rb") as f:
            header = f.read(12)
        # Check for WAV header
        if header.startswith(b'RIFF') and header[8:12] == b'WAVE':
            return True
        # Check for MP3 header
        if header.startswith(b'\xFF\xFB') or header.startswith(b'ID3'):
            return True
        # Add more checks for other formats if needed
        return False
    except Exception as e:
        st.error(f"Error validating file: {str(e)}")
        return False

def transcribe_audio(audio_file, progress_bar):
    """
    Transcribe the audio file using Azure Speech-to-Text.
    """
    try:
        # Read the entire file into memory
        with open(audio_file, "rb") as f:
            audio_data = f.read()

        # Set up the speech config
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        
        # Use PushAudioInputStream
        push_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        # Create a speech recognizer and start recognition
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Set up the complete callback
        done = False
        all_results = []

        def stop_cb(evt):
            nonlocal done
            done = True

        def recognized_cb(evt):
            all_results.append(evt.result.text)
            progress_bar.progress(min(len(all_results) / 20, 1.0))  # Assume max 20 utterances

        # Connect callbacks
        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start continuous speech recognition
        speech_recognizer.start_continuous_recognition()

        # Push audio data to the stream
        push_stream.write(audio_data)
        push_stream.close()

        while not done:
            time.sleep(0.5)

        speech_recognizer.stop_continuous_recognition()

        transcription = ' '.join(all_results)
        
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
        if not is_valid_audio_file(uploaded_file):
            st.error("The uploaded file does not appear to be a valid audio file.")
            return

        # Save the uploaded file temporarily
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if st.button("Transcribe"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("Transcribing..."):
                transcription = transcribe_audio(uploaded_file.name, progress_bar)
            
            progress_bar.progress(1.0)
            status_text.text("Transcription completed!")
            st.success("Transcription completed!")
            st.text_area("Transcription", transcription, height=300)

            st.download_button(
                label="Download Transcription",
                data=transcription,
                file_name="transcription.txt",
                mime="text/plain"
            )

        # Clean up the temporary file
        os.remove(uploaded_file.name)

if __name__ == "__main__":
    main()
