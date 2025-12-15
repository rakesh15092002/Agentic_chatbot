// lib/mongodb.js
import mongoose from "mongoose";

// Prevent multiple connections in development (Next.js hot reload)
let cached = global.mongoose || { conn: null, promise: null };

export default async function connectDB() {
  if (cached.conn) {
    // If connection already exists, reuse it
    return cached.conn;
  }

  if (!cached.promise) {
    // Create a new connection promise
    cached.promise = mongoose
      .connect(process.env.MONGODB_URI)
      .then((mongoose) => mongoose);
  }

  try {
    // Wait for connection to resolve
    cached.conn = await cached.promise;
  } catch (error) {
    console.error("Error connecting to MongoDB:", error);
    throw error; // Rethrow so API routes know it failed
  }

  // Store the cached object on global (for hot reloads)
  global.mongoose = cached;

  return cached.conn;
}
