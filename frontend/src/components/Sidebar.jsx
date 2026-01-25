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
    if (window.innerWidth < 768) setExpand(false);
  };

  return (
    <>
      {/* ---------------- MOBILE OVERLAY ---------------- */}
      <div
        onClick={() => setExpand(false)}
        className={`md:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40
        transition-opacity duration-300
        ${expand ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
      />

      {/* ---------------- SIDEBAR ---------------- */}
      <div
        className={`flex flex-col h-screen bg-[#171717] border-r border-[#333] z-50
        fixed top-0 left-0 md:relative
        w-[260px]
        transform transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]
        ${expand ? "translate-x-0" : "-translate-x-full md:translate-x-0 md:w-[72px]"}
        overflow-hidden`}
      >
        {/* ---------------- TOP ---------------- */}
        <div className="flex flex-col pt-5 px-3">
          {/* Toggle */}
          <div className={`flex items-center ${expand ? "justify-start pl-1" : "justify-center"} mb-6`}>
            <button
              onClick={() => setExpand(!expand)}
              className="p-2 hover:bg-white/10 rounded-lg transition"
            >
              <Image src={assets.menu_icon} alt="Menu" className="w-5 h-5 invert opacity-70" />
            </button>
          </div>

          {/* ---------------- NEW CHAT ---------------- */}
          <div className="relative group">
            <button
              onClick={handleNewChat}
              className={`flex items-center justify-center transition-all duration-300 whitespace-nowrap overflow-hidden
              ${expand
                ? "bg-blue-600 hover:bg-blue-700 w-full py-3 px-4 rounded-xl gap-3"
                : "bg-transparent hover:bg-white/10 w-10 h-10 rounded-lg mx-auto"
              }`}
            >
              <Image
                src={expand ? assets.chat_icon : assets.chat_icon_dull}
                alt="New Chat"
                className={`transition-all duration-300 shrink-0
                ${expand ? "w-5 brightness-200" : "w-6 opacity-60"}`}
              />

              <span
                className={`text-white text-sm transition-all duration-300
                ${expand ? "max-w-[150px] opacity-100" : "max-w-0 opacity-0"}`}
              >
                New Chat
              </span>
            </button>

            {!expand && (
              <div className="absolute left-14 top-1/2 -translate-y-1/2
                bg-black border border-white/20 text-white text-xs px-2 py-1 rounded
                opacity-0 group-hover:opacity-100 transition pointer-events-none">
                New Chat
              </div>
            )}
          </div>
        </div>

        {/* ---------------- RECENT CHATS ---------------- */}
        <div
          onScroll={handleScroll}
          className={`flex-1 overflow-y-auto mt-4 px-2 transition-opacity duration-300
          ${expand ? "opacity-100" : "opacity-100"}`}
        >
          {expand && (
            <p className="text-[11px] font-bold text-gray-500 mb-3 px-3 uppercase tracking-wider">
              Recent
            </p>
          )}

          <div className="flex flex-col gap-1">
            {chats
              .filter(chat => chat && (chat.title || chat.name))
              .map(chat => (
                <div key={chat._id}>
                  <ChatLabel
                    name={chat.title || chat.name || "New Chat"}
                    id={chat._id}
                    openMenu={openMenu}
                    setOpenMenu={setOpenMenu}
                    compact={!expand}
                    onSelect={() => {
                      if (window.innerWidth < 768) setExpand(false);
                    }}
                  />
                </div>
              ))}
          </div>
        </div>

        {/* ---------------- USER PROFILE ---------------- */}
        <div className="p-3 border-t border-white/10 bg-[#171717]">
          <button
            onClick={user ? null : openSignIn}
            className={`flex items-center w-full p-2 rounded-xl hover:bg-white/5 transition
            ${expand ? "justify-start gap-3" : "justify-center"}`}
          >
            {user ? (
              <div className="w-8 h-8 rounded-full overflow-hidden border border-white/20 shrink-0">
                <UserButton appearance={{ elements: { userButtonAvatarBox: "w-full h-full" } }} />
              </div>
            ) : (
              <Image src={assets.profile_icon} alt="" className="w-7 h-7 rounded-full opacity-70" />
            )}

            <div
              className={`flex flex-col overflow-hidden transition-all duration-300
              ${expand ? "max-w-[150px] opacity-100" : "max-w-0 opacity-0"}`}
            >
              <span className="text-sm text-gray-200 truncate">
                {user ? user.fullName || "User" : "Sign In"}
              </span>
              {user && <span className="text-xs text-gray-500">My Profile</span>}
            </div>
          </button>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
