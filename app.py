import os
from flask import Flask
from routes.main import main_bp
from routes.downloads import downloads_bp

app = Flask(__name__)

# Set secret key for session management (required for flash messages)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production-2024'

# Directories where downloads and trimmed videos will be stored
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
TRIMMED_FOLDER = os.path.join(os.getcwd(), 'trimmed_videos')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(TRIMMED_FOLDER, exist_ok=True)

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(downloads_bp)

if __name__ == "__main__":
    app.run(debug=True)
