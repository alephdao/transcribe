import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")

def transcribe_audio(audio_file, progress_bar):
    """
    Transcribe the audio file using Azure Speech-to-Text.
    
    Args:
    audio_file (str): Path to the audio file to transcribe.
    progress_bar (streamlit.ProgressBar): Streamlit progress bar object.
    
    Returns:
    str: The transcribed text or an error message.
    """
    try:
        # Set up the speech config
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file)

        # Create a speech recognizer and start recognition
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Set up the complete callback
        done = False
        all_results = []

        def stop_cb(evt):
            """Callback to stop continuous recognition upon receiving an event `evt`"""
            nonlocal done
            done = True

        # Connect callbacks to the events fired by the speech recognizer
        speech_recognizer.recognized.connect(lambda evt: all_results.append(evt.result.text))
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start continuous speech recognition
        speech_recognizer.start_continuous_recognition()

        start_time = time.time()
        while not done:
            time.sleep(0.5)
            progress_bar.progress(min((time.time() - start_time) / 300, 1.0))  # Assume max 5 minutes

        speech_recognizer.stop_continuous_recognition()

        transcription = ' '.join(all_results)
        
    except Exception as e:
        transcription = f"An error occurred: {str(e)}"

    return transcription

def main():
    st.title("Audio Transcription App")

    # Check if Azure credentials are properly configured
    if not speech_key or not service_region:
        st.error("Azure Speech to Text credentials are not properly configured. Please check your .env file.")
        return

    # File uploader
    uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3", "ogg", "flac"])

    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Transcribe button
        if st.button("Transcribe"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("Transcribing..."):
                transcription = transcribe_audio(uploaded_file.name, progress_bar)
            
            progress_bar.progress(1.0)
            status_text.text("Transcription completed!")
            st.success("Transcription completed!")
            st.text_area("Transcription", transcription, height=300)

            # Download button
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
