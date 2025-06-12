import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET(
  request: Request,
  { params }: { params: { filename: string } }
) {
  try {
    const { filename } = params;
    
    // Call your FastAPI endpoint
    const response = await axios.get(`http://localhost:8000/audio/${filename}`, {
      responseType: 'arraybuffer'
    });

    // Return the audio file with proper headers
    return new NextResponse(response.data, {
      headers: {
        'Content-Type': 'audio/mp3',
        'Content-Disposition': `attachment; filename="${filename}"`
      }
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch audio file' },
      { status: 500 }
    );
  }
}