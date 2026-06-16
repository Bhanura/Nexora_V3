import React from 'react';
import ReactDOM from 'react-dom/client';
import ChatWidget from './ChatWidget';
// Import Tailwind styles. During build, these will be injected into the JS.
import '../index.css'; 

const MOUNT_POINT_ID = 'elanka-chat-ai-widget-root';

console.log('[eLanka Chat AI Widget] Script loaded');

function init(apiKey, options = {}) {
  console.log('[eLanka Chat AI Widget] Initializing with API key:', apiKey ? 'YES' : 'NO');
  
  if (!apiKey) {
    console.error("eLanka Chat AI Widget: API key is required");
    return;
  }

  // Default API URL (for widgets hosted on same domain)
  const apiUrl = options.apiUrl || window.location.origin + '/api';
  console.log('[eLanka Chat AI Widget] API URL:', apiUrl);

  // Create a container div if it doesn't exist
  let container = document.getElementById(MOUNT_POINT_ID);
  if (!container) {
    console.log('[eLanka Chat AI Widget] Creating container div');
    container = document.createElement('div');
    container.id = MOUNT_POINT_ID;
    document.body.appendChild(container);
  }

  // Mount React
  console.log('[eLanka Chat AI Widget] Mounting React component');
  const root = ReactDOM.createRoot(container);
  root.render(
    <React.StrictMode>
      <ChatWidget apiKey={apiKey} apiUrl={apiUrl} />
    </React.StrictMode>
  );
  console.log('[eLanka Chat AI Widget] Widget rendered successfully');
}

// Auto-initialize if window.ELANKA_CHAT_AI_CHATBOT_ID is set (legacy mode)
function autoInit() {
  const apiKey = window.ELANKA_CHAT_AI_CHATBOT_ID;
  if (apiKey) {
    console.log('[eLanka Chat AI Widget] Auto-initializing from window.ELANKA_CHAT_AI_CHATBOT_ID');
    init(apiKey);
  }
}

// Check for auto-init after DOM loads
if (document.readyState === 'complete') {
  autoInit();
} else {
  window.addEventListener('load', autoInit);
}

// Expose globally for browsers explicitly
window.eLankaChatAIWidget = { init };

// Export the init function
export { init };