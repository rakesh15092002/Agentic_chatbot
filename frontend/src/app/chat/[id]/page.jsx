// src/app/chat/[id]/page.jsx
"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { assets } from "@/assets/assets";
import Sidebar from '@/components/Sidebar';
import PromptBox from '@/components/PromptBox';
import Message from '@/components/Message';
import { useAppContext } from "@/context/AppContext";

export default function ChatPage({ params }) {
  // NEXT.JS 15 FIX: Unwrap params
  const { id } = React.use(params); 

  const [expand, setExpand] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false); 

  const { selectedChat, chats, setSelectedChat, fetchMessages, messages, isMessagesLoading } = useAppContext();
  const containerRef = useRef(null);

  useEffect(() => {
    if (chats.length > 0) {
      const currentChat = chats.find(c => c._id === id);
      if (currentChat) setSelectedChat(currentChat);
    }
    if (id) {
      fetchMessages(id);
    }
  }, [id, chats, setSelectedChat]); 

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({ top: containerRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isMessagesLoading]);

  return (
    <div className="flex h-screen">
      <Sidebar expand={expand} setExpand={setExpand} />
      <div className="flex-1 flex flex-col items-center justify-center px-4 pb-8 bg-[#292a2d] text-white relative">
        {selectedChat?.name && (
          <p className="fixed top-8 border border-transparent hover:border-gray-500/50 py-1 px-2 rounded-lg font-semibold z-10 bg-[#292a2d]">
            {selectedChat.name}
          </p>
        )}

        <div className="relative flex flex-col items-center justify-start w-full mt-20 max-h-screen overflow-y-auto" ref={containerRef}>
          {isMessagesLoading && messages.length === 0 && (
             <p className="text-gray-400 mt-10">Loading conversation...</p>
          )}
          {messages.map((msg, index) => (
            <Message key={index} role={msg.role} content={msg.content} />
          ))}
          {isGenerating && (
            <div className="flex gap-4 max-w-3xl w-full py-3">
              <Image className="h-9 w-9 p-1 border border-white/15 rounded-full" src={assets.logo_icon} alt="logo" />
              <div className="loader flex justify-center items-center gap-1">
                <div className="w-1 h-1 rounded-full bg-white animate-bounce"></div>
                <div className="w-1 h-1 rounded-full bg-white animate-bounce"></div>
                <div className="w-1 h-1 rounded-full bg-white animate-bounce"></div>
              </div>
            </div>
          )}
        </div>

        <PromptBox 
            isLoading={isGenerating} 
            setIsLoading={setIsGenerating} 
            threadId={id} 
        />
        <p className="text-xs absolute bottom-1 text-gray-500">AI-generated, for reference only</p>
      </div>
    </div>
  );
}