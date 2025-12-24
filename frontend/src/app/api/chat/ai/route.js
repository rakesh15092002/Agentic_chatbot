import { getAuth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const FASTAPI_BASE = `${process.env.BACKEND_BASE_URL}/api/py`;

export async function POST(req) {
  try {
    const { userId } = getAuth(req);
    if (!userId) return NextResponse.json({ success: false }, { status: 401 });

    const { chatId, prompt } = await req.json();

    // 1. Call FastAPI Chat Endpoint
    // Note: Adjust '/chat/send' if your python route prefix is different
    const response = await fetch(`${FASTAPI_BASE}/chat/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: chatId, // Send the ID the backend gave us
        message: prompt
      }),
    });

    if (!response.ok) throw new Error("FastAPI Chat Error");

    const data = await response.json();
    // Python returns: { "reply": "...", "thread_id": "..." }

    // 2. Format for Frontend
    return NextResponse.json({
      success: true,
      data: {
          role: "assistant",
          content: data.reply, 
          timestamp: Date.now()
      },
      chatId: data.thread_id 
    });

  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}