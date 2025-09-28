import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>; // optional loader

  return user ? children : <Navigate to="/" />; // redirect to login if not logged in
};

export default PrivateRoute;
