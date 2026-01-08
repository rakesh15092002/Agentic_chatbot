"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { assets } from "@/assets/assets";
import Sidebar from '@/components/Sidebar';
import PromptBox from '@/components/PromptBox';
import Message from '@/components/Message';
import { useAppContext } from "@/context/AppContext";

export default function ChatPage({ params }) {
  // Unwrap params using React.use()
  const { id } = React.use(params); 

  const [expand, setExpand] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false); 
   
  const { 
    selectedChat, 
    chats, 
    setSelectedChat, 
    fetchMessages, 
    messages: contextMessages, 
    isMessagesLoading,
    // ✅ 1. Get the new helper function from Context
    refreshTitleAfterDelay 
  } = useAppContext();
  
  // Local state for immediate UI updates during streaming
  const [messages, setMessages] = useState([]);

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

  // Sync local state when context messages finish loading
  useEffect(() => {
    if (contextMessages) {
      setMessages(contextMessages);
    }
  }, [contextMessages]);

  // ✅ 2. NEW EFFECT: Trigger Sidebar Refresh on First Message
  // When the user sends the very first message, this runs and updates the title after 2.5s
  useEffect(() => {
    if (messages.length === 1 && messages[0].role === "user") {
        refreshTitleAfterDelay();
    }
  }, [messages, refreshTitleAfterDelay]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({ top: containerRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isMessagesLoading]);

  return (
    <div className="flex h-screen overflow-hidden"> 
      <Sidebar expand={expand} setExpand={setExpand} />
      
      <div className="flex-1 flex flex-col items-center justify-center bg-[#292a2d] text-white relative">
        
        {/* --- MOBILE TOP BAR --- */}
        <div className="md:hidden w-full flex items-center justify-between py-4 px-4 shrink-0 z-20 absolute top-0 left-0 bg-[#292a2d]">
            <Image
                onClick={() => setExpand(!expand)}
                className="w-6 cursor-pointer"
                src={assets.menu_icon}
                alt="Menu"
            />
            <Image className="opacity-70 w-6" src={assets.chat_icon} alt="Chat" />
        </div>

        {/* --- CHAT NAME PILL --- */}
        {/* ✅ 3. Updated to show Title OR Name (matches Sidebar logic) */}
        {(selectedChat?.title || selectedChat?.name) && (
          <p className="hidden md:block fixed top-6 border border-white/10 py-1.5 px-4 rounded-full font-medium text-sm z-20 bg-[#292a2d] shadow-md">
            {selectedChat.title || selectedChat.name}
          </p>
        )}

        {/* --- SCROLLABLE CONTAINER --- */}
        <div className="flex-1 w-full overflow-y-auto custom-scrollbar" ref={containerRef}>
            
            <div className="w-full max-w-3xl mx-auto flex flex-col gap-4 px-4 pt-24 pb-52">
                
                {isMessagesLoading && messages.length === 0 && (
                   <div className="flex flex-col items-center justify-center h-40 gap-2">
                       <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                       <p className="text-gray-400 text-sm">Loading conversation...</p>
                   </div>
                )}
                
                {messages.map((msg, index) => (
                    <Message 
                        key={index} 
                        role={msg.role} 
                        content={msg.content}
                        // Only show loader for the last message if we are generating
                        isGenerating={isGenerating && index === messages.length - 1}
                    />
                ))}
            </div>
        </div>

        {/* --- PROMPT BOX AREA --- */}
        <div className="w-full absolute bottom-0 bg-gradient-to-t from-[#292a2d] via-[#292a2d] to-transparent pt-10 pb-6 px-4 flex flex-col items-center">
             <PromptBox 
                isLoading={isGenerating} 
                setIsLoading={setIsGenerating} 
                threadId={id}
                setMessages={setMessages}
             />
             <p className="text-xs text-gray-500 mt-2">AI-generated, for reference only</p>
        </div>
      </div>
    </div>
  );
}