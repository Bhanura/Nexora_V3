import { createContext, useContext, useState, useEffect } from "react";
import { API_BASE_URL, authenticatedFetch } from "../config";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // 1. Check if user is already logged in when page loads
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const profile = await authenticatedFetch("/auth/me");
          setUser(profile);
        } catch (err) {
          console.error("Session invalid:", err);
          localStorage.removeItem("token");
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  // 2. Login Logic (Matches FastAPI OAuth2 Form Data requirement)
  const login = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Invalid credentials");
    }

    const data = await response.json();
    localStorage.setItem("token", data.access_token);
    
    // Fetch full profile to get role
    const profile = await authenticatedFetch("/auth/me");
    setUser(profile);
    
    return profile.role; // Returns "client_admin" or "super_admin"
  };

  // 3. Register Logic
  const register = async (email, password, name) => {
    await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    }).then(async (res) => {
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Registration failed");
        }
    });
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);