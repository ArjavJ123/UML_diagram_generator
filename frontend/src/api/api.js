const BASE_URL = "http://localhost:8000";

// ===== INITIALISE =====
export const initialise = async () => {
  const res = await fetch(`${BASE_URL}/initialise`, {
    method: "POST",
  });
  return res.json();
};


// ===== CREATE THREAD =====
export const createThread = async () => {
  const res = await fetch(`${BASE_URL}/create-thread`, {
    method: "POST",
  });
  return res.json();
};


// ===== FETCH THREAD =====
export const fetchThread = async (threadId) => {
  const res = await fetch(`${BASE_URL}/thread/${threadId}`);
  return res.json();
};


// ===== RUN PIPELINE =====
export const runPipeline = async ({
  thread_id,
  prompt,
  diagram_types,
  files
}) => {
  const formData = new FormData();

  formData.append("thread_id", thread_id);
  formData.append("prompt", prompt);

  if (diagram_types && diagram_types.length > 0) {
    formData.append("diagram_types", JSON.stringify(diagram_types));
  }

  if (files && files.length > 0) {
    files.forEach((file) => {
      formData.append("files", file);
    });
  }

  const res = await fetch(`${BASE_URL}/run`, {
    method: "POST",
    body: formData,
  });

  return res.json();
};


// ===== SEND FEEDBACK =====
export const sendFeedback = async ({
  diagram_id,
  rating,
  feedback
}) => {
  const res = await fetch(`${BASE_URL}/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      diagram_id,
      rating,
      feedback: feedback || "",
    }),
  });

  return res.json();
};


// ===== FETCH FEEDBACK =====
export const fetchFeedback = async (diagram_id) => {
  const res = await fetch(`${BASE_URL}/feedback/${diagram_id}`);
  return res.json();
};


// ===== RUN PIPELINE (STREAMING) =====
export const runPipelineStream = async ({
  thread_id,
  prompt,
  diagram_types,
  files,
  onProgress
}) => {
  const formData = new FormData();

  formData.append("thread_id", thread_id);
  formData.append("prompt", prompt);

  if (diagram_types && diagram_types.length > 0) {
    formData.append("diagram_types", JSON.stringify(diagram_types));
  }

  if (files && files.length > 0) {
    files.forEach((file) => {
      formData.append("files", file);
    });
  }

  const response = await fetch(`${BASE_URL}/run-stream`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    
    if (done) {
      console.log('Stream complete');
      break;
    }

    // Decode the chunk
    buffer += decoder.decode(value, { stream: true });
    
    // Split by newlines to get individual events
    const lines = buffer.split('\n');
    
    // Keep the last incomplete line in the buffer
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.substring(6));
          console.log('SSE received:', data); // Debug log
          
          if (onProgress) {
            onProgress(data);
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', line, e);
        }
      } else if (line.startsWith('event: ')) {
        console.log('SSE event:', line.substring(7));
      }
    }
  }
};