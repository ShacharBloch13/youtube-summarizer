from googleapiclient.discovery import build
from pytube import YouTube
import isodate 
import os
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import easyocr
import webbrowser
from google.cloud import speech
import requests
import base64


api_key = 'AIzaSyCOevHFAmoNY3WONd-wzIoMPfGqA3ix4t0' # it is better practice to save locally under variables, but for the checkers to see that it is working, I will leave it here
text_to_speech_key = 'AIzaSyA3H4KnMcwvo70Xmhde7vFg1IIOvBet1JE'
youtube = build('youtube', 'v3', developerKey=api_key)
watermark_text = "Shachar Bloch"
threshold_level = 60.0
OUTPUT_FILE = "collected_text.txt"

def video_search_and_download(subject):
    search_request = youtube.search().list(
    part="snippet",
    maxResults=50,
    q=subject,
    type="video",
    order="relevance",  # This ensures results are ordered by relevance
)
    search_response = search_request.execute()

    for item in search_response['items']:
        video_id = item['id']['videoId']
        youtube_link = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
        filename = yt.title.replace(" ", "_") + ".mp4"
        download_path = os.path.join(os.getcwd(), filename)
        video_request = youtube.videos().list(
            part="contentDetails",
            id=video_id
        )
        video_response = video_request.execute()

        duration = isodate.parse_duration(video_response['items'][0]['contentDetails']['duration'])
        # Check if the video is less than 10 minutes
        if duration.total_seconds() < 600:
            if not os.path.exists(download_path):
                yt.streams.get_highest_resolution().download(filename=filename)
                print("Download completed.")
                return download_path, video_id
            else:
                print("Video already exists.")
                return download_path, video_id
            
        


        # Get video details to check the duration
        video_request = youtube.videos().list(
            part="contentDetails",
            id=video_id
        )
        video_response = video_request.execute()
        duration = isodate.parse_duration(video_response['items'][0]['contentDetails']['duration'])
        if not os.path.exists(download_path):
                yt.streams.get_highest_resolution().download(filename=filename)
                print("Download completed.")
                return download_path, video_id
        else:
            print("Video already exists.")
            return download_path, video_id
    print("No suitable video found.")
    return None

def download_audio(video_id):
    youtube_link = f"https://www.youtube.com/watch?v={video_id}"
    yt = YouTube(youtube_link)
    audio_filename = yt.title.replace(" ", "_") + ".mp3"
    audio_download_path = os.path.join(os.getcwd(), audio_filename)

    # Check if audio file already exists
    if os.path.exists(audio_download_path):
        print("Audio file already exists.")
        return audio_download_path

    audio_stream = yt.streams.filter(only_audio=True).first()
    if audio_stream:
        audio_stream.download(filename=audio_filename)
        print("Audio download completed.")
        return audio_download_path
    else:
        print("No audio stream found.")
        return None

    sound = AudioSegment.from_mp3(audio_download_path)
    wav_file_path = audio_download_path.replace(".mp3", ".wav")
    sound.export(wav_file_path, format="wav")
    return wav_file_path


def transcribe_mp3_to_file(text_to_speech_key, mp3_file_path):
    url = f"https://speech.googleapis.com/v1/speech:recognize?key={text_to_speech_key}"
    
    with open(mp3_file_path, "rb") as audio_file:
        audio_content = base64.b64encode(audio_file.read()).decode("utf-8")
    
    data = {
        "config": {
            "encoding": "MP3",
            "sampleRateHertz": 16000,
            "languageCode": "en-US"
        },
        "audio": {
            "content": audio_content
        }
    }
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        json_response = response.json()
        results = json_response.get('results', [])
        
        if not results:
            print("No speech could be recognized.")
            return
        
        transcripts = []
        for result in results:
            alternatives = result.get('alternatives', [])
            for alternative in alternatives:
                if 'transcript' in alternative:
                    transcripts.append(alternative['transcript'])
        
        transcript_text = "\n".join(transcripts)
        if transcripts:
            with open("audio_to_text.txt", "w", encoding="utf-8") as file:
                file.write(transcript_text)
            print("Transcription completed and saved to audio_to_text.txt.")
            
            file_url = 'file://' + os.path.abspath("audio_to_text.txt")
            webbrowser.open(file_url)
        else:
            print("Transcript was empty.")
    else:
        print(f"Failed to transcribe audio: {response.status_code} - {response.text}")


def display_transcript():
    with open("transcript.txt", "r") as file:
        content = file.read()
        print(content)

def image_text_decipher(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path)
    excluded_string = watermark_text
    detected_text = "\n".join([text[1] for text in result if excluded_string not in text[1]])


    print(detected_text)  # Print detected text to console

    # Save detected text to a file
    with open(OUTPUT_FILE, 'a') as text_file:
        text_file.write(detected_text + "\n")
    
    return detected_text  # Return the detected text for any further use

