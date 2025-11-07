"""
Main scraper module for URL content extraction.
"""

import io
import re
import time
from typing import Optional, Dict, List, Union
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


class URLScraper:
    """
    A scraper class that extracts content from URLs.

    For YouTube URLs, it returns the video transcript with timestamps.
    For PDF files, it extracts and returns the text content.
    For other URLs, it returns the text content of the page.
    """

    YOUTUBE_PATTERNS = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/embed\/([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/v\/([a-zA-Z0-9_-]{11})",
    ]

    def __init__(
        self,
        timeout: int = 30,
        user_agent: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the URL scraper.

        Args:
            timeout: Request timeout in seconds (default: 30)
            user_agent: Custom user agent string (optional)
            max_retries: Maximum number of retry attempts for failed requests (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()

        if user_agent:
            self.session.headers.update({"User-Agent": user_agent})
        else:
            self.session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                }
            )

    def _retry_request(self, url: str) -> requests.Response:
        """
        Make an HTTP request with retry logic and exponential backoff.

        Args:
            url: The URL to request

        Returns:
            The response object

        Raises:
            requests.RequestException: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except (
                requests.Timeout,
                requests.ConnectionError,
                requests.HTTPError,
            ) as e:
                last_exception = e

                if isinstance(e, requests.HTTPError):
                    if (
                        400 <= e.response.status_code < 500
                        and e.response.status_code != 429
                    ):
                        raise

                if attempt == self.max_retries - 1:
                    break

                wait_time = self.retry_delay * (2**attempt)
                time.sleep(wait_time)

        raise last_exception

    def _is_youtube_url(self, url: str) -> bool:
        """
        Check if a URL is a YouTube URL.

        Args:
            url: The URL to check

        Returns:
            True if the URL is a YouTube URL, False otherwise
        """
        for pattern in self.YOUTUBE_PATTERNS:
            if re.search(pattern, url):
                return True
        return False

    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract the YouTube video ID from a URL.

        Args:
            url: The YouTube URL

        Returns:
            The video ID if found, None otherwise
        """
        for pattern in self.YOUTUBE_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        parsed = urlparse(url)
        if "youtube.com" in parsed.netloc:
            query_params = parse_qs(parsed.query)
            if "v" in query_params:
                return query_params["v"][0]

        return None

    def _get_youtube_transcript(
        self, video_id: str, languages: Optional[List[str]] = None
    ) -> Dict[str, Union[str, List[Dict[str, Union[str, float]]]]]:
        """
        Get the transcript for a YouTube video.

        Args:
            video_id: The YouTube video ID
            languages: List of preferred language codes (default: ['en'])

        Returns:
            Dictionary containing transcript data with 'text' and 'segments' keys

        Raises:
            Exception: If transcript cannot be retrieved
        """
        if languages is None:
            languages = ["en"]

        try:
            ytt_api = YouTubeTranscriptApi()

            try:
                transcript_list = ytt_api.list(video_id)

                try:
                    transcript = transcript_list.find_transcript(languages)
                except NoTranscriptFound:
                    transcript = transcript_list.find_generated_transcript(["en"])

                transcript_data = transcript.fetch()

                segments = []
                full_text = []

                for entry in transcript_data:
                    segment = {
                        "text": entry.text,
                        "start": entry.start,
                        "duration": entry.duration,
                    }
                    segments.append(segment)
                    full_text.append(entry.text)

                return {
                    "text": " ".join(full_text),
                    "segments": segments,
                    "language": transcript.language,
                    "language_code": transcript.language_code,
                    "is_generated": transcript.is_generated,
                }

            except Exception:
                # Fallback: Try direct fetch method
                transcript_data = ytt_api.fetch(video_id, languages=languages)

                # Extract text segments
                segments = []
                full_text = []

                for entry in transcript_data:
                    segment = {
                        "text": entry.text,
                        "start": entry.start,
                        "duration": entry.duration,
                    }
                    segments.append(segment)
                    full_text.append(entry.text)

                return {
                    "text": " ".join(full_text),
                    "segments": segments,
                    "language": (
                        transcript_data.language
                        if hasattr(transcript_data, "language")
                        else "Unknown"
                    ),
                    "language_code": (
                        transcript_data.language_code
                        if hasattr(transcript_data, "language_code")
                        else languages[0]
                    ),
                    "is_generated": (
                        transcript_data.is_generated
                        if hasattr(transcript_data, "is_generated")
                        else False
                    ),
                }

        except TranscriptsDisabled:
            raise Exception(f"Transcripts are disabled for video: {video_id}")
        except VideoUnavailable:
            raise Exception(f"Video unavailable: {video_id}")
        except Exception as e:
            raise Exception(f"Error retrieving transcript: {str(e)}")

    def _is_pdf_url(self, url: str) -> bool:
        """
        Check if a URL likely points to a PDF file based on extension.

        Args:
            url: The URL to check

        Returns:
            True if the URL appears to be a PDF, False otherwise
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        return path.endswith(".pdf")

    def _get_pdf_content(self, url: str) -> str:
        """
        Extract text content from a PDF file.

        Args:
            url: The URL to the PDF file

        Returns:
            The extracted text content from the PDF

        Raises:
            Exception: If the PDF cannot be retrieved or parsed
        """
        try:
            response = self._retry_request(url)

            content_type = response.headers.get("Content-Type", "").lower()
            if "application/pdf" not in content_type and not self._is_pdf_url(url):
                raise ValueError("Content is not a PDF")

            pdf_file = io.BytesIO(response.content)
            pdf_reader = PdfReader(pdf_file)

            text_parts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)

            lines = (line.strip() for line in full_text.splitlines())
            full_text = " ".join(line for line in lines if line)

            return full_text

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Error extracting PDF content: {str(e)}")

    def _get_webpage_content(self, url: str) -> str:
        """
        Get the text content from a webpage with retry logic.

        Args:
            url: The URL to scrape

        Returns:
            The extracted text content

        Raises:
            Exception: If the webpage cannot be retrieved after all retries
        """
        try:
            response = self._retry_request(url)

            soup = BeautifulSoup(response.content, "lxml")

            for script in soup(["script", "style", "header", "footer", "nav"]):
                script.decompose()

            text = soup.get_text(separator=" ", strip=True)

            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except requests.RequestException as e:
            raise Exception(
                f"Error fetching URL after {self.max_retries} attempts: {str(e)}"
            )
        except Exception as e:
            raise Exception(f"Error parsing content: {str(e)}")

    def scrape(
        self, url: str, languages: Optional[List[str]] = None
    ) -> Union[str, Dict[str, Union[str, List[Dict[str, Union[str, float]]]]]]:
        """
        Scrape content from a URL.

        For YouTube URLs, returns a dictionary with transcript data.
        For PDF URLs, returns the extracted text content.
        For other URLs, returns the text content as a string.

        Args:
            url: The URL to scrape
            languages: List of preferred language codes for YouTube transcripts (default: ['en'])

        Returns:
            For YouTube: Dictionary with 'text', 'segments', 'language', etc.
            For PDFs and webpages: String containing the text content

        Raises:
            ValueError: If the URL is invalid
            Exception: If scraping fails

        Examples:
            >>> scraper = URLScraper()
            >>> # Scrape a YouTube video
            >>> result = scraper.scrape("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            >>> print(result['text'])  # Full transcript text
            >>>
            >>> # Scrape a PDF document
            >>> text = scraper.scrape("https://example.com/document.pdf")
            >>> print(text)  # PDF text content
            >>>
            >>> # Scrape a regular webpage
            >>> text = scraper.scrape("https://example.com")
            >>> print(text)  # Webpage text content
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        url = url.strip()

        if self._is_youtube_url(url):
            video_id = self._extract_video_id(url)
            if not video_id:
                raise ValueError(f"Could not extract video ID from URL: {url}")
            return self._get_youtube_transcript(video_id, languages)

        if self._is_pdf_url(url):
            try:
                return self._get_pdf_content(url)
            except ValueError:
                pass
        try:
            return self._get_pdf_content(url)
        except (ValueError, Exception):
            return self._get_webpage_content(url)

    def scrape_text_only(self, url: str, languages: Optional[List[str]] = None) -> str:
        """
        Scrape content from a URL and return only the text.

        This is a convenience method that always returns a string,
        extracting just the text from YouTube transcripts.

        Args:
            url: The URL to scrape
            languages: List of preferred language codes for YouTube transcripts (default: ['en'])

        Returns:
            The text content as a string

        Examples:
            >>> scraper = URLScraper()
            >>> text = scraper.scrape_text_only("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            >>> print(text)  # Just the transcript text
        """
        result = self.scrape(url, languages)

        if isinstance(result, dict):
            return result["text"]
        return result
