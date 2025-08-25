import os
import yt_dlp
from flask import Blueprint, render_template, request, redirect, url_for, flash
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from datetime import datetime
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)

# Directories where downloads and trimmed videos will be stored
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
TRIMMED_FOLDER = os.path.join(os.getcwd(), 'trimmed_videos')

# Function to trim videos
def get_unique_output_path(input_dir, input_filename):
    base_filename, ext = os.path.splitext(input_filename)
    output_filename = f"{base_filename}_trimmed{ext}"
    return os.path.join(input_dir, output_filename)

def trim_video(input_file_path, output_file_path, start_time, duration):
    end_time = start_time + duration
    ffmpeg_extract_subclip(input_file_path, start_time, end_time, targetname=output_file_path)

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}  # Add allowed video extensions

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/upload', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'video' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['video']
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(DOWNLOAD_FOLDER, filename))
            # Return success with trim option
            flash(f'Video "{filename}" uploaded successfully! Would you like to trim it now?', 'upload_success')
            return redirect(url_for('main.index', uploaded_file=filename, show_trim='true'))
    return render_template('upload.html')

# Combined route for both downloading and trimming videos
@main_bp.route('/', methods=['GET', 'POST'])
def index():
    message = None
    current_year = datetime.now().year
    videos = os.listdir(DOWNLOAD_FOLDER)  # Get the list of downloaded videos
    
    # Check if coming from upload with trim suggestion
    uploaded_file = request.args.get('uploaded_file')
    show_trim = request.args.get('show_trim')

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle the download action
        if action == "Download Playlist":
            playlist_url = request.form.get('url')
            format_choice = request.form.get('format', 'mp3')  # Default to MP3

            if playlist_url:
                try:
                    # Check if a file with the same name already exists in the download folder
                    if any(file.startswith(os.path.basename(playlist_url)) for file in os.listdir(DOWNLOAD_FOLDER)):
                        message = "A video from this playlist has already been downloaded."
                    else:
                        if format_choice == 'mp4':  # Video download
                            ydl_opts = {
                                'format': 'bestvideo+bestaudio[ext=mp4]/best[ext=mp4]/best',
                                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                                'merge_output_format': 'mp4',
                                'ffmpeg_location': r'C:\ffmpeg\bin\ffmpeg.exe'
                            }
                        else:  # Audio download
                            ydl_opts = {
                                'format': 'bestaudio/best',
                                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                                'postprocessors': [{
                                    'key': 'FFmpegExtractAudio',
                                    'preferredcodec': format_choice,
                                    'preferredquality': '192',
                                }],
                                'postprocessor_args': ['-ar', '16000'],
                                'ffmpeg_location': r'C:\ffmpeg\bin\ffmpeg.exe'
                            }

                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([playlist_url])
                        message = f"Download completed in {format_choice.upper()} format! Check the 'downloads' folder."
                except Exception as e:
                    message = f"An error occurred during download: {e}"

        # Handle the trim video action
        elif action == "Trim Video":
            video_file = request.form.get('video_file')
            start_time = request.form.get('start_time')
            duration = request.form.get('duration')

            if video_file and start_time and duration:
                try:
                    start_time = float(start_time)
                    duration = float(duration)

                    input_file_path = os.path.join(DOWNLOAD_FOLDER, video_file)
                    output_file_path = get_unique_output_path(TRIMMED_FOLDER, video_file)  # Use the function to generate a unique output path

                    # Trim the video
                    trim_video(input_file_path, output_file_path, start_time, duration)

                    # Provide a direct download link for the trimmed video
                    trimmed_filename = os.path.basename(output_file_path)
                    message = f"""
                    Video trimmed successfully! 
                    <a href='/download_trimmed/{trimmed_filename}' download class='btn btn-primary mt-2'>Download Trimmed Video</a>
                    """
                except Exception as e:
                    message = f"An error occurred during trimming: {e}"
            else:
                message = "Please provide valid inputs for video trimming."

    return render_template('index.html', videos=videos, message=message, current_year=current_year, 
                          uploaded_file=uploaded_file, show_trim=show_trim)