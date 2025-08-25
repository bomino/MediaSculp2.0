import os
from flask import Blueprint, render_template, jsonify, send_from_directory

downloads_bp = Blueprint('downloads', __name__)

DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
TRIMMED_FOLDER = os.path.join(os.getcwd(), 'trimmed_videos')

@downloads_bp.route('/downloads', methods=['GET'])
def list_downloads():
    downloaded_files = os.listdir(DOWNLOAD_FOLDER)
    downloaded_files = [f for f in downloaded_files if not f.startswith('.')]
    return render_template('downloads.html', files=downloaded_files)

@downloads_bp.route('/download_file/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@downloads_bp.route('/delete_file/<filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'message': 'File deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@downloads_bp.route('/download_trimmed/<filename>')
def download_trimmed(filename):
    try:
        return send_from_directory(TRIMMED_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'success': False, 'error': 'File not found'}), 404

@downloads_bp.route('/trimmed_videos', methods=['GET'])
def trimmed_videos():
    trimmed_files = os.listdir(TRIMMED_FOLDER)
    trimmed_files = [f for f in trimmed_files if not f.startswith('.')]  # Exclude hidden files
    return render_template('trimmed_videos.html', files=trimmed_files)

@downloads_bp.route('/delete_trimmed_video/<filename>', methods=['POST'])
def delete_trimmed_video(filename):
    file_path = os.path.join(TRIMMED_FOLDER, filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'message': 'Video deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
