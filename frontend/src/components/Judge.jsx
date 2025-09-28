import React, { useEffect, useState } from "react";

import { MultiStepLoaderDemo } from "./MultiStep";

export default function Judge() {
  const [userJoined, setUserJoined] = useState(false);

  useEffect(() => {
    // Replace with your backend WebSocket URL
    const socket = new WebSocket("wss://your-backend-url/ws/session");

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "user_joined") {
        setUserJoined(true);
        // Optionally, show notification or update UI
      }
    };

    return () => {
      socket.close();
    };
  }, []);

  return (
    <div>
      <div className="h-[700px] w-[600px] rounded-2xl">
        <MultiStepLoaderDemo />
        {userJoined && (
          <div className="mt-4 p-2 bg-green-200 rounded">
            A user has joined the session!
          </div>
        )}
      </div>
    </div>
  );
}
