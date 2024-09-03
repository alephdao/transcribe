import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import time
from pydub import AudioSegment
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")

def get_audio_duration(file_path):
    """Get the duration of an audio file in seconds."""
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000  # Convert milliseconds to seconds

def transcribe_audio(audio_file, progress_bar):
    """
    Transcribe the entire audio file using Azure Speech-to-Text.
    Converts MP3 to WAV if necessary.
    
    Args:
    audio_file (str): Path to the audio file to transcribe.
    progress_bar (streamlit.ProgressBar): Streamlit progress bar object.
    
    Returns:
    str: The transcribed text or an error message.
    """
    temp_wav_file = None
    try:
        # Convert MP3 to WAV if necessary
        if audio_file.lower().endswith('.mp3'):
            temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
            sound = AudioSegment.from_mp3(audio_file)
            sound.export(temp_wav_file, format="wav")
            wav_file_to_transcribe = temp_wav_file
        else:
            wav_file_to_transcribe = audio_file

        # Get audio duration
        audio_duration = get_audio_duration(wav_file_to_transcribe)

        # Set up the speech config
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        audio_config = speechsdk.audio.AudioConfig(filename=wav_file_to_transcribe)

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
            elapsed_time = time.time() - start_time
            progress = min(elapsed_time / audio_duration, 1.0)
            progress_bar.progress(progress)

        speech_recognizer.stop_continuous_recognition()

        transcription = ' '.join(all_results)
        
    except Exception as e:
        transcription = f"An error occurred: {str(e)}"
    finally:
        # Clean up the temporary WAV file if it was created
        if temp_wav_file and os.path.exists(temp_wav_file):
            os.remove(temp_wav_file)

    return transcription

def main():
    st.title("Audio Transcription App")

    # Check if Azure credentials are properly configured
    if not speech_key or not service_region:
        st.error("Azure Speech to Text credentials are not properly configured. Please check your .env file.")
        return

    # File uploader
    uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3"])

    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # Transcribe button
        if st.button("Transcribe"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("Transcribing..."):
                transcription = transcribe_audio(tmp_file_path, progress_bar)
            
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
        os.unlink(tmp_file_path)

if __name__ == "__main__":
    main()
