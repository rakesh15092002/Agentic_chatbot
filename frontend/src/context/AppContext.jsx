"use client";
import { useAuth, useUser } from "@clerk/nextjs";
import axios from "axios";
import { createContext, useContext, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

export const AppContext = createContext(null);

export const useAppContext = () => useContext(AppContext);

export const AppContextProvider = ({ children }) => {
  const { user } = useUser();
  const { getToken } = useAuth();
  const router = useRouter();

  // --- State ---
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [loading, setLoading] = useState(false);

  // 1. NEW: State for storing messages of the current active chat
  const [messages, setMessages] = useState([]); 
  const [isMessagesLoading, setIsMessagesLoading] = useState(false);

  // --- Fetch Chat List (Sidebar) ---
  const fetchUsersChats = async () => {
    try {
      if (!user) return;
      setLoading(true);
      const token = await getToken();
      const { data } = await axios.get("/api/chat/get", {
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

  // --- Create Chat ---
  const createNewChat = async () => {
    try {
      if (!user) return;
      const token = await getToken();
      const { data } = await axios.post(
        "/api/chat/create",
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (data.success) {
        const newChat = data.data;
        setChats((prev) => [newChat, ...prev]);
        router.push(`/chat/${newChat._id}`);
        toast.success("New chat started");
      } else {
        toast.error(data.message);
      }
    } catch (error) {
      toast.error("Failed to create chat");
    }
  };

  // 2. NEW: Fetch Messages for a specific Thread ID
  const fetchMessages = async (threadId) => {
    try {
      setIsMessagesLoading(true);
      setMessages([]); // Clear old messages instantly

      // Direct call to FastAPI (Ensure your FastAPI is running on port 8000)
      // Or use your Next.js API route if you created a proxy
      const { data } = await axios.get(`http://localhost:8000/thread/${threadId}/messages`);

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
        // Export new states and functions
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