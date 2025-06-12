 'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface Podcast {
  filename: string;
  generated_at: string;
  url: string;
}

export default function HomePage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [recentPodcasts, setRecentPodcasts] = useState<Podcast[]>([]);

  useEffect(() => {
    fetchRecentPodcasts();
  }, []);

  const fetchRecentPodcasts = async () => {
    try {
      const response = await axios.get('/api/recent-podcasts');
      setRecentPodcasts(response.data);
    } catch (error) {
      console.error('Failed to fetch recent podcasts:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/generate-podcast', { url });
      await fetchRecentPodcasts();
      setUrl('');
    } catch (error: any) {
      setError(error.response?.data?.error || 'Failed to generate podcast');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Blog to Podcast Converter</h1>
        
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-4">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter blog URL"
              className="flex-1 p-2 border rounded"
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-blue-300"
            >
              {loading ? 'Generating...' : 'Generate Podcast'}
            </button>
          </div>
          {error && <p className="text-red-500 mt-2">{error}</p>}
        </form>

        <div>
          <h2 className="text-2xl font-bold mb-4">Recent Podcasts</h2>
          <div className="space-y-4">
            {recentPodcasts.map((podcast) => (
              <div key={podcast.filename} className="p-4 border rounded">
                <p className="font-medium">{podcast.url}</p>
                <p className="text-sm text-gray-500">
                  Generated: {new Date(podcast.generated_at).toLocaleString()}
                </p>
                <audio
                  controls
                  className="mt-2 w-full"
                  src={`/api/audio/${podcast.filename}`}
                >
                  Your browser does not support the audio element.
                </audio>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}