"use client";
import { useAuth, useUser } from "@clerk/nextjs";
import axios from "axios";
import { createContext, useContext, useEffect, useState, useCallback } from "react"; // 1. Import useCallback
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

  // ✅ FIX 1: Wrap fetchUsersChats in useCallback so it doesn't change on every render
  const fetchUsersChats = useCallback(async () => {
    try {
      if (!user) return;
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
  }, [user, getToken]); // Dependencies

  // ✅ FIX 2: Wrap helper in useCallback
  const refreshTitleAfterDelay = useCallback(() => {
      setTimeout(() => {
        fetchUsersChats();
      }, 2500);
  }, [fetchUsersChats]);

  // ✅ FIX 3: Wrap createNewChat in useCallback
  const createNewChat = useCallback(async (redirect = true) => {
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
  }, [user, getToken, router]);

  // ✅ FIX 4: Wrap fetchMessages in useCallback
  const fetchMessages = useCallback(async (threadId) => {
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
  }, []);

  // Initial load effect
  useEffect(() => {
    if (user) fetchUsersChats();
  }, [user, fetchUsersChats]); // Safe now because fetchUsersChats is stable

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
        refreshTitleAfterDelay
      }}
    >
      {children}
    </AppContext.Provider>
  );
};