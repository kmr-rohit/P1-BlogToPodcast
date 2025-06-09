from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from datetime import datetime
import json
from typing import List, Optional
from blog_to_podcast import BlogToPodcastAgent
from dotenv import load_dotenv
import logging
from base64 import b64encode

app = FastAPI(title="Blog to Podcast API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the agent with environment variables and error handling
def get_agent():
    gemini_key = os.getenv("GEMINI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    
    if not all([gemini_key, elevenlabs_key, firecrawl_key]):
        missing = []
        if not gemini_key: missing.append("GEMINI_API_KEY")
        if not elevenlabs_key: missing.append("ELEVENLABS_API_KEY")
        if not firecrawl_key: missing.append("FIRECRAWL_API_KEY")
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return BlogToPodcastAgent(
        gemini_api_key=gemini_key,
        elevenlabs_api_key=elevenlabs_key,
        firecrawl_api_key=firecrawl_key
    )

class PodcastRequest(BaseModel):
    url: str

class PodcastResponse(BaseModel):
    audio_data: str  # Base64 encoded audio data
    metadata: dict

class RecentPodcast(BaseModel):
    filename: str
    title: str
    created_at: str
    audio_url: str

@app.get("/")
async def root():
    return {"message": "Blog to Podcast API", "status": "healthy"}

@app.get("/health")
async def health_check():
    try:
        # Check if environment variables are set
        agent = get_agent()
        return {"status": "healthy", "message": "All services ready"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/generate-podcast", response_model=PodcastResponse)
async def generate_podcast(request: PodcastRequest):
    logger.info(f"Received request to generate podcast for URL: {request.url}")
    
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    try:
        # Initialize agent
        agent = get_agent()
        
        # Generate podcast
        result = await agent.generate_podcast(request.url)
        
        if not result:
            logger.error("Failed to generate podcast: result is None")
            raise HTTPException(status_code=500, detail="Failed to generate podcast")
        
        # Convert audio bytes to base64
        audio_base64 = b64encode(result["audio_data"]).decode('utf-8')
        
        logger.info("Podcast generated successfully!")
        
        return {
            "audio_data": audio_base64,
            "metadata": result["metadata"]
        }
    except ValueError as ve:
        logger.error(f"Configuration error: {ve}")
        raise HTTPException(status_code=500, detail=f"Server configuration error: {ve}")
    except Exception as e:
        logger.exception(f"Exception during podcast generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate podcast: {str(e)}")

@app.get("/recent-podcasts", response_model=List[RecentPodcast])
async def get_recent_podcasts():
    """
    Note: This endpoint won't work on Vercel since it relies on persistent file storage.
    Vercel is serverless and doesn't have persistent file system.
    Consider using cloud storage (AWS S3, Google Cloud Storage) or a database instead.
    """
    logger.warning("Recent podcasts endpoint called - this won't work on Vercel without external storage")
    
    # Return empty list for now - you'll need to implement cloud storage
    return []
    
    # Original code commented out since it won't work on Vercel:
    # try:
    #     audio_dir = "generated_audio"
    #     if not os.path.exists(audio_dir):
    #         logger.warning(f"Audio directory does not exist: {audio_dir}")
    #         return []
    #     
    #     podcasts = []
    #     for filename in os.listdir(audio_dir):
    #         if filename.endswith(".mp3"):
    #             file_path = os.path.join(audio_dir, filename)
    #             created_at = datetime.fromtimestamp(os.path.getctime(file_path))
    #             
    #             # Try to get title from metadata file
    #             title = filename.replace(".mp3", "")
    #             metadata_path = os.path.join(audio_dir, f"{filename}.json")
    #             if os.path.exists(metadata_path):
    #                 try:
    #                     with open(metadata_path, "r") as f:
    #                         metadata = json.load(f)
    #                         title = metadata.get("title", title)
    #                 except Exception as meta_e:
    #                     logger.warning(f"Failed to read metadata for {filename}: {meta_e}")
    #             
    #             podcasts.append({
    #                 "filename": filename,
    #                 "title": title,
    #                 "created_at": created_at.isoformat(),
    #                 "audio_url": f"/audio/{filename}"
    #             })
    #     
    #     # Sort by creation date, newest first
    #     podcasts.sort(key=lambda x: x["created_at"], reverse=True)
    #     logger.info(f"Returning {len(podcasts)} recent podcasts")
    #     return podcasts
    # except Exception as e:
    #     logger.exception(f"Exception during fetching recent podcasts: {e}")
    #     raise HTTPException(status_code=500, detail=str(e))

# Don't include this when deploying to Vercel
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)