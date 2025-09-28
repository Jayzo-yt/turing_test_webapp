// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyDyH3Sjdncauz0HkXwz-L5Oc5oZeDspBHc",
  authDomain: "turing-de440.firebaseapp.com",
  projectId: "turing-de440",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

export const googleProvider = new GoogleAuthProvider();
// Configure Google provider to avoid COOP issues
googleProvider.setCustomParameters({
  prompt: "select_account",
});
