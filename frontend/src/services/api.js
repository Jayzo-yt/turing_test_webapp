// API service for session management
import { auth } from "../firebase/firebase";

const API_BASE_URL = "http://localhost:8000";

// Helper function to get auth header
const getAuthHeader = async () => {
  const user = auth.currentUser;
  if (!user) {
    console.error("No authenticated user found");
    throw new Error("User not authenticated");
  }

  console.log("Getting token for user:", user.email);
  const token = await user.getIdToken();
  console.log("Token obtained, length:", token.length);
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
};

// API functions
export const sessionAPI = {
  // Create a new session
  async createSession(sessionData) {
    try {
      const headers = await getAuthHeader();
      const response = await fetch(`${API_BASE_URL}/api/sessions/create`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          session_name: sessionData.sessionName,
          description: sessionData.description || "",
          max_participants: sessionData.maxParticipants || 3,
          duration_minutes: sessionData.durationMinutes || 30,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create session");
      }

      return await response.json();
    } catch (error) {
      console.error("Error creating session:", error);
      throw error;
    }
  },

  // Join an existing session
  async joinSession(joinData) {
    try {
      const headers = await getAuthHeader();
      const response = await fetch(`${API_BASE_URL}/api/sessions/join`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          session_id: joinData.sessionId || null,
          join_code: joinData.joinCode || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to join session");
      }

      return await response.json();
    } catch (error) {
      console.error("Error joining session:", error);
      throw error;
    }
  },

  // Get session details
  async getSession(sessionId) {
    try {
      const headers = await getAuthHeader();
      const response = await fetch(
        `${API_BASE_URL}/api/sessions/${sessionId}`,
        {
          method: "GET",
          headers,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to get session");
      }

      return await response.json();
    } catch (error) {
      console.error("Error getting session:", error);
      throw error;
    }
  },

  // List user's sessions
  async listUserSessions() {
    try {
      const headers = await getAuthHeader();
      const response = await fetch(`${API_BASE_URL}/api/sessions`, {
        method: "GET",
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to list sessions");
      }

      return await response.json();
    } catch (error) {
      console.error("Error listing sessions:", error);
      throw error;
    }
  },

  // Delete a session
  async deleteSession(sessionId) {
    try {
      const headers = await getAuthHeader();
      const response = await fetch(
        `${API_BASE_URL}/api/sessions/${sessionId}`,
        {
          method: "DELETE",
          headers,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete session");
      }

      return await response.json();
    } catch (error) {
      console.error("Error deleting session:", error);
      throw error;
    }
  },

  // Connect to WebSocket for real-time communication
  connectToSession(sessionId, userId, role) {
    const wsUrl = `ws://localhost:8000/ws/${sessionId}/${userId}/${role}`;
    return new WebSocket(wsUrl);
  },
};
