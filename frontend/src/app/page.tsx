"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [chunks, setChunks] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput("");

    // Add user message to state
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setChatLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to get response");
      }

      // Add assistant response to state
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);
    } catch (err: any) {
      console.error("Chat error:", err);
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${err.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setTranscript("");
    setChunks([]);
    setMessages([]); // Reset chat on new video

    console.log("🚀 Starting transcript extraction process...");
    console.log(`🔗 URL: ${url}`);

    try {
      console.log("📡 Sending request to backend...");
      const response = await fetch("http://localhost:8000/transcript", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      console.log(`📥 Response status: ${response.status}`);
      const data = await response.json();

      if (!response.ok) {
        console.error("❌ Error from backend:", data.detail);
        throw new Error(data.detail || "Failed to fetch transcript");
      }

      console.log("✅ Transcript received!");
      console.log(`📄 Transcript length: ${data.transcript.length} characters`);
      console.log(`🧩 Number of chunks: ${data.total_chunks}`);

      setTranscript(data.transcript);
      setChunks(data.chunks);
    } catch (err: any) {
      console.error("💥 Exception occurred:", err);
      setError(err.message);
    } finally {
      setLoading(false);
      console.log("🏁 Process finished.");
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-50 dark:bg-gray-900">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold mb-8 text-center w-full text-gray-800 dark:text-white">
          YouTube Transcript Extractor
        </h1>
      </div>

      <div className="w-full max-w-2xl">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="url"
            placeholder="Enter YouTube URL (e.g., https://www.youtube.com/watch?v=...)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="p-4 rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="p-4 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Training..." : "Train Agent"}
          </button>
        </form>

        {error && (
          <div className="mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {transcript && (
          <div className="mt-8 space-y-8">
            <div>
              <h2 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-white">Full Transcript</h2>
              <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md max-h-[400px] overflow-y-auto whitespace-pre-wrap text-gray-700 dark:text-gray-300 leading-relaxed text-sm">
                {transcript}
              </div>
            </div>
          </div>
        )}

        {/* Chat Interface */}
        <div className="mt-12 w-full border-t border-gray-200 dark:border-gray-700 pt-8">
          <h2 className="text-2xl font-bold mb-6 text-center text-gray-800 dark:text-white">
            Chat with Agent
          </h2>

          <div className="flex flex-col h-[500px] bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 relative">

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-400">
                  Start a conversation...
                </div>
              ) : (
                messages.map((m, index) => (
                  <div
                    key={index}
                    className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${m.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                        }`}
                    >
                      <p className="text-xs font-bold mb-1 opacity-75 uppercase">
                        {m.role === "user" ? "You" : "Agent"}
                      </p>
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">
                        {m.content}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleChatSubmit} className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 rounded-b-lg">
              <div className="flex gap-2">
                <input
                  className="flex-1 p-3 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  value={input}
                  onChange={handleInputChange}
                  placeholder="Ask something..."
                  disabled={chatLoading}
                />
                <button
                  type="submit"
                  disabled={chatLoading || !input.trim()}
                  className="px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {chatLoading ? "..." : "Send"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </main>
  );
}
