import { useState } from "react";
import "./App.css";
import { AuthProvider } from "./context/AuthContext";
import PrivateRoute from "./routes/PrivateRoutes";
import Login from "./components/Login";
import Home from "./components/Home";
import Chat from "./components/Chat";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

function App() {
  const [count, setCount] = useState(0);

  return (
    <BrowserRouter>            {/* Only one BrowserRouter */}
      <AuthProvider>           {/* Auth context wraps all pages */}
        <Routes>
          <Route path="/" element={<Login />} />
          <Route
            path="/home"
            element={
              <PrivateRoute>
                <Home />
              </PrivateRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <PrivateRoute>
                <Chat />
              </PrivateRoute>
            }
          />
          {/* Redirect unknown paths to login */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
