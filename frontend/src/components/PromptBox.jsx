"use client";
import React, { useState, useRef } from "react";
import Image from "next/image";
import { assets } from "@/assets/assets";
import { useAppContext } from "@/context/AppContext";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL
const FASTAPI_BASE = `${process.env.NEXT_PUBLIC_BACKEND_BASE_URL}/api/py`;

const PromptBox = ({ isLoading, setIsLoading, threadId, setMessages }) => {
  const [prompt, setPrompt] = useState("");
  const textareaRef = useRef(null);
  const router = useRouter();

  const [activeFeatures, setActiveFeatures] = useState({
    deepThink: false,
    search: false,
    agentic: false,
  });

  const { user, createNewChat } = useAppContext();

  const toggleFeature = (feature) => {
    setActiveFeatures((prev) => ({
      ...prev,
      [feature]: !prev[feature],
    }));
  };

  const handleInput = (e) => {
    setPrompt(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const sendPrompt = async (e) => {
    if (e) e.preventDefault();

    if (!user) return toast.error("Login to send message");
    if (isLoading) return toast.error("Wait for response");
    if (!prompt.trim()) return;

    if (typeof setMessages !== "function") {
      return toast.error("Internal Error: UI State update failed.");
    }

    const promptCopy = prompt;
    
    // 1. Clear UI immediately
    setPrompt("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    
    // 2. START LOADING
    setIsLoading(true);

    // Optimistically Add User Message
    setMessages(prev => [...prev, { role: "user", content: promptCopy }]);
    // Add Placeholder for AI response
    setMessages(prev => [...prev, { role: "assistant", content: "" }]);

    try {
      let activeThreadId = threadId;
      let isNewChat = false;

      // --- LOGIC: Handle New Chat Creation ---
      // If no threadId is passed, we are on the Home page.
      if (!activeThreadId) {
        // Create the chat in DB first, but pass 'false' to prevent auto-redirect
        const newChat = await createNewChat(false); 
        if (!newChat) throw new Error("Failed to create chat");
        activeThreadId = newChat._id;
        isNewChat = true;
      }

      // --- FETCH STREAM ---
      const response = await fetch(`${FASTAPI_BASE}/chat/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: activeThreadId,
          message: promptCopy,
          features: activeFeatures 
        }),
      });

      if (!response.ok) throw new Error(`Server Error: ${response.statusText}`);
      if (!response.body) throw new Error("No response body received");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let aiResponse = "";

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          aiResponse += chunk;
          
          setMessages(prev => {
             const newMessages = [...prev];
             const lastMsgIndex = newMessages.length - 1;
             if (lastMsgIndex >= 0) {
                 newMessages[lastMsgIndex] = { ...newMessages[lastMsgIndex], content: aiResponse };
             }
             return newMessages;
          });
        }
      }

      // --- REDIRECT IF NEW CHAT ---
      // We redirect AFTER the message has started/finished so the user sees the flow
      if (isNewChat) {
         router.push(`/chat/${activeThreadId}`);
      }

    } catch (error) {
      console.error("Stream Error:", error);
      toast.error("Failed to get response");
      setPrompt(promptCopy); // Restore text if failed
      setMessages(prev => prev.slice(0, -1)); // Remove empty bubble
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className="w-full max-w-3xl bg-[#2f2f33] p-4 rounded-3xl transition-all shadow-xl border border-white/5">
      <textarea
        ref={textareaRef}
        disabled={isLoading}
        className={`outline-none w-full resize-none bg-transparent text-white placeholder-white/40 px-2 text-base custom-scrollbar overflow-y-auto max-h-52 min-h-[48px] 
        ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
        rows={1}
        placeholder={
            isLoading 
            ? (activeFeatures.search ? "Searching the web..." : "AI is thinking...") 
            : (activeFeatures.agentic ? "Ask Agent to perform a task..." : "Message AI...")
        }
        onChange={handleInput}
        value={prompt}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendPrompt(e);
          }
        }}
      />

      <div className="flex items-center justify-between text-sm mt-3">
        {/* Feature Toggles */}
        <div className="flex items-center gap-2 flex-wrap">
          <div
            onClick={() => toggleFeature("deepThink")}
            className={`flex items-center gap-2 text-xs border px-3 py-1.5 rounded-full cursor-pointer transition-all select-none
            ${activeFeatures.deepThink ? "bg-blue-500/20 border-blue-500 text-blue-200" : "border-gray-500/40 text-gray-400 hover:bg-gray-600/30"}`}
          >
            {assets.deepthink_icon && <Image className={`h-4 w-4 ${activeFeatures.deepThink ? "" : "opacity-60"}`} src={assets.deepthink_icon} alt="Think" />}
            Thinking
          </div>

          <div
            onClick={() => toggleFeature("search")}
            className={`flex items-center gap-2 text-xs border px-3 py-1.5 rounded-full cursor-pointer transition-all select-none
            ${activeFeatures.search ? "bg-green-500/20 border-green-500 text-green-200" : "border-gray-500/40 text-gray-400 hover:bg-gray-600/30"}`}
          >
             {assets.search_icon && <Image className={`h-4 w-4 ${activeFeatures.search ? "" : "opacity-60"}`} src={assets.search_icon} alt="Search" />}
            Search
          </div>

          <div
            onClick={() => toggleFeature("agentic")}
            className={`flex items-center gap-2 text-xs border px-3 py-1.5 rounded-full cursor-pointer transition-all select-none
            ${activeFeatures.agentic ? "bg-purple-500/20 border-purple-500 text-purple-200" : "border-gray-500/40 text-gray-400 hover:bg-gray-600/30"}`}
          >
             <span className="text-lg leading-3">⚡</span> 
            Agentic Mode
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={sendPrompt}
            type="submit"
            disabled={isLoading || !prompt}
            className={`${prompt ? "bg-blue-600 shadow-blue-500/20 shadow-md" : "bg-[#55555c]"} h-10 w-10 flex items-center justify-center rounded-full cursor-pointer transition-all duration-200`}
          >
            {isLoading ? (
                // DYNAMIC LOADER
                <div className={`w-5 h-5 border-2 border-t-transparent rounded-full animate-spin 
                    ${activeFeatures.search ? "border-green-400" : "border-white/50"}`}>
                </div>
            ) : (
                assets.arrow_icon && <Image className={`h-5 w-5 transition-transform ${prompt ? "-rotate-0" : ""}`} src={assets.arrow_icon} alt="Send" />
            )}
          </button>
        </div>
      </div>
    </form>
  );
};

export default PromptBox;