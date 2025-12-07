'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

// -------------------------------------------------------------------------
// Type Definitions
// -------------------------------------------------------------------------
type Message = {
    role: 'user' | 'assistant';
    content: string;
    isStatus?: boolean; // Distinguishes between final answers and temporary status updates
};

type LogEntry = {
    timestamp: string;
    status: string;
    message: string;
    type: 'info' | 'success' | 'error';
};

/**
 * Main Application Component
 * 
 * Architecture:
 * - Uses Native `fetch` with `ReadableStream` for handling Server-Sent Events (SSE).
 * - Manages two distinct data streams:
 *   1. Ingestion Stream: Updates the "System Logs" console.
 *   2. Chat Stream: Updates the conversational UI.
 */
export default function Home() {
    // -------------------------------------------------------------------------
    // State Management
    // -------------------------------------------------------------------------
    const [url, setUrl] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    
    // Chat State
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isChatLoading, setIsChatLoading] = useState(false);

    // Logs State (Array of structured log entries)
    const [logs, setLogs] = useState<LogEntry[]>([]);
    
    // Refs for auto-scrolling
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const logsEndRef = useRef<HTMLDivElement>(null);

    // Helper: Scroll to bottom of chat/logs when new content arrives
    const scrollToBottom = (ref: React.RefObject<HTMLDivElement | null>) => {
        ref.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => { scrollToBottom(messagesEndRef); }, [messages]);
    useEffect(() => { scrollToBottom(logsEndRef); }, [logs]);

    /**
     * Adds a new entry to the System Logs console.
     */
    const addLog = (status: string, message: string, type: 'info' | 'success' | 'error' = 'info') => {
        const timestamp = new Date().toLocaleTimeString();
        setLogs(prev => [...prev, { timestamp, status, message, type }]);
    };

    /**
     * Handles Video Ingestion (Training)
     * Flow:
     * 1. Connects to /transcript endpoint.
     * 2. Reads the ReadableStream line-by-line (NDJSON format).
     * 3. Parses each line as JSON and updates the Logs state.
     */
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setLogs([]); // Clear previous logs
        
        try {
            addLog('init', `Connecting to backend for: ${url}`, 'info');

            const response = await fetch('http://localhost:8000/transcript', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });

            if (!response.body) throw new Error("No response body received");

            // -------------------------------------------------------------------------
            // Stream Reader Implementation
            // Reads binary chunks, decodes them to text, and splits by newline.
            // -------------------------------------------------------------------------
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                
                // Process all complete lines
                buffer = lines.pop() || ''; 

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);
                            
                            // Map backend status to UI log types
                            const logType = data.status === 'error' ? 'error' : 
                                            data.status === 'complete' ? 'success' : 'info';
                            
                            addLog(data.status, data.message, logType);

                            if (data.status === 'complete') {
                                addLog('system', '✅ Training complete! You can now chat.', 'success');
                            }
                        } catch (e) {
                            console.error("Error parsing JSON line:", line, e);
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Error:', error);
            addLog('error', `Connection failed: ${error}`, 'error');
        } finally {
            setIsLoading(false);
        }
    };

    /**
     * Handles Chat Interactions
     * Flow:
     * 1. Displays user message immediately.
     * 2. Shows a temporary "Thinking..." status message.
     * 3. Connects to /chat endpoint (Stream).
     * 4. Updates the temporary message with real-time status (Searching -> Found -> Generating).
     * 5. Final replacement with the actual LLM answer.
     */
    const handleChatSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsChatLoading(true);

        // Add initial placeholder for Assistant response
        setMessages(prev => [...prev, { role: 'assistant', content: 'Thinking...', isStatus: true }]);

        try {
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);
                            
                            // Update the last message (the assistant's placeholder)
                            setMessages(prev => {
                                const newHistory = [...prev];
                                const lastMsg = newHistory[newHistory.length - 1];
                                
                                if (data.status === 'complete') {
                                    // Final Answer: Remove status flag, set content
                                    lastMsg.content = data.response;
                                    lastMsg.isStatus = false;
                                } else if (data.status === 'error') {
                                    lastMsg.content = `❌ Error: ${data.message}`;
                                    lastMsg.isStatus = false;
                                } else {
                                    // Status Update: Keep status flag, update text
                                    lastMsg.content = data.message; // e.g., "Searching...", "Found context..."
                                    lastMsg.isStatus = true;
                                }
                                return newHistory;
                            });

                        } catch (e) {
                            console.error("JSON Parse Error", e);
                        }
                    }
                }
            }

        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'assistant', content: "Failed to reach server." }]);
        } finally {
            setIsChatLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 p-8 font-sans">
            <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                {/* LEFT COLUMN: Ingestion & Logs */}
                <div className="space-y-6">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500 mb-2">
                            Single Twin Video RAG Agent
                        </h1>
                        <p className="text-gray-400">
                            Ingest a YouTube video to chat with it.
                        </p>
                    </div>

                    {/* Input Form */}
                    <form onSubmit={handleSubmit} className="flex gap-2">
                        <input
                            type="text"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="Paste YouTube URL here..."
                            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-white placeholder-gray-500 transition-all"
                        />
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium transition-colors duration-200"
                        >
                            {isLoading ? 'Processing...' : 'Train'}
                        </button>
                    </form>

                    {/* System Logs Console */}
                    <div className="bg-black/50 border border-gray-800 rounded-lg overflow-hidden flex flex-col h-[600px]">
                        <div className="bg-gray-800 px-4 py-2 text-xs font-mono text-gray-400 border-b border-gray-700 flex justify-between items-center">
                            <span>SYSTEM LOGS - {logs.length} events</span>
                            {isLoading && <span className="animate-pulse text-blue-400">● Live</span>}
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-sm scrollbar-thin scrollbar-thumb-gray-700">
                            {logs.length === 0 && (
                                <div className="text-gray-600 italic text-center mt-20">
                                    Ready to ingest video...
                                </div>
                            )}
                            {logs.map((log, i) => (
                                <div key={i} className={`flex gap-2 animate-in fade-in slide-in-from-left-1 duration-200`}>
                                    <span className="text-gray-600 select-none">[{log.timestamp}]</span>
                                    <span className={`
                                        ${log.type === 'error' ? 'text-red-400' : ''}
                                        ${log.type === 'success' ? 'text-green-400 font-bold' : 'text-gray-300'}
                                    `}>
                                        {log.type === 'info' && <span className="text-blue-500 mr-2">ℹ</span>}
                                        {log.type === 'success' && <span className="mr-2">✅</span>}
                                        {log.type === 'error' && <span className="mr-2">❌</span>}
                                        {log.message}
                                    </span>
                                </div>
                            ))}
                            <div ref={logsEndRef} />
                        </div>
                    </div>
                </div>

                {/* RIGHT COLUMN: Chat Interface */}
                <div className="bg-gray-800/50 rounded-xl border border-gray-700 flex flex-col h-[750px] shadow-2xl">
                    <div className="p-4 border-b border-gray-700 bg-gray-800/80 backdrop-blur rounded-t-xl">
                        <h2 className="text-lg font-semibold flex items-center gap-2">
                            <span>💬</span> Agent Chat
                        </h2>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-600">
                        {messages.length === 0 && (
                            <div className="text-center text-gray-500 mt-32 space-y-2">
                                <div className="text-4xl">👋</div>
                                <p>Ingest a video, then ask me anything!</p>
                            </div>
                        )}
                        
                        {messages.map((m, i) => (
                            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`
                                    max-w-[85%] rounded-2xl px-5 py-3 shadow-sm
                                    ${m.role === 'user' 
                                        ? 'bg-blue-600 text-white rounded-br-none' 
                                        : m.isStatus 
                                            ? 'bg-gray-700/50 text-gray-400 italic border border-gray-600 animate-pulse' // Styling for status updates
                                            : 'bg-gray-700 text-gray-100 rounded-bl-none'
                                    }
                                `}>
                                    {m.role === 'assistant' && !m.isStatus ? (
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <ReactMarkdown>
                                                {m.content}
                                            </ReactMarkdown>
                                        </div>
                                    ) : (
                                        m.content
                                    )}
                                </div>
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>

                    <form onSubmit={handleChatSubmit} className="p-4 border-t border-gray-700 bg-gray-800/80 rounded-b-xl">
                        <div className="flex gap-2">
                            <input
                                className="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-blue-500 transition-colors placeholder-gray-500"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask about the video..."
                                disabled={isChatLoading || logs.length === 0} // Disable if no video ingested
                            />
                            <button 
                                type="submit" 
                                disabled={isChatLoading || logs.length === 0}
                                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 rounded-lg font-medium transition-all transform active:scale-95"
                            >
                                Send
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
