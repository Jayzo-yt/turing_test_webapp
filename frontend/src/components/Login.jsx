import React from 'react'
import SignupFormDemo from './LoginForm'
import { useEffect } from 'react';
import { useState } from 'react';
import LoginForm from './LoginForm';

export default function Login() {
    const [dark, setDark] = useState(true);


  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.add("dark");
    }
  }, [dark]);
  return (
     <>
     <div className="min-h-screen bg-white dark:bg-black flex items-center justify-center">
      <button
        className="absolute top-4 right-4 p-2 border rounded"
        onClick={() => setDark(!dark)}
      >
        Toggle Dark
      </button>
    
   <LoginForm/>
   </div>
   </>
    
  )
}
