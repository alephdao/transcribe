import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import time
from pydub import AudioSegment
import tempfile

# Remove the dotenv import and load_dotenv() call

# Remove these lines:
# speech_key = os.getenv("AZURE_SPEECH_KEY")
# service_region = os.getenv("AZURE_SPEECH_REGION")

try:
    import moviepy.editor as mp
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

# ... [keep all other functions as they are] ...

def transcribe_audio(audio_file, progress_bar, speech_key, service_region):
    """
    Transcribe the entire audio file using Azure Speech-to-Text.
    Converts MP3 and M4A to WAV if necessary, and extracts audio from MP4.
    
    Args:
    audio_file (str): Path to the audio/video file to transcribe.
    progress_bar (streamlit.ProgressBar): Streamlit progress bar object.
    speech_key (str): Azure Speech API key.
    service_region (str): Azure Speech service region.
    
    Returns:
    str: The transcribed text or an error message.
    """
    # ... [keep the rest of the function as it is, just use the passed speech_key and service_region] ...

def main():
    st.title("Audio/Video Transcription App")

    # Add input fields for API keys
    speech_key = st.text_input("Enter your Azure Speech API Key", type="password")
    service_region = st.text_input("Enter your Azure Speech Service Region")

    # Check if API keys are provided
    if not speech_key or not service_region:
        st.warning("Please enter your Azure Speech to Text credentials to use the app.")
        return

    # File uploader
    allowed_types = ["wav", "mp3", "m4a"]
    if MOVIEPY_AVAILABLE:
        allowed_types.append("mp4")
    
    uploaded_file = st.file_uploader("Choose an audio or video file", type=allowed_types)

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
                transcription = transcribe_audio(tmp_file_path, progress_bar, speech_key, service_region)
            
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
