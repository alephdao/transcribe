import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import time
from pydub import AudioSegment
import tempfile

try:
    import moviepy.editor as mp
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

def get_audio_duration(file_path):
    """Get the duration of an audio file in seconds."""
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000  # Convert milliseconds to seconds

def extract_audio_from_video(video_path):
    """Extract audio from video file and save as temporary WAV file."""
    if not MOVIEPY_AVAILABLE:
        raise ImportError("moviepy is not installed. Cannot extract audio from video.")
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(temp_audio_file)
    return temp_audio_file

def convert_to_wav(audio_file):
    """Convert audio file to WAV format."""
    temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
    sound = AudioSegment.from_file(audio_file)
    sound.export(temp_wav_file, format="wav")
    return temp_wav_file

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
    temp_wav_file = None
    try:
        # Handle different file types
        if audio_file.lower().endswith(('.mp3', '.m4a')):
            temp_wav_file = convert_to_wav(audio_file)
            wav_file_to_transcribe = temp_wav_file
        elif audio_file.lower().endswith('.mp4'):
            if not MOVIEPY_AVAILABLE:
                return "Error: moviepy is not installed. Cannot process video files."
            temp_wav_file = extract_audio_from_video(audio_file)
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
    st.title("Audio/Video Transcription App")

    # Add input fields for API keys
    speech_key = st.text_input("Enter your Azure Speech API Key", type="password")
    service_region = st.text_input("Enter your Azure Speech Service Region")

    # Check if API keys are provided
    if not speech_key or not service_region:
        st.warning("Please enter your Azure Speech-to-Text credentials to use the app. Your credentials are not stored, and they will be cleared when you close or refresh your browser session.")
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
