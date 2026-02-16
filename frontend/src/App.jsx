import { useChat } from "./hooks/useChat";
import ThreadSidebar from "./components/ThreadSidebar";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";

function App() {
  const {
    threads,
    currentThread,
    chatHistory,  // ← Changed from messages/diagrams
    loading,
    sendMessage,
    createNewThread,
    setCurrentThread,
  } = useChat();

  return (
    <div className="chat-container">
      <ThreadSidebar
        threads={threads}
        currentThread={currentThread}
        setCurrentThread={setCurrentThread}
        createNewThread={createNewThread}
      />

      <div className="chat-main">
        <ChatWindow chatHistory={chatHistory} />  {/* ← Pass chatHistory */}
        <InputBar onSend={sendMessage} disabled={loading} />
      </div>
    </div>
  );
}

export default App;