"use client";
import React, { useState } from "react";
import Image from "next/image";
import { assets } from "@/assets/assets";
import { useAppContext } from "@/context/AppContext";
import toast from "react-hot-toast";
import axios from "axios";

const PromptBox = ({ isLoading, setIsLoading, threadId }) => {
  const [prompt, setPrompt] = useState("");
  
  // Feature Toggles State
  const [activeFeatures, setActiveFeatures] = useState({
    deepThink: false,
    search: false,
    agentic: false,
  });

  const { user, setMessages } = useAppContext();

  const toggleFeature = (feature) => {
    setActiveFeatures((prev) => ({
      ...prev,
      [feature]: !prev[feature],
    }));
  };

  const sendPrompt = async (e) => {
    if (e) e.preventDefault();
    
    if (!user) return toast.error("Login to send message");
    if (isLoading) return toast.error("Wait for response");
    if (!prompt.trim()) return;

    const promptCopy = prompt;
    setPrompt(""); 
    setIsLoading(true);

    try {
      // 1. Optimistic Update (Add user message instantly)
      setMessages(prev => [
        ...prev, 
        { role: "user", content: promptCopy }
      ]);

      // 2. FIX: URL Updated to match main.py prefix + router endpoint
      // main.py has prefix="/chat", router has "/send" -> "/chat/send"
      const { data } = await axios.post("http://localhost:8000/chat/send", {
        thread_id: threadId,
        message: promptCopy,
        features: activeFeatures, 
      });

      // 3. FIX: Handle the specific response format from Python
      // Your Python returns: { "reply": "...", "thread_id": "..." }
      if (data && data.reply) {
        setMessages(prev => [
          ...prev, 
          { role: "assistant", content: data.reply } // Use .reply, not .response
        ]);
      } else {
        // Fallback in case backend structure changes
        console.warn("Unexpected response format:", data);
      }

    } catch (error) {
      console.error("Send Error:", error);
      toast.error("Failed to send message");
      setPrompt(promptCopy); // Restore text on error
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form
      className="w-full max-w-3xl bg-[#2f2f33] p-4 rounded-3xl mt-4 transition-all shadow-lg border border-white/5"
    >
      <textarea
        className="outline-none w-full resize-none overflow-hidden break-words bg-transparent text-white placeholder-white/40 px-2"
        rows={2}
        placeholder={activeFeatures.agentic ? "Ask Agent to perform a task..." : "Message AI..."}
        onChange={(e) => setPrompt(e.target.value)}
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
          
          {/* DeepThink Toggle */}
          <div
            onClick={() => toggleFeature("deepThink")}
            className={`flex items-center gap-2 text-xs border px-3 py-1.5 rounded-full cursor-pointer transition-all select-none
            ${
              activeFeatures.deepThink
                ? "bg-blue-500/20 border-blue-500 text-blue-200"
                : "border-gray-500/40 text-gray-400 hover:bg-gray-600/30"
            }`}
          >
            <Image 
                className={`h-4 w-4 ${activeFeatures.deepThink ? "" : "opacity-60"}`} 
                src={assets.deepthink_icon || assets.menu_icon} 
                alt="" 
            />
            Thinking
          </div>

          {/* Web Search Toggle */}
          <div
            onClick={() => toggleFeature("search")}
            className={`flex items-center gap-2 text-xs border px-3 py-1.5 rounded-full cursor-pointer transition-all select-none
            ${
              activeFeatures.search
                ? "bg-green-500/20 border-green-500 text-green-200"
                : "border-gray-500/40 text-gray-400 hover:bg-gray-600/30"
            }`}
          >
            <Image 
                className={`h-4 w-4 ${activeFeatures.search ? "" : "opacity-60"}`} 
                src={assets.search_icon || assets.menu_icon} 
                alt="" 
            />
            Search
          </div>

          {/* Agentic Mode Toggle */}
          <div
            onClick={() => toggleFeature("agentic")}
            className={`flex items-center gap-2 text-xs border px-3 py-1.5 rounded-full cursor-pointer transition-all select-none
            ${
              activeFeatures.agentic
                ? "bg-purple-500/20 border-purple-500 text-purple-200"
                : "border-gray-500/40 text-gray-400 hover:bg-gray-600/30"
            }`}
          >
             <span className="text-lg leading-3">⚡</span> 
            Agentic Mode
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <div className="p-2 hover:bg-white/10 rounded-full cursor-pointer transition">
            <Image className="w-5 opacity-70" src={assets.pin_icon || assets.menu_icon} alt="" />
          </div>

          <button
            onClick={sendPrompt}
            type="submit"
            disabled={isLoading || !prompt}
            className={`${
              prompt ? "bg-blue-600 shadow-blue-500/20 shadow-md" : "bg-[#55555c]"
            } h-10 w-10 flex items-center justify-center rounded-full cursor-pointer transition-all duration-200`}
          >
            {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
                <Image
                className={`h-5 w-5 transition-transform ${prompt ? "-rotate-0" : ""}`}
                src={prompt ? assets.send_icon : assets.send_icon}
                alt=""
                />
            )}
          </button>
        </div>
      </div>
    </form>
  );
};

export default PromptBox;