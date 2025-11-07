import os
from typing import Any

import yt_dlp


class Downloader:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def download(self, url: str) -> str:
        self._initialize_youtube_dl()

        self.youtube_dl.download(url)
        url_data = self.youtube_dl.extract_info(url, download=False)

        filename = f"{url_data['id']}.{url_data['ext']}"
        return filename

    def _initialize_youtube_dl(self) -> None:
        self.youtube_dl = yt_dlp.YoutubeDL(self._config())

    def _config(self) -> dict[str, Any]:
        config = {
            'ignoreerrors': True,
            'noplaylist': True,
            'outtmpl': os.path.join(self.output_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'verbose': False,
            'format': "bestaudio"
        }

        return config
