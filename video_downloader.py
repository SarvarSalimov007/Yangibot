import yt_dlp
import os
import asyncio
import subprocess
import time
import random
import string

class VideoDownloader:
    def __init__(self):
        self.output_dir = "downloads"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.ffmpeg_available = self._check_ffmpeg()
        
        # Advanced headers to avoid blocking
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def _check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            return False

    def _generate_unique_id(self, length=6):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    async def extract_info(self, url):
        """
        Ultra-robust metadata extraction.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'check_formats': True,
            'user_agent': self.user_agent,
            'add_header': [
                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language: en-US,en;q=0.9',
            ],
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'no_color': True,
            'extract_flat': False,
        }
        
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                 info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                 
            formats = info.get('formats', [])
            available_qualities = set()
            
            for f in formats:
                # Handle cases where height/resolution is missing but it's a valid format
                height = f.get('height')
                if f.get('vcodec') != 'none' and height:
                    if height >= 2160: available_qualities.add('4k')
                    elif height >= 1440: available_qualities.add('2k')
                    elif height >= 1080: available_qualities.add('1080p')
                    elif height >= 720: available_qualities.add('720p')
                    elif height >= 480: available_qualities.add('480p')
                    elif height >= 360: available_qualities.add('360p')
                    else: available_qualities.add('low')

            # If no heights found but formats exist, at least add 'best'
            if not available_qualities and formats:
                available_qualities.add('best')

            priority = ['4k', '2k', '1080p', '720p', '480p', '360p', 'low', 'best']
            sorted_qualities = [q for q in priority if q in available_qualities]
            
            return sorted_qualities, info.get('title', 'Video')
            
        except Exception as e:
            print(f"Extraction Error: {e}")
            return [], None

    async def download_video(self, url, quality):
        """
        Ultra-robust downloader with fallback logic and unique filenames.
        """
        unique_id = self._generate_unique_id()
        
        # Map quality to height
        h_map = {'4k': 2160, '2k': 1440, '1080p': 1080, '720p': 720, '480p': 480, '360p': 360}
        target_h = h_map.get(quality, 0)

        # Build format string for stability
        if self.ffmpeg_available:
            if target_h > 0:
                format_str = f"bestvideo[height<={target_h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={target_h}]/best"
            else:
                format_str = "bestvideo+bestaudio/best"
        else:
            # WITHOUT FFMPEG: We MUST use a single format that has both video and audio
            if target_h > 0:
                format_str = f"best[height<={target_h}][ext=mp4]/best[height<={target_h}]/best"
            else:
                format_str = "best"

        # Unique template to avoid conflicts
        filename = f"dl_{quality}_{unique_id}_%(id)s.%(ext)s"
        outtmpl = os.path.join(self.output_dir, filename)

        ydl_opts = {
            'format': format_str,
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'user_agent': self.user_agent,
            'nocheckcertificate': True,
            'merge_output_format': 'mp4' if self.ffmpeg_available else None,
            'writethumbnail': False,
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}] if self.ffmpeg_available else [],
            'noplaylist': True,
        }

        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Run download in executor to keep bot responsive
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
                
                # Retrieve the actual filepath from info
                # yt-dlp might have merged or changed extension
                if 'requested_downloads' in info:
                    filepath = info['requested_downloads'][0]['filepath']
                else: 
                    filepath = ydl.prepare_filename(info)
                
                # Double check existence and potential extension changes (e.g. .mkv -> .mp4)
                if not os.path.exists(filepath):
                    base = os.path.splitext(filepath)[0]
                    for ext in ['.mp4', '.mkv', '.webm', '.flv', '.3gp']:
                        if os.path.exists(base + ext):
                            filepath = base + ext
                            break
                            
                return filepath
        except Exception as e:
            print(f"Download Error for {url}: {e}")
            return None
