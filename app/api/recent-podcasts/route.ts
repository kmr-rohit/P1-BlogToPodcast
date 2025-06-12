import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET() {
  try {
    // Call your FastAPI endpoint
    const response = await axios.get('http://localhost:8000/recent-podcasts');
    return NextResponse.json(response.data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch recent podcasts' },
      { status: 500 }
    );
  }
}