import { useState } from "react";
import FeedbackModal from "./FeedbackModal";

export default function ChatWindow({ chatHistory }) {
  const [selectedDiagram, setSelectedDiagram] = useState(null);

  return (
    <div style={styles.container}>
      {chatHistory.length === 0 && (
        <div style={styles.empty}>Start a conversation 🚀</div>
      )}

      {chatHistory.map((item, index) => {
        if (item.type === "user") {
          return <UserMessage key={index} message={item} />;
        } else if (item.type === "assistant") {
          return (
            <AssistantMessage
              key={index}
              message={item}
              onDiagramClick={setSelectedDiagram}
            />
          );
        }
        return null;
      })}

      {/* Feedback Modal */}
      {selectedDiagram && (
        <FeedbackModal
          diagram={selectedDiagram}
          onClose={() => setSelectedDiagram(null)}
        />
      )}
    </div>
  );
}

// ===== USER MESSAGE COMPONENT =====
function UserMessage({ message }) {
  return (
    <div style={styles.userContainer}>
      <div style={styles.userBubble}>
        <div style={styles.userPrompt}>{message.prompt}</div>
        
        {message.diagram_types && message.diagram_types.length > 0 && (
          <div style={styles.metadata}>
            📊 Diagram Types: {message.diagram_types.join(", ")}
          </div>
        )}
        
        {message.files && message.files.length > 0 && (
          <div style={styles.metadata}>
            📎 Files: {message.files.join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}

// ===== ASSISTANT MESSAGE COMPONENT =====
function AssistantMessage({ message, onDiagramClick }) {
  // Loading state with progress
  if (message.loading) {
    return (
      <div style={styles.assistantContainer}>
        <div style={styles.loadingBubble}>
          <div style={styles.progressContainer}>
            <div style={styles.spinner}></div>
            <div style={styles.progressText}>
              <div style={styles.progressMessage}>
                {message.progressMessage || "Generating diagrams..."}
              </div>
              {message.progress !== undefined && (
                <div style={styles.progressBarContainer}>
                  <div style={styles.progressBar}>
                    <div 
                      style={{
                        ...styles.progressFill,
                        width: `${message.progress}%`
                      }}
                    />
                  </div>
                  <span style={styles.progressPercentage}>
                    {message.progress}%
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (message.error) {
    return (
      <div style={styles.assistantContainer}>
        <div style={styles.errorBubble}>
          ❌ {message.error}
        </div>
      </div>
    );
  }

  // Success with diagrams
  return (
    <div style={styles.assistantContainer}>
      <div style={styles.assistantBubble}>
        <div style={styles.assistantText}>Here are your diagrams:</div>
        
        <div style={styles.diagramGrid}>
          {message.diagrams.map((diagram) => (
            <div
              key={diagram.diagram_id}
              style={styles.diagramCard}
              onClick={() => onDiagramClick(diagram)}
            >
              <img
                src={`http://localhost:8000/${diagram.diagram_png_file_path}`}
                alt={`${diagram.diagram_type} diagram`}
                style={styles.diagramImage}
                onError={(e) => {
                  e.target.style.display = "none";
                  console.error("Failed to load:", diagram.diagram_png_file_path);
                }}
              />
              <div style={styles.diagramLabel}>
                {diagram.diagram_type} diagram (v{diagram.version})
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ===== STYLES =====
const styles = {
  container: {
    flex: 1,
    overflowY: "auto",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  empty: {
    textAlign: "center",
    marginTop: "100px",
    color: "#888",
    fontSize: "18px",
  },
  
  // User message
  userContainer: {
    display: "flex",
    justifyContent: "flex-end",
  },
  userBubble: {
    background: "#2563eb",
    padding: "12px 16px",
    borderRadius: "16px",
    maxWidth: "70%",
    wordWrap: "break-word",
  },
  userPrompt: {
    marginBottom: "8px",
  },
  metadata: {
    fontSize: "12px",
    opacity: 0.8,
    marginTop: "6px",
    paddingTop: "6px",
    borderTop: "1px solid rgba(255, 255, 255, 0.2)",
  },
  
  // Assistant message
  assistantContainer: {
    display: "flex",
    justifyContent: "flex-start",
  },
  assistantBubble: {
    background: "#1a1f2e",
    padding: "12px 16px",
    borderRadius: "16px",
    maxWidth: "85%",
  },
  assistantText: {
    marginBottom: "12px",
    color: "#e5e7eb",
  },
  
  // Loading with progress
  loadingBubble: {
    background: "#1a1f2e",
    padding: "16px",
    borderRadius: "16px",
    minWidth: "300px",
  },
  progressContainer: {
    display: "flex",
    alignItems: "flex-start",
    gap: "12px",
  },
  spinner: {
    width: "20px",
    height: "20px",
    border: "3px solid #333",
    borderTop: "3px solid #2563eb",
    borderRadius: "50%",
    animation: "spin 1s linear infinite",
    flexShrink: 0,
    marginTop: "2px",
  },
  progressText: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  progressMessage: {
    color: "#e5e7eb",
    fontSize: "14px",
    lineHeight: "1.4",
  },
  progressBarContainer: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  progressBar: {
    flex: 1,
    height: "6px",
    background: "#333",
    borderRadius: "3px",
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    background: "linear-gradient(90deg, #2563eb 0%, #3b82f6 100%)",
    transition: "width 0.3s ease",
    borderRadius: "3px",
  },
  progressPercentage: {
    fontSize: "12px",
    color: "#9ca3af",
    minWidth: "35px",
    textAlign: "right",
  },
  
  // Error
  errorBubble: {
    background: "#7f1d1d",
    padding: "12px 16px",
    borderRadius: "16px",
    color: "#fca5a5",
  },
  
  // Diagrams
  diagramGrid: {
    display: "flex",
    flexWrap: "wrap",
    gap: "12px",
  },
  diagramCard: {
    background: "#111827",
    padding: "8px",
    borderRadius: "10px",
    cursor: "pointer",
    transition: "transform 0.2s, box-shadow 0.2s",
  },
  diagramImage: {
    width: "350px",
    maxWidth: "100%",
    borderRadius: "6px",
    display: "block",
  },
  diagramLabel: {
    fontSize: "12px",
    color: "#9ca3af",
    marginTop: "6px",
    textAlign: "center",
  },
};