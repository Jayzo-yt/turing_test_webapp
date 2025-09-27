import { useAuth } from "@/context/AuthContext";
import { Trophy, ArrowRightIcon } from "lucide-react";
// Component ported and enhanced from https://codepen.io/JuanFuentes/pen/eYEeoyE
import { useState } from "react";
import ASCIIText from "./ASCIIText";
import { MultiStepLoaderDemo } from "./MultiStep";
import { Button } from "@/components/ui/button";
import Judge from "./Judge";

export default function Home() {
  const { foundUser, setFU } = useState(false);
  const [showProg, setSP] = useState(false);
  const { user, logout } = useAuth();
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
            onClick={() => {
              setSP((t) => !t);
            }}
          >
            Become a Turing Tester
            <ArrowRightIcon
              className="-me-1 opacity-60 transition-transform group-hover:translate-x-0.5"
              size={16}
              aria-hidden="true"
            />
          </Button>
          <Button className="group z-20 relative bottom-20 ">
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
            className="fixed inset-0 z-20 flex items-center justify-center"
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
      </div>
    </>
  );
}
