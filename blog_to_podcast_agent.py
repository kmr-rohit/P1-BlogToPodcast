import os
from uuid import uuid4
import asyncio
from firecrawl import AsyncFirecrawlApp
from agno.agent import Agent
from agno.models.google import Gemini
from agno.agent import Agent, RunResponse
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import streamlit as st

# Default API Keys (replace these with your actual keys)
DEFAULT_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD2NfBcDJdmMzKDCtvHuWnODy2Z5wa4NXA")
DEFAULT_ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_e25fde28d02dde371e328439aabd6d0ab8fd31b8f2b84be5")
DEFAULT_FIRECRAWL_KEY = os.getenv("FIRECRAWL_API_KEY", "fc-5317e7da35d84992b4375b69bcdd4c66")

# Streamlit Page Setup
st.set_page_config(page_title="📰 ➡️ 🎙️ Blog to Podcast Agent", page_icon="��️")
st.title("📰 ➡️ 🎙️ Blog to Podcast Agent")

# Sidebar: API Keys
st.sidebar.header("🔑 API Keys")
gemini_api_key = st.sidebar.text_input(
    "Gemini API Key", 
    value=DEFAULT_GEMINI_KEY,
    type="password",
    help="Enter your Gemini API key or use the default from environment variables"
)
elevenlabs_api_key = st.sidebar.text_input(
    "ElevenLabs API Key", 
    value=DEFAULT_ELEVENLABS_KEY,
    type="password",
    help="Enter your ElevenLabs API key or use the default from environment variables"
)
firecrawl_api_key = st.sidebar.text_input(
    "Firecrawl API Key", 
    value=DEFAULT_FIRECRAWL_KEY,
    type="password",
    help="Enter your Firecrawl API key or use the default from environment variables"
)

# Check if all keys are provided and not using default placeholders
keys_provided = all([
    gemini_api_key ,
    elevenlabs_api_key ,
    firecrawl_api_key 
])

# Input: Blog URL
url = st.text_input("Enter the Blog URL:", "")

# Button: Generate Podcast
generate_button = st.button("🎙️ Generate Podcast", disabled=not keys_provided)

if not keys_provided:
    st.warning("Please enter all required API keys to enable podcast generation.")

async def scrape_blog_content(url: str, api_key: str) -> str:
    """Scrape blog content using Firecrawl SDK."""
    try:
        app = AsyncFirecrawlApp(api_key=api_key)
        response = await app.scrape_url(
            url=url,
            formats=['markdown'],
            only_main_content=True
        )
        return response
    except Exception as e:
        st.error(f"Error scraping blog: {e}")
        raise

def generate_audio(text: str, api_key: str) -> bytes:
    """Generate audio using ElevenLabs SDK."""
    try:
        elevenlabs = ElevenLabs(api_key=api_key)
        audio_generator = elevenlabs.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        # Convert generator to bytes
        audio_bytes = b''.join(chunk for chunk in audio_generator)
        return audio_bytes
    except Exception as e:
        st.error(f"Error generating audio: {e}")
        raise

if generate_button:
    if url.strip() == "":
        st.warning("Please enter a blog URL first.")
    else:
        # Set API keys as environment variables for Agno
        os.environ["GOOGLE_API_KEY"] = gemini_api_key

        with st.spinner("Processing... Scraping blog, summarizing and generating podcast 🎶"):
            try:
                # First, scrape the blog content
                blog_content = asyncio.run(scrape_blog_content(url, firecrawl_api_key))
                
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

                # Generate the podcast script from the scraped content
                podcast_script: RunResponse = blog_to_podcast_agent.run(
                    f"Convert this blog content to a podcast script:\n\n{blog_content}"
                )

                # Generate audio from the script
                audio_bytes = generate_audio(podcast_script.content, elevenlabs_api_key)

                # Save the audio file
                save_dir = "audio_generations"
                os.makedirs(save_dir, exist_ok=True)
                filename = f"{save_dir}/podcast_{uuid4()}.mp3"
                
                with open(filename, "wb") as f:
                    f.write(audio_bytes)

                st.success("Podcast generated successfully! 🎧")
                st.audio(audio_bytes, format="audio/mp3")

                st.download_button(
                    label="Download Podcast",
                    data=audio_bytes,
                    file_name="generated_podcast.mp3",
                    mime="audio/mp3"
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.error(f"Error details: {str(e)}")