import { NextResponse } from "next/server";

const FASTAPI_BASE = `${process.env.BACKEND_BASE_URL}/api/py`;

// We use POST here because your React component sends a POST request
export async function POST(req) {
  try {
    const { chatId } = await req.json();

    // 1. Validate Request
    if (!chatId) {
      return NextResponse.json({ success: false, message: "Chat ID is required" });
    }

    // 2. Call your FastAPI Backend
    // Note: FastAPI expects a DELETE request at /thread/{thread_id}
    const fastApiResponse = await fetch(`${FASTAPI_BASE}/api/py/thread/${chatId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 3. Handle FastAPI Response
    if (!fastApiResponse.ok) {
      const errorData = await fastApiResponse.json();
      return NextResponse.json({ 
        success: false, 
        message: errorData.detail || "Failed to delete thread in backend" 
      });
    }

    // 4. Success
    return NextResponse.json({
      success: true,
      message: "Thread deleted successfully",
    });
    
  } catch (error) {
    console.error("Proxy Error:", error);
    return NextResponse.json({
      success: false,
      error: error.message,
    });
  }
}