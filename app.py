import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import time
from dotenv import load_dotenv
import io
from pydub import AudioSegment

# Load environment variables from .env file
load_dotenv()

speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")

def convert_mp3_to_wav(mp3_data):
    """Convert MP3 data to WAV format."""
    audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")
    return wav_io.getvalue()

def is_valid_audio_file(file):
    """Check if the file is a valid audio file."""
    try:
        # Read the first 12 bytes of the file
        header = file.getvalue()[:12]
        # Check for WAV header
        if header.startswith(b'RIFF') and header[8:12] == b'WAVE':
            return True, "wav"
        # Check for MP3 header
        if header.startswith(b'\xFF\xFB') or header.startswith(b'ID3'):
            return True, "mp3"
        return False, None
    except Exception as e:
        st.error(f"Error validating file: {str(e)}")
        return False, None

def transcribe_audio(audio_data, progress_bar):
    """
    Transcribe the audio file using Azure Speech-to-Text.
    """
    try:
        # Set up the speech config
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_recognition_language="en-US"
        
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
        is_valid, file_type = is_valid_audio_file(uploaded_file)
        if not is_valid:
            st.error("The uploaded file does not appear to be a valid audio file.")
            return

        if st.button("Transcribe"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("Transcribing..."):
                audio_data = uploaded_file.getvalue()
                if file_type == "mp3":
                    st.info("Converting MP3 to WAV for better transcription quality...")
                    audio_data = convert_mp3_to_wav(audio_data)
                transcription = transcribe_audio(audio_data, progress_bar)
            
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

if __name__ == "__main__":
    main()
