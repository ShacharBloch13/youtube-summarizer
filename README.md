# youtube-summarizer

``` https://youtu.be/g2plcf1lbgs ```

The YouTube Summarizer is a Python script designed to automate the process of downloading YouTube videos, extracting audio, transcribing the audio content, and performing scene detection. This document outlines the setup, usage, and flow of the script.

# Disclaimer
This script includes API keys hardcoded directly within the source code for the Google YouTube Data API and the Google Cloud Speech-to-Text API. While this practice is not recommended due to security concerns, it is done here for simplicity and ease of use for anyone running the script in a controlled, non-production environment.

# Installation
Before running the script, ensure that you have Python installed on your system and then install the necessary libraries using pip:
```pip install google-api-python-client pytube3 isodate opencv-python-headless pillow easyocr requests```

# How It Works
The script operates in the following sequence:

1. Video Search and Download: Searches for a video on YouTube based on a user-provided subject and downloads the video if it meets specified criteria (e.g., duration).

2. Audio Extraction: Extracts the audio from the downloaded video and saves it as an MP3 file.

3. Audio Transcription: Transcribes the extracted audio content using the Google Cloud Speech-to-Text API and saves the transcript.

4. Scene Detection: Analyzes the video to detect scene changes and captures screenshots of these scenes, applying a watermark.

5. Text Extraction from Images: Uses OCR to extract text from the captured scene images.

6. Each step is performed by a dedicated function within the script, with main() orchestrating the overall flow.

# Technologies Used
1. Python: The core programming language for the script.
   
2. Google YouTube Data API: For searching and identifying YouTube videos.
   
3. PyTube: For downloading YouTube videos.
   
4. Google Cloud Speech-to-Text API: For transcribing audio content.
   
5. OpenCV: For video processing and scene detection.
 
6. Pillow: For image manipulation, including adding watermarks.
   
7. EasyOCR: For extracting text from images.
   
8. Requests: For making HTTP requests (used for direct interaction with the Speech-to-Text API).
   
9. Running the Script

To run the script, navigate to the directory containing the script and execute:
```python youtubesummarizer.py```

Follow the prompts to input your search query. The script will handle the rest, saving the video, audio, transcription, and scene captures in the current working directory.

# Final Note
The script is designed for educational and demonstration purposes. Users are encouraged to adopt best practices for API key management and consider security implications when adapting this script for other uses.
