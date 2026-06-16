import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { API_BASE_URL } from "../config";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Authenticated fetch helper that includes JWT token from localStorage
 */
export async function authenticatedFetch(endpoint, options = {}) {
  const token = localStorage.getItem("token");
  
  const headers = {
    ...options.headers,
  };
  
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  return fetch(url, {
    ...options,
    headers,
  });
}