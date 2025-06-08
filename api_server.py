import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from firecrawl import AsyncFirecrawlApp
from agno.agent import Agent
from agno.models.google import Gemini
from elevenlabs.client import ElevenLabs
import shutil
from datetime import datetime
import json
from typing import List
import glob

# Initialize FastAPI app
app = FastAPI(title="Blog to Podcast API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Next.js domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
AUDIO_DIR = "audio_generations"
MAX_FILES = 5
METADATA_FILE = "audio_metadata.json"

# Ensure audio directory exists
os.makedirs(AUDIO_DIR, exist_ok=True)

# Load API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Input model
class BlogURL(BaseModel):
    url: str

# Response model
class PodcastResponse(BaseModel):
    audio_url: str
    filename: str
    generated_at: str

def load_metadata() -> List[dict]:
    """Load metadata of generated audio files."""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_metadata(metadata: List[dict]):
    """Save metadata of generated audio files."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f)

def cleanup_old_files():
    """Keep only the last MAX_FILES audio files."""
    metadata = load_metadata()
    if len(metadata) > MAX_FILES:
        # Sort by generation time
        metadata.sort(key=lambda x: x['generated_at'], reverse=True)
        # Keep only the last MAX_FILES
        to_keep = metadata[:MAX_FILES]
        to_delete = metadata[MAX_FILES:]
        
        # Delete old files
        for file_info in to_delete:
            try:
                os.remove(os.path.join(AUDIO_DIR, file_info['filename']))
            except FileNotFoundError:
                pass
        
        # Update metadata
        save_metadata(to_keep)

async def scrape_blog_content(url: str) -> str:
    """Scrape blog content using Firecrawl SDK."""
    try:
        app = AsyncFirecrawlApp(api_key=FIRECRAWL_API_KEY)
        response = await app.scrape_url(
            url=url,
            formats=['markdown'],
            only_main_content=True
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error scraping blog: {str(e)}")

def generate_audio(text: str) -> bytes:
    """Generate audio using ElevenLabs SDK."""
    try:
        elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio_generator = elevenlabs.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        return b''.join(chunk for chunk in audio_generator)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating audio: {str(e)}")

@app.post("/generate-podcast", response_model=PodcastResponse)
async def generate_podcast(blog_url: BlogURL):
    """Generate podcast from blog URL."""
    try:
        # Scrape blog content
        blog_content = await scrape_blog_content(blog_url.url)
        
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
            debug_mode=True,
        )

        # Generate podcast script
        podcast_script = blog_to_podcast_agent.run(
            f"Convert this blog content to a podcast script:\n\n{blog_content}"
        )

        # Generate audio
        audio_bytes = generate_audio(podcast_script.content)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"podcast_{timestamp}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        # Save audio file
        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        # Update metadata
        metadata = load_metadata()
        metadata.append({
            "filename": filename,
            "generated_at": datetime.now().isoformat(),
            "url": blog_url.url
        })
        save_metadata(metadata)

        # Cleanup old files
        cleanup_old_files()

        # Return response
        return PodcastResponse(
            audio_url=f"/audio/{filename}",
            filename=filename,
            generated_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio file."""
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(filepath, media_type="audio/mp3")

@app.get("/recent-podcasts")
async def get_recent_podcasts():
    """Get list of recent podcasts."""
    metadata = load_metadata()
    return metadata

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 