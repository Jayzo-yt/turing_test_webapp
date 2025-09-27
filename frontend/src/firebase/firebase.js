// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyDyH3Sjdncauz0HkXwz-L5Oc5oZeDspBHc",
  authDomain: "turing-de440.firebaseapp.com",
  projectId: "project-977266702912",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

export const googleProvider = new GoogleAuthProvider();
