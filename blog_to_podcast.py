import os
from uuid import uuid4
import asyncio
from firecrawl import AsyncFirecrawlApp
from agno.agent import Agent
from agno.models.google import Gemini
from agno.agent import RunResponse
from elevenlabs.client import ElevenLabs
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

class BlogToPodcastAgent:
    def __init__(self, 
                 gemini_api_key: str = None, 
                 elevenlabs_api_key: str = None, 
                 firecrawl_api_key: str = None):
        self.gemini_api_key = gemini_api_key or GEMINI_API_KEY
        self.elevenlabs_api_key = elevenlabs_api_key or ELEVENLABS_API_KEY
        self.firecrawl_api_key = firecrawl_api_key or FIRECRAWL_API_KEY
        if not all([self.gemini_api_key, self.elevenlabs_api_key, self.firecrawl_api_key]):
            raise ValueError("All API keys must be provided via arguments or environment variables.")

    async def scrape_blog_content(self, url: str) -> str:
        """Scrape blog content using Firecrawl SDK."""
        app = AsyncFirecrawlApp(api_key=self.firecrawl_api_key)
        response = await app.scrape_url(
            url=url,
            formats=['markdown'],
            only_main_content=True
        )
        return response

    def generate_audio(self, text: str) -> bytes:
        """Generate audio using ElevenLabs SDK."""
        elevenlabs = ElevenLabs(api_key=self.elevenlabs_api_key)
        audio_generator = elevenlabs.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        audio_bytes = b''.join(chunk for chunk in audio_generator)
        return audio_bytes

    async def generate_podcast(self, url: str) -> dict:
        """
        Scrape the blog, summarize it, and generate audio.
        Returns a dictionary containing audio data and metadata.
        """
        # Set Gemini API key for Agno
        os.environ["GOOGLE_API_KEY"] = self.gemini_api_key
        
        # Scrape blog content (async)
        blog_content = await self.scrape_blog_content(url)

        # Initialize the podcast generation agent
        blog_to_podcast_agent = Agent(
            name="Blog to Podcast Agent",
            agent_id="blog_to_podcast_agent",
            model=Gemini(id="gemini-1.5-flash"),
            description="You are an AI agent that creates engaging podcast summaries from blog content.",
            instructions=[
                "Given the blog content:",
                "1. Create a concise, engaging summary that is NO MORE than 2000 characters long",
                "2. Write in a natural, conversational tone that's perfect for podcast delivery",
                "3. DO NOT include any podcast-specific elements like 'Host:', 'Intro Music:', or 'Outro Music:'",
                "4. Focus on the main points and key insights from the blog",
                "5. Use clear transitions between topics",
                "6. End with a strong conclusion that summarizes the key takeaways",
                "7. Ensure the summary is within the 2000 character limit",
                "8. Format the text with proper punctuation and pauses for natural speech delivery",
            ],
            markdown=True,
            debug_mode=False,
        )

        # Generate the podcast script from the scraped content
        podcast_script: RunResponse = blog_to_podcast_agent.run(
            f"Convert this blog content to a podcast script:\n\n{blog_content}"
        )

        # Generate audio from the script
        audio_bytes = self.generate_audio(podcast_script.content)

        # Create metadata
        metadata = {
            "title": podcast_script.content[:80] + ("..." if len(podcast_script.content) > 80 else ""),
            "script": podcast_script.content,
            "timestamp": datetime.now().isoformat()
        }

        return {
            "audio_data": audio_bytes,
            "metadata": metadata
        } 