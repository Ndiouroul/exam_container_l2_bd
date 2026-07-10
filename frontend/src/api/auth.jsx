import { createContext, useContext, useState, useCallback } from "react";
import { authApi } from "./client.js";

const AuthContext = createContext(null);

const TOKEN_KEY = "dit_library_token";
const USER_KEY = "dit_library_user";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  });

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const register = useCallback(async ({ full_name, email, password }) => {
    // Inscription publique : pas de rôle à fournir (étudiant/professeur ont les mêmes
    // privilèges, le compte créé est toujours de type ETUDIANT côté serveur).
    await authApi.register({ full_name, email, password });
    await login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const isAdmin = user?.user_type === "PERSONNEL_ADMINISTRATIF";

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout, isAuthenticated: !!token, isAdmin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé dans un AuthProvider");
  return ctx;
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearStoredAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
