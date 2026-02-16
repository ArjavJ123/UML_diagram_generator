import { useState, useEffect } from "react";
import { sendFeedback, fetchFeedback } from "../api/api";

export default function FeedbackModal({ diagram, onClose }) {
  const [rating, setRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState("");
  const [existingFeedback, setExistingFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // Load existing feedback
  useEffect(() => {
    const loadFeedback = async () => {
      try {
        const response = await fetchFeedback(diagram.diagram_id);
        console.log("Feedback response:", response);
        
        if (response.status === "success" && response.feedback) {
          setExistingFeedback(response);
          setRating(response.rating || 0);
          setFeedbackText(response.feedback || "");
        } else {
          setIsEditing(true);
        }
      } catch (error) {
        console.error("Failed to load feedback:", error);
        setIsEditing(true);
      }
    };

    loadFeedback();
  }, [diagram.diagram_id]);

  const handleSubmit = async () => {
    if (rating === 0) {
      alert("Please select a rating");
      return;
    }

    setLoading(true);
    console.log("Submitting feedback:", {
      diagram_id: diagram.diagram_id,
      rating,
      feedback: feedbackText,
    });

    try {
      const response = await sendFeedback({
        diagram_id: diagram.diagram_id,
        rating,
        feedback: feedbackText,
      });

      console.log("Submit response:", response);

      if (response.success) {
        alert("✓ Feedback submitted!");
        setExistingFeedback({ rating, feedback: feedbackText });
        setIsEditing(false);
      } else {
        alert(`Failed: ${response.message || "Unknown error"}`);
      }
    } catch (error) {
      alert("Failed to submit feedback");
      console.error("Submit error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={styles.header}>
          <h3 style={styles.title}>
            {diagram.diagram_type} Diagram (v{diagram.version})
          </h3>
          <button style={styles.closeBtn} onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Diagram Image */}
        <div style={styles.imageContainer}>
          <img
            src={`http://localhost:8000/${diagram.diagram_png_file_path}`}
            alt={`${diagram.diagram_type} diagram`}
            style={styles.image}
          />
        </div>

        {/* Feedback Section */}
        <div style={styles.feedbackSection}>
          <h4 style={styles.sectionTitle}>Feedback</h4>

          {/* Show existing feedback (not editing) */}
          {existingFeedback && !isEditing && (
            <div style={styles.existingFeedback}>
              <div style={styles.ratingDisplay}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <span key={star} style={styles.star}>
                    {star <= existingFeedback.rating ? "⭐" : "☆"}
                  </span>
                ))}
              </div>
              <p style={styles.feedbackText}>
                {existingFeedback.feedback || "No text feedback provided"}
              </p>
              <button
                style={styles.editBtn}
                onClick={() => setIsEditing(true)}
              >
                Edit Feedback
              </button>
            </div>
          )}

          {/* Feedback Form (editing or new) */}
          {(!existingFeedback || isEditing) && (
            <div style={styles.form}>
              {/* Rating */}
              <div style={styles.ratingSection}>
                <label style={styles.label}>Rating *</label>
                <div style={styles.stars}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      style={styles.starBtn}
                      onClick={() => setRating(star)}
                      type="button"
                    >
                      {star <= rating ? "⭐" : "☆"}
                    </button>
                  ))}
                </div>
              </div>

              {/* Feedback Text */}
              <div style={styles.textSection}>
                <label style={styles.label}>Feedback (optional)</label>
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Share your thoughts about this diagram..."
                  style={styles.textarea}
                  rows={4}
                />
              </div>

              {/* Buttons */}
              <div style={styles.buttons}>
                {existingFeedback && (
                  <button
                    style={styles.cancelBtn}
                    onClick={() => {
                      setIsEditing(false);
                      setRating(existingFeedback.rating || 0);
                      setFeedbackText(existingFeedback.feedback || "");
                    }}
                  >
                    Cancel
                  </button>
                )}
                <button
                  style={styles.submitBtn}
                  onClick={handleSubmit}
                  disabled={loading || rating === 0}
                >
                  {loading ? "Submitting..." : "Submit Feedback"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: "rgba(0, 0, 0, 0.8)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  modal: {
    background: "#1a1f2e",
    borderRadius: "16px",
    maxWidth: "800px",
    maxHeight: "90vh",
    width: "90%",
    overflow: "auto",
    boxShadow: "0 20px 60px rgba(0, 0, 0, 0.5)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "20px",
    borderBottom: "1px solid #2a2f45",
  },
  title: {
    margin: 0,
    fontSize: "20px",
    color: "#e5e7eb",
  },
  closeBtn: {
    background: "none",
    border: "none",
    color: "#9ca3af",
    fontSize: "24px",
    cursor: "pointer",
    padding: "0 8px",
  },
  imageContainer: {
    padding: "20px",
    display: "flex",
    justifyContent: "center",
    background: "#111827",
  },
  image: {
    maxWidth: "100%",
    height: "auto",
    borderRadius: "8px",
  },
  feedbackSection: {
    padding: "20px",
  },
  sectionTitle: {
    margin: "0 0 16px 0",
    fontSize: "16px",
    color: "#e5e7eb",
  },
  existingFeedback: {
    background: "#111827",
    padding: "16px",
    borderRadius: "8px",
  },
  ratingDisplay: {
    fontSize: "24px",
    marginBottom: "12px",
  },
  star: {
    marginRight: "4px",
  },
  feedbackText: {
    color: "#d1d5db",
    lineHeight: "1.5",
    marginBottom: "12px",
  },
  editBtn: {
    background: "#2563eb",
    border: "none",
    padding: "8px 16px",
    borderRadius: "6px",
    color: "white",
    cursor: "pointer",
    fontSize: "14px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  ratingSection: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  label: {
    fontSize: "14px",
    color: "#9ca3af",
    fontWeight: "500",
  },
  stars: {
    display: "flex",
    gap: "4px",
  },
  starBtn: {
    background: "none",
    border: "none",
    fontSize: "32px",
    cursor: "pointer",
    padding: 0,
    transition: "transform 0.1s",
  },
  textSection: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  textarea: {
    background: "#111827",
    border: "1px solid #2a2f45",
    borderRadius: "8px",
    padding: "12px",
    color: "white",
    fontSize: "14px",
    resize: "vertical",
    fontFamily: "inherit",
  },
  buttons: {
    display: "flex",
    gap: "8px",
    justifyContent: "flex-end",
  },
  cancelBtn: {
    background: "#374151",
    border: "none",
    padding: "10px 20px",
    borderRadius: "8px",
    color: "white",
    cursor: "pointer",
    fontSize: "14px",
  },
  submitBtn: {
    background: "#2563eb",
    border: "none",
    padding: "10px 20px",
    borderRadius: "8px",
    color: "white",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "600",
  },
};