import { useState, useEffect } from "react";
import {
  initialise,
  createThread,
  fetchThread,
  runPipelineStream,
} from "../api/api";

export const useChat = () => {
  const [threads, setThreads] = useState([]);
  const [currentThread, setCurrentThread] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // ===== INITIAL LOAD (ALWAYS RESET) =====
  useEffect(() => {
    const init = async () => {
      // Step 1: Reset backend
      await initialise();
      console.log("✓ Backend reset");
      
      // Step 2: Clear frontend
      localStorage.clear();
      console.log("✓ Frontend cleared");
      
      // Step 3: Create fresh thread
      const res = await createThread();
      const threadId = res.thread_id;

      setThreads([threadId]);
      setCurrentThread(threadId);
      
      // Step 4: Save to localStorage
      localStorage.setItem('threads', JSON.stringify([threadId]));
      localStorage.setItem('currentThread', threadId);
      
      console.log("✓ Fresh thread created:", threadId);
    };

    init();
  }, []);

  // ===== LOAD THREAD =====
  useEffect(() => {
    if (!currentThread) return;

    const load = async () => {
      const data = await fetchThread(currentThread);
      const history = convertToChat(data.messages, data.diagrams);
      setChatHistory(history);
    };

    load();
  }, [currentThread]);

  // ===== CONVERT BACKEND DATA TO CHAT FORMAT =====
  const convertToChat = (messages, diagrams) => {
    const history = [];
    
    messages.forEach((msg) => {
      // User message
      history.push({
        type: "user",
        message_id: msg.message_id,
        prompt: msg.prompt,
        diagram_types: msg.diagram_types,
        files: msg.files,
      });
      
      // Assistant response (diagrams for this message)
      const messageDiagrams = diagrams.filter(d => d.message_id === msg.message_id);
      
      if (messageDiagrams.length > 0) {
        history.push({
          type: "assistant",
          message_id: msg.message_id,
          diagrams: messageDiagrams,
        });
      }
    });
    
    return history;
  };

  const sendMessage = async ({ prompt, diagramTypes, files }) => {
    if (!currentThread || !prompt.trim()) return;

    const userMessage = {
      type: "user",
      message_id: `temp_${Date.now()}`,
      prompt: prompt,
      diagram_types: diagramTypes,
      files: files ? Array.from(files).map(f => f.name) : [],
    };

    const loadingMessage = {
      type: "assistant",
      message_id: `temp_loading_${Date.now()}`,
      loading: true,
      progressMessage: "🚀 Starting...",
      progress: 0
    };

    setChatHistory((prev) => [...prev, userMessage, loadingMessage]);
    setLoading(true);

    try {
      console.log('Starting stream...');
      
      await runPipelineStream({
        thread_id: currentThread,
        prompt,
        diagram_types: diagramTypes,
        files,
        onProgress: (update) => {
          console.log('Progress callback received:', update);
          
          // Update loading message
          setChatHistory((prev) => {
            const newHistory = [...prev];
            const loadingIdx = newHistory.findIndex(m => m.loading);
            
            if (loadingIdx !== -1) {
              newHistory[loadingIdx] = {
                ...newHistory[loadingIdx],
                progressMessage: update.message || "Processing...",
                progress: update.progress || 0
              };
            }
            
            return newHistory;
          });
        }
      });

      console.log('Stream complete, refreshing thread...');

      // Refresh thread
      const data = await fetchThread(currentThread);
      const history = convertToChat(data.messages, data.diagrams);
      setChatHistory(history);
      
    } catch (error) {
      console.error("Stream error:", error);
      
      setChatHistory((prev) => {
        const filtered = prev.filter(m => !m.loading);
        return [
          ...filtered,
          {
            type: "assistant",
            message_id: `error_${Date.now()}`,
            error: error.message || "Failed to generate diagrams",
          }
        ];
      });
    } finally {
      setLoading(false);
    }
  };

  // ===== CREATE THREAD =====
  const createNewThread = async () => {
    const res = await createThread();
    const threadId = res.thread_id;

    const newThreads = [...threads, threadId];
    setThreads(newThreads);
    setCurrentThread(threadId);
    setChatHistory([]);
    
    // Update localStorage
    localStorage.setItem('threads', JSON.stringify(newThreads));
    localStorage.setItem('currentThread', threadId);
  };

  return {
    threads,
    currentThread,
    chatHistory,
    loading,
    sendMessage,
    createNewThread,
    setCurrentThread,
  };
};