import yt_dlp
import os
import asyncio
import subprocess

class VideoDownloader:
    def __init__(self):
        self.output_dir = "downloads"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            return False

    async def extract_info(self, url):
        """
        Extracts video metadata and available formats.
        Returns a list of available resolutions.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'check_formats': True,
        }
        
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                 info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                 
            formats = info.get('formats', [])
            available_qualities = set()
            
            for f in formats:
                # Filter for video streams
                if f.get('vcodec') != 'none' and f.get('height'):
                    height = f['height']
                    
                    # If ffmpeg is missing, YouTube 1080p+ won't have audio
                    # We still list them, but we should be aware
                    if height >= 2160:
                        available_qualities.add('4k')
                    elif height >= 1440:
                        available_qualities.add('2k')
                    elif height >= 1080:
                        available_qualities.add('1080p')
                    elif height >= 720:
                        available_qualities.add('720p')
                    elif height >= 480:
                        available_qualities.add('480p')
                    elif height >= 360:
                        available_qualities.add('360p')
                    else:
                        available_qualities.add('low')

            # Sort qualities for display
            priority = ['4k', '2k', '1080p', '720p', '480p', '360p', 'low']
            sorted_qualities = [q for q in priority if q in available_qualities]
            
            return sorted_qualities, info.get('title', 'Video')
            
        except Exception as e:
            print(f"Error extracting info: {e}")
            return [], None

    async def download_video(self, url, quality):
        """
        Downloads the video in the specified quality.
        Returns the path to the downloaded file.
        """
        # Improved format selection logic
        if quality == '4k':
            h = 2160
        elif quality == '2k':
            h = 1440
        elif quality == '1080p':
            h = 1080
        elif quality == '720p':
            h = 720
        elif quality == '480p':
            h = 480
        elif quality == '360p':
            h = 360
        else:
            h = 0

        if h > 0:
            # Try to get video+audio for the requested height
            # If ffmpeg is missing, this might only get a lower quality that has both,
            # or it might get the high quality video only (depending on site)
            if self.ffmpeg_available:
                format_str = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
            else:
                # Without ffmpeg, we prefer combined formats (usually up to 720p)
                # or just the best single file with audio
                format_str = f"best[height<={h}][ext=mp4]/best[height<={h}]/best"
        else:
            format_str = "best"

        # Output template
        filename = f"video_{quality}_%(id)s.%(ext)s"
        outtmpl = os.path.join(self.output_dir, filename)

        ydl_opts = {
            'format': format_str,
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4' if self.ffmpeg_available else None,
        }

        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
                
                if 'requested_downloads' in info:
                    filepath = info['requested_downloads'][0]['filepath']
                else: 
                    filepath = ydl.prepare_filename(info)
                
                # Check if file actually exists (yt-dlp sometimes changes extension)
                if not os.path.exists(filepath):
                    # Try to find it if extension changed
                    base = os.path.splitext(filepath)[0]
                    for ext in ['.mp4', '.mkv', '.webm']:
                        if os.path.exists(base + ext):
                            filepath = base + ext
                            break
                            
                return filepath
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None
