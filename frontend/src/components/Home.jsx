import { useAuth } from "@/context/AuthContext";
import { Trophy, ArrowRightIcon } from "lucide-react";
import { useState } from "react";
import ASCIIText from "./ASCIIText";
import { Button } from "@/components/ui/button";
import Judge from "./Judge";
import { sessionAPI } from "@/services/api";

export default function Home() {
  const [showProg, setSP] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { user, logout } = useAuth();

  const handleCreateSession = async () => {
    try {
      setLoading(true);
      setError(null);
      setSP(true); // Show the loader/judge component

      // Create session with default values
      const sessionData = {
        sessionName: `${user?.displayName || user?.email}'s Turing Test`,
        description:
          "A Turing test session to distinguish between AI and human",
        maxParticipants: 3,
        durationMinutes: 30,
      };

      const response = await sessionAPI.createSession(sessionData);
      console.log("Session created:", response);

      // You can store the session info and navigate to the session
      // For now, we'll just show the judge component
    } catch (error) {
      console.error("Failed to create session:", error);
      setError(error.message);
      setSP(false); // Hide loader on error
    } finally {
      setLoading(false);
    }
  };

  const handleJoinAsHuman = async () => {
    // For now, just show a simple prompt for join code
    const joinCode = prompt("Enter the session join code:");
    if (!joinCode) return;

    try {
      setLoading(true);
      setError(null);

      const response = await sessionAPI.joinSession({ joinCode });
      console.log("Joined session:", response);

      // Navigate to the session or update UI accordingly
      alert(`Successfully joined session: ${response.session_name}`);
    } catch (error) {
      console.error("Failed to join session:", error);
      setError(error.message);
      alert(`Failed to join session: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  console.log("from home ");
  console.log(user);
  return (
    <>
      <div className="relative h-[100vh] w-full ">
        <ASCIIText text="Hello!" enableWaves={false} asciiFontSize={8} />

        <div className=" h-[100vh] flex gap-5 justify-center items-end ">
          <Button className="group z-20 absolute top-10 ">
            Leaderboards
            <Trophy />
          </Button>
          <button
            className="group/btn shadow-input absolute right-4 top-5 flex h-10 items-center justify-start space-x-2 rounded-md bg-gray-50 px-4 font-medium text-black dark:bg-zinc-900 dark:shadow-[0px_0px_1px_1px_#262626]"
            onClick={logout}
          >
            <span className="text-sm text-neutral-700 dark:text-neutral-300">
              Logout
            </span>
          </button>

          <Button
            className="group z-20 relative bottom-20 "
            onClick={handleCreateSession}
            disabled={loading}
          >
            {loading ? "Creating Session..." : "Become a Turing Tester"}
            <ArrowRightIcon
              className="-me-1 opacity-60 transition-transform group-hover:translate-x-0.5"
              size={16}
              aria-hidden="true"
            />
          </Button>
          <Button
            className="group z-20 relative bottom-20 "
            onClick={handleJoinAsHuman}
            disabled={loading}
          >
            Play as Human
            <ArrowRightIcon
              className="-me-1 opacity-60 transition-transform group-hover:translate-x-0.5"
              size={16}
              aria-hidden="true"
            />
          </Button>
        </div>
        {showProg && (
          <div
            className="fixed inset-0 z-20 flex items-center justify-center bg-black/50"
            onClick={() => setSP(false)}
          >
            <div
              className="absolute top-[50%] rounded-2xl left-[50%] translate-[-50%]"
              onClick={(e) => e.stopPropagation()}
            >
              <Judge />
            </div>
          </div>
        )}

        {error && (
          <div className="fixed top-4 right-4 z-30 bg-red-500 text-white p-4 rounded-lg">
            <p>{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 px-3 py-1 bg-red-700 rounded text-sm"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>
    </>
  );
}
