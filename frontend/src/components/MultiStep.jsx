"use client";
import React, { useState } from "react";
import { MultiStepLoader as Loader } from "./ui/multi-step-loader";
import { IconSquareRoundedX } from "@tabler/icons-react";

const loadingStates = [
  {
    text: "Creating a Session",
  },
  {
    text: "Connecting to AI Chat bot",
  },
  {
    text: "Looking for USERS",
  },
  
];

export function MultiStepLoaderDemo() {
  const [loading, setLoading] = useState(true);
  return (
    <div className="w-full h-[60vh] rounded-2xl flex items-center justify-center">
      {/* Core Loader Modal */}
      <Loader loadingStates={loadingStates} loading={loading} duration={2000} />
      {/* The buttons are for demo only, remove it in your actual code ⬇️ */}
      <button
        onClick={() => setLoading(true)}
        
        style={{
            borderRadius: "200px",
          boxShadow:
            "0px -1px 0px 0px #ffffff40 inset, 0px 1px 0px 0px #ffffff40 inset",
        }}>
   
      </button>
      
      
    </div>
  );
}
