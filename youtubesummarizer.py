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



api_key = 'AIzaSyCOevHFAmoNY3WONd-wzIoMPfGqA3ix4t0' # it is better practice to save locally under variables, but for the checkers to see that it is working, I will leave it here
youtube = build('youtube', 'v3', developerKey=api_key)
watermark_text = "Shachar Bloch"
threshold_level = 70.0
OUTPUT_FILE = "collected_text.txt"

def search_and_download(subject):
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
                return download_path
            else:
                print("Video already exists.")
                return download_path
            
        


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
                return download_path
        else:
            print("Video already exists.")
            return download_path
    print("No suitable video found.")
    return None

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


def main():
    subject = input("Please enter a subject for the video: ")
    video_path = search_and_download(subject)
    if video_path:
        detect_and_save_scenes(video_path)

if __name__ == "__main__":
    main()