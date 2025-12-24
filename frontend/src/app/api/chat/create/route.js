import { auth } from "@clerk/nextjs/server"; // Use 'auth', not 'getAuth'
import { NextResponse } from "next/server";

// 1. FIX: Use the standard URL (Single 'thread')
const FASTAPI_URL = `${process.env.BACKEND_BASE_URL}/api/py/thread/create`; 

export async function POST(req) {
  try {
    // 2. FIX: Use auth() for App Router
    const { userId } = await auth();
    
    if (!userId) {
      return NextResponse.json({ success: false, message: "Unauthorized" }, { status: 401 });
    }

    console.log(`Connecting to backend: ${FASTAPI_URL}...`);

    // 3. Send request to Python
    const response = await fetch(`${FASTAPI_URL}?name=New%20Chat`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json" 
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend Error Response:", errorText);
      throw new Error(`Backend failed with status ${response.status}: ${errorText}`);
    }

    const backendData = await response.json(); 
    
    // 4. Return mapped data
    return NextResponse.json({ 
      success: true, 
      data: { 
          _id: backendData.thread_id, 
          chatId: backendData.thread_id,
          name: backendData.name,
          messages: [],
          updatedAt: new Date().toISOString() // Add date for sorting
      }
    });

  } catch (error) {
    console.error("Create Chat Error:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}