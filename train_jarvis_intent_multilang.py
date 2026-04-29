#!/usr/bin/env python3
"""Create and POST multilingual intent training examples to Jarvis via /api/god-mode/feed

Usage:
  .venv\Scripts\python.exe train_jarvis_intent_multilang.py

Optional: set environment variable JARVIS_BASE to override base URL (default http://127.0.0.1:8001)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

BASE = os.environ.get("JARVIS_BASE", "http://127.0.0.1:8001")
FEED_URL = f"{BASE}/api/god-mode/feed"
TRAINING_LOG = Path(__file__).resolve().parent / "Brain_Logs" / "training_data.jsonl"

examples = [
    {"prompt": "hi jarvis", "response": "Hey Shri — how can I help you today?", "intent": "greeting", "language": "english", "source": "manual_training"},
    {"prompt": "हेलो जार्विस", "response": "नमस्ते! मैं आपकी कैसे मदद कर सकता/सकती हूँ?", "intent": "greeting", "language": "hindi", "source": "manual_training"},
    {"prompt": "hi jarvis whats my location", "response": "I don't have your current location; please confirm or enable location sharing so I can help.", "intent": "location_query", "language": "english", "source": "manual_training"},
    {"prompt": "mera location kya hai", "response": "मुझे आपका लोकेशन मालूम नहीं है — क्या आप अपना स्थान बताना चाहेंगे?", "intent": "location_query", "language": "hindi", "source": "manual_training"},
    {"prompt": "kya aaj mausam kaisa hai", "response": "Aapka location kya hai? Main uss location ka mausam bata dunga. (Please provide city or allow location.)", "intent": "weather_query", "language": "hinglish", "source": "manual_training"},
    {"prompt": "hi jarvis whats the weather today", "response": "Which city should I check the weather for? If you want current location, enable location sharing.", "intent": "weather_query", "language": "english", "source": "manual_training"},
    {"prompt": "find schools and tuition centers near 66 Foot Road Patel Nagar Bahadurgarh with mail and contact no", "response": "Searching local listings and web results; I'll return top matches with contacts and emails. Do you want results ranked by distance or rating?", "intent": "search_local", "language": "english", "source": "manual_training"},
    {"prompt": "schools aur tuition centers batado yahin ke", "response": "Thik hai — main aapke aas-paas ki top schools aur tuition centers dhoondh raha hoon. Kya contact details chahiye ya sirf naam?", "intent": "search_local", "language": "hinglish", "source": "manual_training"},
    {"prompt": "chal SCREEN PR KYA DIKHRA HAI VO BTA PURI SCREEN ANALYSE KRKE BTA", "response": "I can analyse a screenshot but I need a clearer image or the specific region to inspect. Please upload the image or allow screen access and confirm what you want me to find.", "intent": "screen_analysis", "language": "hinglish", "source": "manual_training"},
    {"prompt": "BRO TU WHATSAPP WEB KHOL JO SCREEN PR ALREADY AK TAB DIKHRA HAI VO KHOL OR VHA JAKE HIMANSHU 3 KO MSG KAR - HII", "response": "I cannot control other apps without your explicit integration and permission. I can show steps to open WhatsApp Web and prepare a message to send; do you want the prepared message?", "intent": "open_app_and_send_message", "language": "hinglish", "source": "manual_training"},
    {"prompt": "send 'Hi' to Himanshu on WhatsApp", "response": "I can craft the message and give you a one-click step to send via WhatsApp Web, but I need you to confirm and paste the prepared message in your WhatsApp Web tab.", "intent": "send_message", "language": "english", "source": "manual_training"},
    {"prompt": "tere pas mera pc acess hai ?", "response": "No — I don't have access to your PC unless you explicitly install and run a connector and grant permissions. I will always ask before taking control.", "intent": "privacy_check", "language": "hinglish", "source": "manual_training"},
    {"prompt": "gandva hai yar tu to , chal SCREEN PR KYA DIKHRA HAI VO BTA", "response": "I understand you're frustrated — please share the screenshot or clarify what you want me to inspect and I'll help promptly.", "intent": "profanity_deescalate", "language": "hinglish", "source": "manual_training"},
    {"prompt": "kya bakchodi krra hai", "response": "Let's keep it focused — tell me exactly what you need and I'll help. If you'd like brief replies, say 'Reply briefly'.", "intent": "profanity_deescalate", "language": "hinglish", "source": "manual_training"},
    {"prompt": "acha gst ka kam ata hai tujhe ?", "response": "I can help with GST basics — do you need HSN/SAC code help, invoice rates, or filing guidance? Please specify the transaction type.", "intent": "domain_clarify", "language": "hinglish", "source": "manual_training"},
    {"prompt": "summarise my last session in 3 bullets", "response": "Sure — I'll summarise the last session in 3 concise bullets: (1) key requests, (2) actions taken, (3) pending items. Would you like me to include timestamps?", "intent": "summarize_session", "language": "english", "source": "manual_training"},
    {"prompt": "Route this to a local model and explain why", "response": "Routing to a local model can improve privacy and reduce latency. I will choose a local model for sensitive data unless you prefer a cloud provider.", "intent": "route_model_decision", "language": "english", "source": "manual_training"},
    {"prompt": "What's running on port 8001 right now?", "response": "I can check system status and return the process listening on port 8001. Do you want full command-line details or a short summary?", "intent": "system_status", "language": "english", "source": "manual_training"},
    {"prompt": "Could not generate code: No module named requests", "response": "This error means Python package 'requests' is missing. Run `pip install requests` in your environment or enable the project's virtualenv.", "intent": "error_troubleshoot", "language": "english", "source": "manual_training"},
    {"prompt": "You can call me Shri", "response": "Got it — I'll remember your preferred display name is 'Shri'. Say 'forget name' to remove it.", "intent": "set_preference", "language": "english", "source": "manual_training"},
    {"prompt": "hi jarvis bro", "response": "Hey bro — what's up? How can I help right now?", "intent": "greeting", "language": "hinglish", "source": "manual_training"},
    {"prompt": "kya tum GST ke liye invoice bana doge", "response": "I can generate a GST invoice — please provide buyer details, items with HSN and rates, and the invoice date.", "intent": "task_request_generate_invoice", "language": "hinglish", "source": "manual_training"},
]


def post_examples(url: str, examples_list: list[dict]):
    print(f"Posting {len(examples_list)} training examples to {url}")
    try:
        r = requests.post(url, json={"examples": examples_list}, timeout=30)
        print("Status:", r.status_code)
        try:
            print("Response:", json.dumps(r.json(), indent=2))
        except Exception:
            print("Non-JSON response:", r.text[:400])
        return r
    except Exception as exc:
        print("Error posting training examples:", exc)
        return None


def tail_file(path: Path, n: int = 20):
    if not path.exists():
        print(f"Training log not found at {path}")
        return
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            decoded = raw.decode(enc)
            break
        except Exception:
            decoded = None
    if not decoded:
        decoded = raw.decode("utf-8", errors="ignore")
    lines = decoded.splitlines()
    print(f"\nLast {n} lines of {path}:\n")
    for line in lines[-n:]:
        print(line)


if __name__ == "__main__":
    res = post_examples(FEED_URL, examples)
    # Give the server a second to persist
    import time

    time.sleep(1.0)
    tail_file(TRAINING_LOG, n=30)
    # Optionally query learning stats
    try:
        stats = requests.get(f"{BASE}/agent/learning", timeout=10)
        print("\nLearning stats:", stats.status_code, stats.text[:800])
    except Exception:
        pass
    print("Done.")