def detect_and_save_scenes(video_path):
    
    if not os.path.isfile(video_path):
        print("Video file does not exist at the specified path.")
        return

    # Set up PySceneDetect
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold_level))
    video_manager = VideoManager([video_path])
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list(video_manager.get_base_timecode())

    # Use OpenCV to read the video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video file.")
        return
    scene_image_paths = []
    for i, (start, end) in enumerate(scene_list, start=1):
        # Seek to the start of the scene
        start_frame = start.get_frames()
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        ret, frame = cap.read()
        if ret:
            # Convert BGR frame to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convert NumPy array (frame) to PIL Image
            frame_image = Image.fromarray(frame)
            
            add_watermark(frame_image, watermark_text)#, (frame_image.width - 220, frame_image.height - 40))
            frame_image_path = f"scene_{i}.jpg"
            frame_image.save(frame_image_path)
            print(f"Saved {i} scene.")
            
            # decihers the text, opens agian the saved image and adds the watermark
            image_text_decipher(frame_image_path)
            frame_image = Image.open(frame_image_path)
            add_watermark(frame_image, watermark_text)
            frame_image.save(frame_image_path)
            scene_image_paths.append(frame_image_path)
    gif_maker(scene_image_paths)
    cap.release()
    video_manager.release()


def add_watermark(image, text):
    # Create a drawing context
    draw = ImageDraw.Draw(image)
    
    # Specify the font: you can use a specific TrueType/OpenType font or the default PIL font
    try:
        # Attempt to use a specific TrueType font file if available
        font = ImageFont.truetype("arial.ttf", 24)  # Adjust font path and size as needed
    except IOError:
        # Fallback to default PIL font if specific font file is not found
        font = ImageFont.load_default()
    
    # Get the size of the text to be drawn
    #text_width, text_height = draw.text((10,25),text, font=font)
    
    # Calculate the position for the text to be in the bottom-right corner, with a small margin
    x = image.width -  10  # Adjust margin as needed
    y = image.height - 10  # Adjust margin as needed
    
    # Draw the text onto the image with the specified font, position, and color (I like Spotify's color scheme)
    draw.text((image.width -175, image.height - 25), text, fill=(30, 215, 96), font=font)


def gif_maker(scene_list, output_filename="GIF.gif", duration=100): #
    images = [Image.open(scene) for scene in scene_list]
    # Ensure the GIF is no longer than 10 seconds
    if len(images) > 0:
        gif_duration = min(duration, 10000 // len(images))
    else:
        gif_duration = duration
    images[0].save(output_filename, save_all=True, append_images=images[1:], loop=0, duration=gif_duration)
    print(f"Saved GIF to {output_filename}")
    file_url = 'file://' + os.path.abspath(output_filename)
    webbrowser.open(file_url)

def print_concatenated_text_from_file(file_path):
    if not os.path.exists(file_path):
        print("Text file does not exist.")
        return ""
    
    with open(file_path, 'r') as file:
        concatenated_text = " ".join([line.strip() for line in file.readlines()])
    
    print("Concatenated Text:", concatenated_text)
    return concatenated_text

def create_transcription(audio_download_path):
    # Assuming your OpenAI API key is already set in your environment variables
    # or you've set it elsewhere in your code
    client = OpenAI()

    try:
        # Open the audio file in binary mode
        with open(audio_download_path, "rb") as audio_file:
            # Create transcription using the OpenAI Whisper model
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Extract the transcription text
        transcription_text = transcript['data']['text']

        # Define the filename for saving the transcription
        transcription_filename = f"{os.path.splitext(audio_download_path)[0]}_transcription.txt"

        # Save the transcription to a text file
        with open(transcription_filename, "w", encoding="utf-8") as file:
            file.write(transcription_text)
        print(f"Saved transcription to {transcription_filename}")

        # Use the 'webbrowser' module to open the text file in the default browser
        file_url = 'file://' + os.path.abspath(transcription_filename)
        webbrowser.open(file_url)

    except Exception as e:
        print(f"An error occurred while creating the transcription: {e}")

    
    

def main():
    subject = input("Please enter a subject for the video: ")
    video_path, video_id = video_search_and_download(subject)  # Now only returns video path and ID
    
    # Download audio using the video ID
    audio_path = download_audio(video_id) if video_id else None
    
    if video_path:
        detect_and_save_scenes(video_path)
    else:
        print("Failed to download video for scene detection.")
    
    # Create transcription if audio was downloaded
    if audio_path:
        transcribe_mp3_to_file(text_to_speech_key, audio_path)  # This replaces create_transcription
        
    else:
        print("Failed to download audio for transcription.")


if __name__ == "__main__":
    main()



    main()