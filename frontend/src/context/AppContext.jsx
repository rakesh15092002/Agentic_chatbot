"use client";

import { useUser } from "@clerk/nextjs";
import { createContext, useContext } from "react";

// 1️⃣ Create the context
export const AppContext = createContext();

// 2️⃣ Custom hook to use the context
export const useAppContext = () => {
    return useContext(AppContext);
}

// 3️⃣ Context Provider
export const AppContextProvider = ({ children }) => {
    const { user } = useUser();  // Clerk user

    const value = {
        user,  // pass any data you want to share globally
    };

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
}
