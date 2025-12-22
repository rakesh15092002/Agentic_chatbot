import { getAuth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const FASTAPI_BASE = "http://127.0.0.1:8000";

export async function GET(req) {
  try {
    const { userId } = getAuth(req);
    if (!userId) return NextResponse.json({ success: false }, { status: 401 });

    const { searchParams } = new URL(req.url);
    const chatId = searchParams.get("chatId");

    let data;

    // A. Get Single Chat Messages
    if (chatId) {
      // Note: Adjust path if your backend is /thread/thread/...
      const res = await fetch(`${FASTAPI_BASE}/thread/thread/${chatId}/messages`, { cache: 'no-store' });
      const threadData = await res.json();
      
      data = {
        _id: chatId,
        messages: threadData.messages.map(m => ({
          role: m.role,
          content: m.content
        }))
      };

    // B. Get All Chats (Sidebar)
    } else {
      // Note: Adjust path if needed
      const res = await fetch(`${FASTAPI_BASE}/thread/all`, { cache: 'no-store' });
      const threads = await res.json();

      data = threads.map(t => ({
        _id: t.id,    // Map id -> _id for Frontend
        name: t.name,
        userId: userId
      }));
    }

    return NextResponse.json({ success: true, data });

  } catch (error) {
    return NextResponse.json({ success: false, error: error.message });
  }
}