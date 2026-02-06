import yt_dlp
import os
import asyncio

class VideoDownloader:
    def __init__(self):
        self.output_dir = "downloads"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def extract_info(self, url):
        """
        Extracts video metadata and available formats.
        Returns a list of available resolutions (e.g., ['144p', '360p', '720p', '1080p']).
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                 info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                 
            formats = info.get('formats', [])
            available_qualities = set()
            
            for f in formats:
                # Filter for video streams that have resolution info
                if f.get('vcodec') != 'none' and f.get('height'):
                    height = f['height']
                    # Group common resolutions
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

            # Sort qualities for display (custom sort order)
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
        # Map simple quality names to yt-dlp format strings
        format_str = ""
        if quality == '4k':
            format_str = "bestvideo[height>=2160]+bestaudio/best[height>=2160]/best"
        elif quality == '2k':
            format_str = "bestvideo[height>=1440]+bestaudio/best[height>=1440]/best"
        elif quality == '1080p':
            format_str = "bestvideo[height>=1080]+bestaudio/best[height>=1080]/best"
        elif quality == '720p':
            format_str = "bestvideo[height>=720]+bestaudio/best[height>=720]/best"
        elif quality == '480p':
            format_str = "bestvideo[height>=480]+bestaudio/best[height>=480]/best"
        elif quality == '360p':
            format_str = "bestvideo[height>=360]+bestaudio/best[height>=360]/best"
        else:
            format_str = "best"

        # Output template
        filename = f"video_{quality}_{{id}}.{{ext}}"
        outtmpl = os.path.join(self.output_dir, filename)

        ydl_opts = {
            'format': format_str,
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            # We want to merge video+audio if possible (ffmpeg required)
            'merge_output_format': 'mp4', 
        }

        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
                # Get the filename of the downloaded file
                if 'requested_downloads' in info:
                    # if it was merged or processed
                    filepath = info['requested_downloads'][0]['filepath']
                else: 
                     # direct download
                    filepath = ydl.prepare_filename(info)
                
                return filepath
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None
