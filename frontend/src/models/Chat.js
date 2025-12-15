import mongoose from "mongoose";

const ChatSchema = new mongoose.Schema(
  {
    name: { type: String, required: true },
    messages: [
      {
        role: { type: String, required: true },
        content: { type: String, required: true },
        timestamp: { type: Number, required: true },
      },
    ],
    userId: { type: String, required: true },
  },
  {
    timestamps: true, // automatically adds createdAt and updatedAt
  }
);

// Use existing model if exists, otherwise create a new one
const Chat = mongoose.models.Chat || mongoose.model("Chat", ChatSchema);

export default Chat;
