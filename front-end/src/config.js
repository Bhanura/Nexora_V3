// API Base URL Configuration
// In production (Docker): Uses /api (nginx reverse proxy)
// In development: Uses localhost:8000 directly
export const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? "/api" : "http://localhost:8000/api");

export const authenticatedFetch = async (endpoint, options = {}) => {
  const token = localStorage.getItem("token");
  
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // If token is expired/invalid, auto-logout
  if (response.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "API Request Failed");
  }

  return response.json();
};