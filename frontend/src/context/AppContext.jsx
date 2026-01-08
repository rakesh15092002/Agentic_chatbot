"use client";
import { useAuth, useUser } from "@clerk/nextjs";
import axios from "axios";
import { createContext, useContext, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

export const AppContext = createContext(null);

export const useAppContext = () => useContext(AppContext);

const FASTAPI_BASE = `/api/py`;

export const AppContextProvider = ({ children }) => {
  const { user } = useUser();
  const { getToken } = useAuth();
  const router = useRouter();

  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]); 
  const [isMessagesLoading, setIsMessagesLoading] = useState(false);

  // Function to fetch all chats (Sidebar list)
  const fetchUsersChats = async () => {
    try {
      if (!user) return;
      // Don't set loading=true here to avoid Sidebar flickering during background refresh
      const token = await getToken();
      const { data } = await axios.get(`/api/chat/get`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!data.success) {
        toast.error(data.message);
        return;
      }

      const chatList = data.data || [];
      chatList.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
      setChats(chatList);
    } catch (error) {
      console.error("Failed to fetch chats", error);
    }
  };

  // ✅ NEW HELPER: Call this from your Chat Page after sending the FIRST message
  const refreshTitleAfterDelay = () => {
     // Wait 2.5 seconds for the 8B model to generate the title, then refresh sidebar
     setTimeout(() => {
        fetchUsersChats();
     }, 2500);
  };

  const createNewChat = async (redirect = true) => {
    try {
      if (!user) return null;
      const token = await getToken();
      const { data } = await axios.post(
        `/api/chat/create`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (data.success) {
        const newChat = data.data;
        setChats((prev) => [newChat, ...prev]);
        
        if (redirect) {
            router.push(`/chat/${newChat._id}`);
            toast.success("New chat started");
        }
        return newChat; 
      } else {
        toast.error(data.message);
        return null;
      }
    } catch (error) {
      toast.error("Failed to create chat");
      return null;
    }
  };

  const fetchMessages = async (threadId) => {
    try {
      setIsMessagesLoading(true);
      const { data } = await axios.get(`${FASTAPI_BASE}/thread/${threadId}/messages`);

      if (data && data.messages) {
        setMessages(data.messages);
      }
    } catch (error) {
      console.error(error);
      toast.error("Failed to load history");
    } finally {
      setIsMessagesLoading(false);
    }
  };

  useEffect(() => {
    if (user) fetchUsersChats();
  }, [user]);

  return (
    <AppContext.Provider
      value={{
        user,
        chats,
        setChats,
        selectedChat,
        setSelectedChat,
        fetchUsersChats,
        createNewChat,
        loading,
        FASTAPI_BASE,
        messages, 
        setMessages,
        fetchMessages,
        isMessagesLoading,
        refreshTitleAfterDelay // ✅ Exported helper
      }}
    >
      {children}
    </AppContext.Provider>
  );
};