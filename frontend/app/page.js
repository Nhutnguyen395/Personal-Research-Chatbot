"use client";
import { useState } from "react";

export default function Home() {
  const [messages, setMessages] = useState([
    { role: "system", content: "Hello! Upload a PDF to start chatting." },
  ]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);

  // 1. Handle File Upload
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "system", content: `Ready! Indexed: ${data.filename}` },
      ]);
    } catch (error) {
      console.error(error);
      alert("Error uploading file. Is the Python backend running?");
    }
    setUploading(false);
  };

  // 2. Handle Messaging
  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add User Message immediately
    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // Send to Python Backend
      const res = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMsg.content }),
      });
      const data = await res.json();

      // Add AI Response + Sources
      const aiMsg = { 
        role: "assistant", 
        content: data.answer,
        sources: data.sources 
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev, 
        { role: "system", content: "Error connecting to backend." }
      ]);
    }
    setLoading(false);
  };

  return (
    <main className="flex flex-col h-screen bg-gray-900 text-gray-100 p-4">
      {/* HEADER & UPLOAD SECTION */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg shadow-md mb-4">
        <h1 className="text-xl font-bold text-blue-400">🤖 Personal Chatbot</h1>
        <div className="flex items-center gap-2">
          <input 
            type="file" 
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"
          />
          <button 
            onClick={handleUpload} 
            disabled={uploading || !file}
            className="bg-green-600 px-4 py-2 rounded text-sm font-bold hover:bg-green-500 disabled:opacity-50"
          >
            {uploading ? "Uploading..." : "Upload PDF"}
          </button>
        </div>
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto bg-gray-800 p-4 rounded-lg space-y-4">
        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`p-3 rounded-lg max-w-3xl ${
              msg.role === "user" 
                ? "bg-blue-600 ml-auto" 
                : msg.role === "system"
                ? "bg-gray-700 mx-auto text-center text-sm italic"
                : "bg-gray-700"
            }`}
          >
            <p className="whitespace-pre-wrap">{msg.content}</p>
            
            {/* RENDER SOURCES IF AVAILABLE */}
            {msg.sources && (
              <div className="mt-3 p-2 bg-gray-900 rounded text-xs">
                <p className="font-bold text-gray-400 mb-1">📚 Sources:</p>
                {msg.sources.map((src, i) => (
                  <div key={i} className="mb-1 pl-2 border-l-2 border-blue-500">
                    <span className="font-semibold text-blue-300">
                      Page {src.page}:
                    </span>{" "}
                    <span className="text-gray-400 italic">
                      "{src.text.slice(0, 100)}..."
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="text-gray-400 italic animate-pulse">Thinking...</div>}
      </div>

      {/* INPUT AREA */}
      <div className="mt-4 flex gap-2">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask a question about your PDF..."
          className="flex-1 p-3 rounded bg-gray-800 border border-gray-700 focus:outline-none focus:border-blue-500"
        />
        <button 
          onClick={sendMessage} 
          disabled={loading}
          className="bg-blue-600 px-6 py-3 rounded font-bold hover:bg-blue-500"
        >
          Send
        </button>
      </div>
    </main>
  );
}