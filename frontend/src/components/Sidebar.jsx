"use client";
import Image from "next/image";
import React, { useState } from "react";
import { assets } from "@/assets/assets";
import { useClerk, UserButton } from "@clerk/nextjs";
import { useAppContext } from "@/context/AppContext";
import ChatLabel from "@/components/ChatLabel";
import { useRouter } from "next/navigation";

const Sidebar = ({ expand, setExpand }) => {
  const { openSignIn } = useClerk();
  const { user, chats, setSelectedChat } = useAppContext();
  const [openMenu, setOpenMenu] = useState({ id: 0, open: false });
  const router = useRouter();

  const handleScroll = () => {
    if (openMenu.open) setOpenMenu({ id: 0, open: false });
  };

  const handleNewChat = () => {
    setSelectedChat(null);
    router.push("/");
    // Close sidebar on mobile when clicking new chat
    if (window.innerWidth < 768) {
      setExpand(false);
    }
  };

  return (
    <>
      {/* --- MOBILE OVERLAY --- */}
      <div 
        onClick={() => setExpand(false)}
        className={`md:hidden fixed inset-0 bg-black/50 z-40 transition-opacity duration-300
        ${expand ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
      ></div>

      {/* --- SIDEBAR CONTAINER --- */}
      <div
        className={`flex flex-col justify-between bg-[#212327] pt-7 transition-all duration-300 z-50 
        border-r border-gray-800 h-screen
        
        /* --- MOBILE STYLES (Screen < 768px) --- */
        fixed top-0 left-0
        ${expand ? "w-72 px-4" : "w-0 px-0 overflow-hidden border-none"}

        /* --- DESKTOP STYLES (Screen >= 768px) --- */
        md:relative md:border-r
        ${expand ? "md:w-72" : "md:w-20 md:px-0"}
        `}
      >
        <div>
          {/* Menu Icon (Toggle) */}
          <div className={`flex items-center absolute w-10 left-5 mb-6`}>
            <div
              onClick={() => setExpand(!expand)}
              className="group flex items-center justify-center hover:bg-gray-700/50 text-gray-400 hover:text-white transition-all duration-200 h-10 w-10 rounded-full cursor-pointer"
            >
              <Image 
                src={assets.menu_icon} 
                alt="Menu" 
                className="w-6 h-6 opacity-80" 
              />
            </div>
          </div>

          {/* New Chat Button */}
          <button
            onClick={handleNewChat}
            className={`flex items-center mt-12 justify-center cursor-pointer transition-all duration-300 whitespace-nowrap overflow-hidden ${
              expand 
                ? "bg-primary hover:opacity-90 rounded-full h-12 w-full gap-3 shadow-md" 
                : "group relative h-10 w-10 mx-auto hover:bg-gray-700/50 rounded-full"
            }`}
          >
            <Image className={expand ? "w-5" : "w-6"} src={expand ? assets.chat_icon : assets.chat_icon_dull} alt="New Chat" />
            {expand && <p className="text-white text-base font-medium">New chat</p>}
          </button>

          {/* Recents List */}
          <div
            onScroll={handleScroll}
            className={`mt-8 text-white/40 text-sm overflow-y-auto max-h-[60vh] custom-scrollbar whitespace-nowrap 
            ${expand ? "block opacity-100" : "hidden opacity-0"} transition-opacity duration-300`}
          >
            <p className="my-2 px-2 font-medium text-xs uppercase tracking-wider">Recents</p>
            {chats
              // ✅ CHANGE 1: Allow chats that have EITHER a title OR a name
              .filter((chat) => chat && (chat.title || chat.name))
              .map((chat) => (
                <ChatLabel 
                    key={chat._id} 
                    // ✅ CHANGE 2: Prioritize 'title', fallback to 'name', then "New Chat"
                    name={chat.title || chat.name || "New Chat"} 
                    id={chat._id} 
                    openMenu={openMenu} 
                    setOpenMenu={setOpenMenu} 
                    // Close sidebar on mobile if a chat is clicked
                    onSelect={() => { if(window.innerWidth < 768) setExpand(false); }}
                />
              ))}
          </div>
        </div>

        {/* User Profile */}
        <div className="mb-4 whitespace-nowrap overflow-hidden">
          <div 
            onClick={user ? null : openSignIn} 
            className={`flex items-center ${expand ? "hover:bg-white/5 rounded-xl px-3 py-3 justify-start" : "justify-center w-full hover:bg-white/5 rounded-xl py-3"} cursor-pointer text-white/70`}
          >
            {user ? (
                <div className="flex items-center justify-center"><UserButton /></div>
            ) : (
                <Image src={assets.profile_icon} alt="" className="w-7 h-7 rounded-full opacity-80" />
            )}
            {expand && <span className="ml-3 font-medium text-sm truncate">My Profile</span>}
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;