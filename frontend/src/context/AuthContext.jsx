import React, { createContext, useContext, useEffect, useState } from "react";
import { auth } from "@/firebase/firebase";
import { onAuthStateChanged, signOut, getRedirectResult } from "firebase/auth";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Handle redirect result first
    getRedirectResult(auth)
      .then((result) => {
        if (result?.user) {
          console.log("Redirect login successful:", result.user);
          setUser(result.user);
          // Navigate to home if needed - could be handled by onAuthStateChanged
        }
      })
      .catch((error) => {
        console.error("Redirect result error:", error);
      });

    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const logout = async () => {
    await signOut(auth);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
