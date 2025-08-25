# MediaSculp 2.0 - Professional Media Processing Suite

![MediaSculp Logo](static/QidayaLogo-small.png)

MediaSculp 2.0 is an enterprise-grade web application for downloading, processing, and managing video content from 1000+ platforms including YouTube, TikTok, Instagram, and more. Built with Flask and featuring a modern navy blue professional interface, MediaSculp provides a seamless experience for content creators and professionals.

**Latest Update (December 2024):** Fixed critical modal freezing issue with custom modal implementation.

## 🎯 Key Features

### Core Functionality
- **Universal Video Downloader:** Download videos from 1000+ platforms using yt-dlp
- **Multi-Format Support:** Export to MP3, WAV, OGG, MP4, and more
- **Precision Video Trimming:** Frame-accurate video editing with decimal precision
- **Batch Processing:** Download entire playlists with a single click
- **Quality Selection:** Choose from multiple quality options (Best, 1080p, 720p, 480p, etc.)

### Professional Interface
- **Enterprise Design:** Navy blue & white color scheme with ultra-compact navigation
- **Responsive Layout:** Fully responsive Bootstrap 5 interface
- **Real-time Statistics:** Dynamic file counting and storage monitoring
- **Advanced Search:** Instant file filtering with keyboard shortcuts (Ctrl+K)
- **Video Previews:** In-browser video and audio preview capabilities

## 🚀 Quick Start

### Prerequisites
- Python 3.6 or above
- [FFmpeg](https://ffmpeg.org/download.html) installed and in PATH
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bomino/MediaSculp2.0.git
   cd MediaSculp2.0
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create required directories:**
   ```bash
   mkdir downloads trimmed_videos
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the application:**
   Open your browser and navigate to `http://127.0.0.1:5000`

## 📁 Project Structure

```
MediaSculpModal/
├── app.py                 # Main Flask application
├── routes/
│   ├── main.py           # Core download & trim routes
│   └── downloads.py      # File management routes
├── templates/
│   ├── base.html         # Base template with navbar/footer
│   ├── index.html        # Home page with tabs
│   ├── downloads.html    # Downloads manager
│   └── trimmed_videos.html # Trimmed videos manager
├── static/
│   ├── styles.css        # Professional navy theme CSS
│   └── QidayaLogo-small.png # Application logo
├── downloads/            # Downloaded files directory
├── trimmed_videos/       # Processed videos directory
├── requirements.txt      # Python dependencies
├── CLAUDE.md            # AI assistant documentation
└── README.md            # This file
```

## 💻 Usage Guide

### Downloading Videos

1. Navigate to the **Home** page
2. Select the **Download** tab
3. Paste any video URL (YouTube, TikTok, Instagram, etc.)
4. Choose output format:
   - **Audio:** MP3, WAV, OGG
   - **Video:** MP4 with quality selection
5. Optional: Check "Download entire playlist" for playlist URLs
6. Click **Start Download**

### Trimming Videos

1. Navigate to the **Trim Video** tab
2. Select a downloaded video from the dropdown
3. Enter start time (supports decimals, e.g., 5.5 seconds)
4. Enter duration for the clip
5. Click **Trim Video**
6. Find your trimmed video in the **Trimmed** section

### File Management

- **Downloads Page:** View, preview, and delete downloaded files
- **Trimmed Page:** Manage your edited video clips
- **Search:** Use Ctrl+K to quickly search files
- **Preview:** Hover over videos for instant preview

## 🎨 Design System

### Color Palette
- **Primary Navy:** #0A2540
- **Accent Blue:** #0066FF
- **White:** #FFFFFF
- **Gray Scale:** #F6F8FA to #4B5563

### Key Design Features
- Ultra-compact 48px navbar
- Gradient effects and animations
- Premium card designs with hover effects
- Professional typography (Inter font)
- Responsive grid layouts
- Enterprise-grade footer with newsletter signup

## 🛠️ Technical Stack

### Backend
- **Flask:** Web framework
- **yt-dlp:** Video downloading engine
- **MoviePy:** Video processing and trimming
- **FFmpeg:** Media codec support

### Frontend
- **Bootstrap 5:** Responsive framework
- **Font Awesome 6:** Icon library
- **Custom CSS:** Navy blue professional theme
- **JavaScript:** Dynamic UI interactions

## 📋 Requirements

```txt
Flask==2.3.3
yt-dlp==2023.7.6
moviepy==1.0.3
Werkzeug==2.3.7
```

## 🔧 Configuration

### FFmpeg Setup
Ensure FFmpeg is properly installed:
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt-get install ffmpeg`

### Custom Settings
Edit `routes/main.py` to customize:
- Download quality defaults
- Output formats
- File naming patterns
- Processing options

## 🚦 API Endpoints

- `GET /` - Home page with download/trim interface
- `POST /` - Process download or trim request
- `GET /downloads` - View downloaded files
- `GET /trimmed_videos` - View trimmed videos
- `POST /delete_file/<filename>` - Delete downloaded file
- `POST /delete_trimmed_video/<filename>` - Delete trimmed video
- `GET /download/<filename>` - Download file
- `GET /download_trimmed/<filename>` - Download trimmed video

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [MoviePy](https://zulko.github.io/moviepy/) - Video processing
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Bootstrap](https://getbootstrap.com/) - UI framework
- [Font Awesome](https://fontawesome.com/) - Icons
- [Qidaya](https://qidaya.com) - Branding and design

## 📞 Support

For questions or support:
- Email: info@qidaya.com
- Website: [MediaSculp Professional](https://mediasculp.com)
- Issues: [GitHub Issues](https://github.com/bomino/MediaSculp2.0/issues)

---

**MediaSculp 2.0** - Professional Video Processing Suite  
Version 2.0.0 | Last Updated: December 2024