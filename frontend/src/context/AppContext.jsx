"use client";
import { useAuth, useUser } from "@clerk/nextjs";
import axios from "axios";
import { createContext, useContext, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

export const AppContext = createContext(null);

export const useAppContext = () => useContext(AppContext);

const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL
const FASTAPI_BASE = `${process.env.NEXT_PUBLIC_BACKEND_BASE_URL}/api/py`;

export const AppContextProvider = ({ children }) => {
  const { user } = useUser();
  const { getToken } = useAuth();
  const router = useRouter();

  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]); 
  const [isMessagesLoading, setIsMessagesLoading] = useState(false);

  const fetchUsersChats = async () => {
    try {
      if (!user) return;
      setLoading(true);
      const token = await getToken();
      const { data } = await axios.get(`${FRONTEND_URL}/api/chat/get`, {
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
      toast.error("Failed to fetch chats");
    } finally {
      setLoading(false);
    }
  };

  // --- MODIFIED: Added 'redirect' parameter ---
  const createNewChat = async (redirect = true) => {
    try {
      if (!user) return null;
      const token = await getToken();
      const { data } = await axios.post(
        `${FRONTEND_URL}/api/chat/create`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (data.success) {
        const newChat = data.data;
        setChats((prev) => [newChat, ...prev]);
        
        // Only redirect if explicitly requested (Sidebar usage would use router.push separately anyway now)
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
      const { data } = await axios.get(`${FASTAPI_BASE}/api/py/thread/${threadId}/messages`);

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
        messages, 
        setMessages,
        fetchMessages,
        isMessagesLoading
      }}
    >
      {children}
    </AppContext.Provider>
  );
};