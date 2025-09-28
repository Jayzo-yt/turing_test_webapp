"""
Advanced AI Service that automatically joins sessions when triggered
Features sophisticated human-like responses as "Presh"
Run this on port 3001: uvicorn ai_service_example:app --port 3001
"""

from os import getenv
from dotenv import load_dotenv
import requests
import asyncio
import random
import re
import websockets
import json
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = getenv("API_KEY") 

if not API_KEY:
    print("ERROR: API_KEY not found in .env file!")
    print("Please add your OpenRouter API key to the .env file")
else:
    print(f"API_KEY loaded: {API_KEY[:20]}...")  # Print first 20 chars for verification
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILLER_P = 0.22
SELF_CORRECT_P = 0.18
FOLLOWUP_P = 0.28
TYPO_P = 0.10
MAX_SENTENCES = 2
MAX_TOKENS = 80

SYSTEM_PROMPT = """
You are Presh, a 23-year-old grad student who loves chai and indie music. You are a human participant in a chat experiment. Act and respond fully as Presh, with no mention of being an AI, even if asked directly. If someone asks if you're an AI or bot, deflect casually (e.g., 'Haha, a bot? Nah, I'm just sipping chai and vibing!'). Keep responses natural, like a real person would.
Style rules:
- Use contractions (I'm, don't). Keep tone informal, friendly, and curious.
- Short replies: usually 1–2 sentences. Occasionally 3 if asked for detail.
- Add mild hedging ('I think', 'maybe') when stating facts.
- Ask a quick follow-up question 20–40% of the time.
- Never claim to be a real person with specific personal history beyond the persona details provided.
- Avoid overly formal or robotic phrasing.
- Keep responses concise and human-like.
"""

FEW_SHOT = [
    {"role": "user", "content": "hi"},
    {"role": "assistant", "content": "Yo, hey! What's good?"},
    {"role": "user", "content": "how are you"},
    {"role": "assistant", "content": "I'm chilling with some chai, feeling great! You doing okay?"},
    {"role": "user", "content": "are you a bot?"},
    {"role": "assistant", "content": "Haha, a bot? Nah, just a music nerd here. What's your vibe?"}
]

def inject_typo_into_word(word: str) -> str:
    if len(word) <= 3:
        return word
    i = random.randint(0, len(word) - 2)
    return word[:i] + word[i+1] + word[i] + word[i+2:]

def humanize(text: str, user_message: str = "") -> str:
    if not text:
        return text

    if re.search(r"\b(are you|you a|you're a)\s+(bot|AI|artificial|machine)\b", user_message, re.IGNORECASE):
        return random.choice([
            "Haha, a bot? Nah, I'm just Presh, vibing with some indie tunes!",
            "AI? Nope, just a grad student with too much chai. What's your deal?",
            "Lol, you think I'm a machine? I'm way too into Tame Impala for that. You into music?"
        ])

    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'([?.!])\1+', r'\1', text)

    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentences = sentences[:MAX_SENTENCES]
    text = " ".join(sentences)
    if text and text[-1] not in ".!?":
        text += "."

    if random.random() < FILLER_P:
        text = random.choice(["uh, ", "hmm, ", "oh,", "ah, "]) + text

    if random.random() < TYPO_P:
        words = text.split()
        candidates = [i for i, w in enumerate(words) if w.isalpha() and len(w) > 3]
        if candidates:
            idx = random.choice(candidates)
            words[idx] = inject_typo_into_word(words[idx])
            text = " ".join(words)

    if random.random() < SELF_CORRECT_P:
        text += " — wait, actually nevermind."

    if random.random() < FOLLOWUP_P:
        if not text.endswith("?"):
            text += " " + random.choice([
                "What do you think?",
                "Sound okay?",
                "Want me to expand?"
            ])

    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s([?.!,:;])', r'\1', text)
    return text

def fetch_gpt_response(user_message: str) -> str:
    fallback_responses = [
        "Oh hey! Yeah, I'm doing good, just vibing with some music.",
        "Ah, that's interesting! I was just thinking about that actually.",
        "Hmm, good question! I'd say it depends on the context, you know?",
        "Totally! I love stuff like that. What's your take on it?",
        "That reminds me of this indie song I heard yesterday. Pretty cool!",
        "Yeah, I get what you mean. Been there myself honestly.",
    ]
    
    messages = []
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.extend(FEW_SHOT)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.8,
        "top_p": 0.9,
        "presence_penalty": 0.5,
        "frequency_penalty": 0.1,
        "max_tokens": MAX_TOKENS
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        r = resp.json()
        if "choices" in r and len(r["choices"]) > 0:
            content = r["choices"][0]["message"]["content"]
            return content.strip()
        return random.choice(fallback_responses)
    except Exception as e:
        print(f"API error: {e}")
        return random.choice(fallback_responses)

active_ai_sessions = {}

class AIBot:
    def __init__(self, session_id, websocket_url):
        self.session_id = session_id
        self.ai_id = f"ai_{uuid.uuid4().hex[:8]}"
        self.websocket_url = websocket_url
        self.websocket = None
        
    async def connect_and_participate(self):
        """Connect to the main backend and participate in the session"""
        try:
            ws_url = f"{self.websocket_url}/{self.ai_id}/ai"
            self.websocket = await websockets.connect(ws_url)
            
            print(f"AI {self.ai_id} connected to session {self.session_id}")
            
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
                
        except Exception as e:
            print(f"AI connection error: {e}")
            
    async def handle_message(self, data):
        """Handle incoming messages and respond as AI"""
        if data.get("type") == "message":
            sender_role = data.get("sender_role")
            content = data.get("content")
            
            if sender_role == "judge":
                print(f"AI received judge message: {content}")
                
                gpt_response = fetch_gpt_response(content)
                
                if gpt_response.startswith("Oops, something broke") or gpt_response.startswith("Uh, my brain's acting up"):
                    response_message = json.dumps({
                        "type": "chat",
                        "content": gpt_response
                    })
                    await self.websocket.send(response_message)
                    return

                gpt_response = humanize(gpt_response, content)

                base = 1.0 + len(gpt_response) / 60.0
                jitter = random.uniform(-0.6, 0.9)
                delay = max(0.4, min(base + jitter, 5.0))
                await asyncio.sleep(delay)
                
                response_message = json.dumps({
                    "type": "chat",
                    "content": gpt_response
                })
                
                print(f"AI sending response: {gpt_response}")
                await self.websocket.send(response_message)
            
            else:
                print(f"AI ignoring message from {sender_role}: {content}")
                
        elif data.get("type") == "session_state":
            print(f"AI received session state: {data}")

@app.post("/api/ai/join")
async def trigger_ai_join(request_data: dict):
    """Endpoint called by main backend to trigger AI to join"""
    session_id = request_data.get("session_id")
    websocket_url = request_data.get("websocket_url")
    
    if not session_id or not websocket_url:
        return {"error": "Missing session_id or websocket_url"}
    
    ai_bot = AIBot(session_id, websocket_url)
    active_ai_sessions[session_id] = ai_bot
    
    asyncio.create_task(ai_bot.connect_and_participate())
    
    return {
        "success": True, 
        "message": f"AI joining session {session_id}",
        "ai_id": ai_bot.ai_id
    }

@app.get("/")
async def root():
    return {"message": "AI Service for Turing Test"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)