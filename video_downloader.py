import yt_dlp  # type: ignore
import os
import asyncio
import subprocess
import time
import random
import string
from typing import Any, cast, List

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
        Ultra-robust and fast metadata extraction with timeouts.
        """
        # Common options for both extraction and download
        base_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': self.user_agent,
            'nocheckcertificate': True,
            'no_color': True,
            'socket_timeout': 10, # 10 second timeout for network operations
            'retries': 3,
            'add_header': [
                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language: en-US,en;q=0.9',
            ],
        }

        ydl_opts = {
            **base_opts,
            'skip_download': True,
            'check_formats': False, # Faster extraction
            'lazy_playlist': True,
            'extract_flat': 'in_playlist',
        }
        
        loop = asyncio.get_event_loop()
        try:
            # Wrap the extractor in a timeout to prevent persistent hangs
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Use a larger timeout for the overall process (20s)
                # We use a simple lambda with positional args to satisfy the linter
                info_raw: Any = await asyncio.wait_for(
                    loop.run_in_executor(None, ydl.extract_info, url, False),
                    timeout=20.0
                )
                info = cast(dict[str, Any], info_raw)
                 
            if not info or not isinstance(info, dict):
                return [], None
                 
            if not info:
                return [], None

            formats = info.get('formats', [])
            available_qualities = set()
            
            # Filter formats to ensure they have video AND aren't just storyboards
            for f in formats:
                height = f.get('height')
                # Ignore if no height or if it's a known non-video format (like mhtml)
                if height and f.get('vcodec') != 'none':
                    if height >= 2160: available_qualities.add('4k')
                    elif height >= 1440: available_qualities.add('2k')
                    elif height >= 1080: available_qualities.add('1080p')
                    elif height >= 720: available_qualities.add('720p')
                    elif height >= 480: available_qualities.add('480p')
                    elif height >= 360: available_qualities.add('360p')
                    else: available_qualities.add('low')

            # Fallback if no specific heights found
            if not available_qualities and formats:
                available_qualities.add('best')

            priority = ['4k', '2k', '1080p', '720p', '480p', '360p', 'low', 'best']
            sorted_qualities = [q for q in priority if q in available_qualities]
            
            # If still empty, try to just return 'best' as a last resort
            if not sorted_qualities:
                sorted_qualities = ['best']

            # Avoid slicing to satisfy all linter types
            final_qualities: List[str] = []
            for i in range(min(len(sorted_qualities), 6)):
                val = sorted_qualities[i]
                final_qualities.append(str(val))
                
            return final_qualities, str(info.get('title', 'Video'))
            
        except asyncio.TimeoutError:
            print(f"Extraction Timeout for {url}")
            return [], "TIMEOUT"
        except Exception as e:
            print(f"Extraction Error: {e}")
            error_msg = str(e)
            if "sign in" in error_msg.lower(): return [], "SIGN_IN"
            if "private" in error_msg.lower(): return [], "PRIVATE"
            return [], "ERROR"

    async def download_video(self, url, quality):
        """
        Optimized downloader for maximum speed and exact quality with timeouts.
        """
        unique_id = self._generate_unique_id()
        
        # Map quality to height
        h_map = {'4k': 2160, '2k': 1440, '1080p': 1080, '720p': 720, '480p': 480, '360p': 360}
        target_h = h_map.get(quality, 0)

        # Build format string for stability and quality
        if self.ffmpeg_available:
            if target_h > 0:
                format_str = (
                    f"bestvideo[height={target_h}][ext=mp4]+bestaudio[ext=m4a]/"
                    f"bestvideo[height<={target_h}][ext=mp4]+bestaudio[ext=m4a]/"
                    f"bestvideo[height<={target_h}]+bestaudio/"
                    f"best[height<={target_h}][ext=mp4]/"
                    f"best"
                )
            else:
                format_str = "bestvideo+bestaudio/best"
        else:
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
            'noplaylist': True,
            
            # --- SPEED OPTIMIZATIONS ---
            'concurrent_fragment_downloads': 15, # Increased for speed
            'retries': 5,
            'fragment_retries': 5,
            'socket_timeout': 15,
            'buffersize': 1024 * 1024, # 1MB buffer
            'http_chunk_size': 10 * 1024 * 1024, # 10MB chunks
            
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}] if self.ffmpeg_available else [],
        }

        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Overall download timeout (5 minutes for big videos)
                info_raw: Any = await asyncio.wait_for(
                    loop.run_in_executor(None, ydl.extract_info, url),
                    timeout=300.0
                )
                
                info = cast(dict[str, Any], info_raw)
                
                if not info or not isinstance(info, dict):
                    return None
                
                if 'requested_downloads' in info:
                    filepath = info['requested_downloads'][0]['filepath']
                else: 
                    filepath = ydl.prepare_filename(info)
                
                # Verify existence and extension
                if not os.path.exists(filepath):
                    base = os.path.splitext(filepath)[0]
                    for ext in ['.mp4', '.mkv', '.webm', '.flv', '.3gp']:
                        if os.path.exists(base + ext):
                            filepath = base + ext
                            break
                            
                return filepath
        except asyncio.TimeoutError:
            print(f"Download Timeout for {url}")
            return None
        except Exception as e:
            print(f"Download Error for {url}: {e}")
            return None
