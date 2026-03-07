"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { login as apiLogin } from "./api";

interface AuthUser {
  id: string;
  email: string;
  name: string;
  picture: string | null;
  user_type: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
  loading: boolean;
  /** True when the authenticated user has account type COLLEGE or SUPER_ADMIN. */
  isCollegeAdmin: boolean;
  /** True when the authenticated user has account type SUPER_ADMIN. */
  isSuperAdmin: boolean;
}

const AuthContext = createContext<AuthContextValue>({} as AuthContextValue);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = localStorage.getItem("token");
    const u = localStorage.getItem("user");
    if (t && u) {
      setToken(t);
      setUser(JSON.parse(u));
    }
    setLoading(false);
  }, []);

  async function signIn(email: string, password: string) {
    const data = await apiLogin(email, password);
    const authUser: AuthUser = {
      id: data.user.id,
      email: data.user.email,
      name: data.user.name,
      picture: (data.user as { picture?: string | null }).picture ?? null,
      user_type: (data.user as { type?: string }).type ?? "USER",
    };
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(authUser));
    setToken(data.access_token);
    setUser(authUser);
  }

  function signOut() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  }

  const isCollegeAdmin = user?.user_type === "COLLEGE" || user?.user_type === "SUPER_ADMIN";
  const isSuperAdmin = user?.user_type === "SUPER_ADMIN";

  return (
    <AuthContext.Provider value={{ user, token, signIn, signOut, loading, isCollegeAdmin, isSuperAdmin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

