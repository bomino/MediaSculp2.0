# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MediaSculp 2.0 is a Flask-based web application for downloading and processing media from YouTube and TikTok. It provides functionality for downloading videos/audio in various formats and trimming video files.

## Recent Updates (December 2024)

### Fixed Delete Modal Freezing Issue
- **Problem**: Bootstrap modals were causing the entire app to freeze when deleting files
- **Solution**: Implemented custom modal solution without Bootstrap JavaScript
- **Key Learning**: KISS (Keep It Simple, Stupid) - Complex Bootstrap modal management was replaced with simple HTML/CSS/JavaScript

## Development Commands

### Running the Application
```bash
python app.py  # Runs on http://127.0.0.1:5000 with debug mode enabled
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Virtual Environment
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

## Architecture Overview

### Core Components

1. **Flask Application Structure**
   - Uses Flask Blueprints for modular route organization
   - Main app entry point: `app.py`
   - Routes split into:
     - `routes/main.py`: Core functionality (downloading, trimming)
     - `routes/downloads.py`: File management endpoints

2. **Media Processing Pipeline**
   - **Downloading**: Uses `yt-dlp` library for YouTube/playlist downloads
   - **Video Trimming**: Uses `moviepy` with FFmpeg backend
   - **File Storage**: Two main directories:
     - `downloads/`: Stores downloaded media files
     - `trimmed_videos/`: Stores processed/trimmed videos

3. **External Dependencies**
   - **FFmpeg**: Required system dependency (hardcoded path: `C:\ffmpeg\bin\ffmpeg.exe`)
   - **yt-dlp**: YouTube download functionality
   - **moviepy**: Video editing operations

### Key Technical Details

- **Supported Video Formats**: MP4, MOV, AVI, MKV
- **Supported Audio Formats**: MP3, WAV, OGG
- **File Upload Security**: Uses `werkzeug.utils.secure_filename` for sanitization
- **Blueprint Registration**: Modular route handling via Flask Blueprints
- **Template Engine**: Jinja2 with base template inheritance
- **Frontend**: Bootstrap-based responsive UI

### Important File Paths

- Download functionality expects FFmpeg at: `C:\ffmpeg\bin\ffmpeg.exe`
- Media files stored in project-relative directories (created automatically)
- SQLite database: `actions.db` (purpose unclear from current code)

## Custom Modal Implementation

The delete functionality uses a custom modal instead of Bootstrap's modal JavaScript to avoid freezing issues:

```javascript
// Custom modal HTML structure (no Bootstrap JS)
<div id="customDeleteModal" style="display: none; ...">
    <!-- Backdrop and modal content -->
</div>

// Simple show/hide functions
function showDeleteConfirm(filename) { /* ... */ }
function hideDeleteConfirm() { /* ... */ }
function confirmDelete() { /* ... */ }
```

**Important**: Never use Bootstrap's `new bootstrap.Modal()` for delete confirmations as it can cause the app to freeze.

## Key Considerations

1. **FFmpeg Path**: Currently hardcoded for Windows - needs adjustment for cross-platform support
2. **File Validation**: Implements extension-based validation for uploads
3. **Error Handling**: Try-catch blocks around download and trim operations
4. **Duplicate Prevention**: Checks for existing downloads before re-downloading