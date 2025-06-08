import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server URL
BASE_URL = "http://localhost:8000"

def test_generate_podcast():
    """Test podcast generation endpoint."""
    print("\nTesting podcast generation...")
    
    # Test URL (using a sample blog post)
    test_url = "https://news.convex.dev/how-convex-took-down-t3-chat-june-1-2025-postmortem/"
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate-podcast",
            json={"url": test_url}
        )
        response.raise_for_status()
        data = response.json()
        print("✅ Podcast generation successful!")
        print(f"Generated audio URL: {data['audio_url']}")
        print(f"Filename: {data['filename']}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error generating podcast: {e}")
        return None

def test_get_audio(filename):
    """Test audio file retrieval."""
    print("\nTesting audio file retrieval...")
    
    try:
        response = requests.get(f"{BASE_URL}/audio/{filename}")
        response.raise_for_status()
        print("✅ Audio file retrieved successfully!")
        
        # Save the audio file for verification
        with open(f"test_audio_{filename}", "wb") as f:
            f.write(response.content)
        print(f"Audio file saved as: test_audio_{filename}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving audio file: {e}")
        return False

def test_recent_podcasts():
    """Test recent podcasts endpoint."""
    print("\nTesting recent podcasts endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/recent-podcasts")
        response.raise_for_status()
        data = response.json()
        print("✅ Recent podcasts retrieved successfully!")
        print(f"Number of recent podcasts: {len(data)}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving recent podcasts: {e}")
        return None

def run_all_tests():
    """Run all tests."""
    print("Starting API tests...")
    
    # Test podcast generation
    podcast_data = test_generate_podcast()
    if not podcast_data:
        return
    
    # Wait for a moment to ensure file is saved
    time.sleep(2)
    
    # Test audio file retrieval
    test_get_audio(podcast_data['filename'])
    
    # Test recent podcasts
    test_recent_podcasts()

if __name__ == "__main__":
    run_all_tests() 