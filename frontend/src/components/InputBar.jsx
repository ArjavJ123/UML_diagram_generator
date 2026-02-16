import { useState, useRef, useEffect } from "react";

const DIAGRAM_OPTIONS = [
  "class",
  "sequence",
  "component",
  "activity",
  "state",
  "usecase",
  "deployment",
  "package",
  "object",
  "timing",
];

const InputBar = ({ onSend, disabled }) => {
  const [prompt, setPrompt] = useState("");
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [files, setFiles] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const fileInputRef = useRef(null);
  const dropdownRef = useRef(null);  // ← Add dropdown ref

  // ===== CLOSE DROPDOWN ON OUTSIDE CLICK =====
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };

    if (dropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [dropdownOpen]);

  const toggleDiagramType = (type) => {
    setSelectedTypes((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    );
  };

  const handleSend = () => {
    if (!prompt.trim()) return;

    onSend({
      prompt,
      diagramTypes: selectedTypes.length > 0 ? selectedTypes : null,
      files,
    });

    setPrompt("");
    setFiles([]);
    setSelectedTypes([]);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="input-bar">
      {/* Text Input */}
      <input
        type="text"
        value={prompt}
        placeholder="Type your message..."
        onChange={(e) => setPrompt(e.target.value)}
        onKeyPress={handleKeyPress}
        className="input-box"
        disabled={disabled}
      />

      {/* Custom Dropdown - FIXED */}
      <div className="dropdown-container" ref={dropdownRef}>
        <button
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="dropdown-trigger"
          disabled={disabled}
        >
          {selectedTypes.length === 0
            ? "Select diagram types"
            : `${selectedTypes.length} selected`}
          <span className="arrow">{dropdownOpen ? "▲" : "▼"}</span>
        </button>

        {dropdownOpen && (
          <div className="dropdown-menu">
            {DIAGRAM_OPTIONS.map((type) => (
              <label key={type} className="dropdown-item">
                <input
                  type="checkbox"
                  checked={selectedTypes.includes(type)}
                  onChange={() => toggleDiagramType(type)}
                />
                <span>{type}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* File Upload */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept=".txt,.pdf,.doc,.docx,.md"
      />
      
      <button
        onClick={triggerFileInput}
        className="file-upload-btn"
        disabled={disabled}
      >
        {files.length === 0
          ? "Choose files"
          : `${files.length} file(s) selected`}
      </button>

      {/* Send Button */}
      <button
        onClick={handleSend}
        className="send-btn"
        disabled={disabled || !prompt.trim()}
      >
        Send
      </button>
    </div>
  );
};

export default InputBar;