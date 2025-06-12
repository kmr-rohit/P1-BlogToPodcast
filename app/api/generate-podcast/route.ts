import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { url } = body;

    // Call your FastAPI endpoint
    const response = await axios.post('http://127.0.0.1:8000/generate-podcast', {
      url
    });

    return NextResponse.json(response.data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to generate podcast' },
      { status: 500 }
    );
  }
}