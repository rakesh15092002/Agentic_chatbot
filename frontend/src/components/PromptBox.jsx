"use client";
import React, { useState, useRef } from "react";
import Image from "next/image";
import { assets } from "@/assets/assets";
import { useAppContext } from "@/context/AppContext";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

const PromptBox = ({ isLoading, setIsLoading, threadId, setMessages }) => {
  const [prompt, setPrompt] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const router = useRouter();

  const [activeFeatures, setActiveFeatures] = useState({
    deepThink: false,
    search: false,
    agentic: false,
  });

  const { user, createNewChat, FASTAPI_BASE } = useAppContext();

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

  // Fetch messages to refresh chat after upload - FIXED VERSION
  const fetchMessages = async (activeThreadId) => {
    try {
      const response = await fetch(`${FASTAPI_BASE}/thread/${activeThreadId}/messages`);
      if (response.ok) {
        const data = await response.json();
        
        // Handle different response formats
        let messagesArray = [];
        
        if (Array.isArray(data)) {
          // If data is already an array
          messagesArray = data;
        } else if (data && Array.isArray(data.messages)) {
          // If data has a messages property that's an array
          messagesArray = data.messages;
        } else if (data && typeof data === 'object') {
          // If it's an object, try to extract messages
          messagesArray = Object.values(data).filter(item => 
            item && typeof item === 'object' && item.role && item.content
          );
        }
        
        // Only update if we have valid messages
        if (messagesArray.length >= 0) {
          setMessages(messagesArray);
        }
      }
    } catch (error) {
      console.error("Error fetching messages:", error);
      // Don't clear messages on error, keep existing ones
    }
  };

  // Handle file upload with confirmation
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!user) return toast.error("Login to upload files");

    // Clear input so same file can be selected again if needed
    if (fileInputRef.current) fileInputRef.current.value = "";

    setIsUploading(true);
    const loadingToast = toast.loading("Uploading PDF to Knowledge Base...");

    try {
      let activeThreadId = threadId;

      // Agar chat ID nahi hai, toh nayi chat banayein
      if (!activeThreadId) {
        const newChat = await createNewChat(false);
        if (!newChat) throw new Error("Failed to create chat");
        activeThreadId = newChat._id;
        window.history.pushState({}, '', `/chat/${activeThreadId}`);
      }

      const formData = new FormData();
      formData.append("files", file); 
      formData.append("thread_id", activeThreadId);

      const response = await fetch(`${FASTAPI_BASE}/documents/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText || "Backend Upload Failed");
      }

      const result = await response.json();
      toast.success(`✅ ${file.name} uploaded successfully!`, { id: loadingToast });
      
      // Refresh messages to show confirmation
      await fetchMessages(activeThreadId);

    } catch (error) {
      console.error("Upload Error:", error);
      toast.error(`Upload Failed: ${error.message}`, { id: loadingToast });
    } finally {
      setIsUploading(false);
    }
  };

  const sendPrompt = async (e) => {
    if (e) e.preventDefault();
    if (!user) return toast.error("Login to send message");
    if (isLoading) return toast.error("Wait for response");
    if (!prompt.trim()) return;

    if (typeof setMessages !== "function") return toast.error("Internal Error: UI State update failed.");

    const promptCopy = prompt;
    setPrompt("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsLoading(true);

    setMessages((prev) => [...prev, { role: "user", content: promptCopy }]);
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      let activeThreadId = threadId;
      let isNewChat = false;

      if (!activeThreadId) {
        const newChat = await createNewChat(false);
        if (!newChat) throw new Error("Failed to create chat");
        activeThreadId = newChat._id;
        isNewChat = true;
      }

      const response = await fetch(`${FASTAPI_BASE}/chat/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: activeThreadId,
          message: promptCopy,
          features: activeFeatures,
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
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMsgIndex = newMessages.length - 1;
            if (lastMsgIndex >= 0) {
              newMessages[lastMsgIndex] = { ...newMessages[lastMsgIndex], content: aiResponse };
            }
            return newMessages;
          });
        }
      }

      if (isNewChat) router.push(`/chat/${activeThreadId}`);

    } catch (error) {
      console.error("Stream Error:", error);
      toast.error("Failed to get response");
      setPrompt(promptCopy);
      setMessages((prev) => prev.slice(0, -1));
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
        placeholder={isLoading ? "AI is thinking..." : "Message AI..."}
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
        
        {/* --- LEFT SIDE: Plus Button + Toggles --- */}
        <div className="flex items-center gap-4">
          
          {/* 1. UPLOAD BUTTON */}
          <div className="flex items-center">
             <input
               type="file"
               ref={fileInputRef}
               onChange={handleFileUpload}
               className="hidden"
               accept=".pdf,.txt,.docx" 
             />
             <button
               type="button" 
               onClick={() => fileInputRef.current?.click()}
               disabled={isUploading || isLoading}
               className={`p-2 rounded-full transition-all duration-200 flex items-center justify-center border border-white/10
                 ${isUploading || isLoading 
                   ? "text-gray-500 cursor-not-allowed bg-transparent" 
                   : "text-gray-400 hover:text-white hover:bg-white/10 active:scale-95 bg-[#3a3a40]"
                 }`}
               title="Upload File"
             >
                {isUploading ? (
                    <span className="block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4">
                       <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                    </svg>
                )}
             </button>
          </div>

          {/* 2. Feature Toggles */}
          <div className="flex items-center gap-2 flex-wrap">
            <div
              onClick={() => toggleFeature("deepThink")}
              className={`flex items-center gap-2 text-xs border px-3 py-1.5 rounded-full cursor-pointer transition-all select-none
              ${
                activeFeatures.deepThink
                  ? "bg-blue-500/20 border-blue-500 text-blue-200"
                  : "border-gray-500/40 text-gray-400 hover:bg-gray-600/30"
              }`}
            >
              {assets.deepthink_icon && (
                <Image
                  className={`h-4 w-4 ${activeFeatures.deepThink ? "" : "opacity-60"}`}
                  src={assets.deepthink_icon}
                  alt="Think"
                />
              )}
              Thinking
            </div>

            <div
              onClick={() => toggleFeature("search")}
              className={`flex items-center gap-2 text-xs border px-3 py-1.5 rounded-full cursor-pointer transition-all select-none
              ${
                activeFeatures.search
                  ? "bg-green-500/20 border-green-500 text-green-200"
                  : "border-gray-500/40 text-gray-400 hover:bg-gray-600/30"
              }`}
            >
              {assets.search_icon && (
                <Image
                  className={`h-4 w-4 ${activeFeatures.search ? "" : "opacity-60"}`}
                  src={assets.search_icon}
                  alt="Search"
                />
              )}
              Search
            </div>

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
              Agentic
            </div>
          </div>
        </div>

        {/* --- RIGHT SIDE: Send Button --- */}
        <div className="flex items-center gap-3">
          <button
            onClick={sendPrompt}
            type="submit"
            disabled={isLoading || !prompt}
            className={`${
              prompt
                ? "bg-blue-600 shadow-blue-500/20 shadow-md"
                : "bg-[#55555c]"
            } h-10 w-10 flex items-center justify-center rounded-full cursor-pointer transition-all duration-200 active:scale-95`}
          >
            {isLoading ? (
              <div className={`w-5 h-5 border-2 border-t-transparent rounded-full animate-spin 
                ${activeFeatures.search ? "border-green-400" : "border-white/50"}`}></div>
            ) : (
              assets.arrow_icon && (
                <Image
                  className={`h-5 w-5 transition-transform ${prompt ? "-rotate-0" : ""}`}
                  src={assets.arrow_icon}
                  alt="Send"
                />
              )
            )}
          </button>
        </div>
      </div>
    </form>
  );
};

export default PromptBox;