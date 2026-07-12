"""
Veyor AI Copilot backend — runs on Groq's FREE API tier.

This is the piece the front-end (veyor.html) talks to instead of calling
a model provider directly. Your Groq API key lives here, server-side,
never in the browser.

Groq's free tier (as of mid-2026): openai/gpt-oss-120b gets 30 requests/min,
1,000 requests/day, 200K tokens/day — no card required. Plenty for a demo.
Note: llama-3.3-70b-versatile and llama-3.1-8b-instant were deprecated by
Groq in June 2026 — this uses their current recommended free replacement.

Run locally:
    pip install -r requirements.txt
    export GROQ_API_KEY=gsk_...
    python app.py
    # -> listening on http://localhost:5000

Then in veyor.html, set:
    const AI_BACKEND_URL = "http://localhost:5000/api/copilot";

For a real deployment, deploy this folder to Render, Railway, Fly.io, or
similar (all have free tiers), set GROQ_API_KEY as an environment
variable there, and point AI_BACKEND_URL at the deployed URL instead.
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)

# In production, replace "*" with your actual site's origin, e.g.
# CORS(app, origins=["https://veyor.yourdomain.com"])
CORS(app, origins="*")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"  # free tier, current (post-June-2026) recommended model

SYSTEM_PROMPT = (
    "You are the Veyor AI Procurement Copilot, embedded inside a B2B "
    "industrial marketplace (raw materials, machinery, electronics, "
    "chemicals, construction materials, packaging, spare parts, "
    "warehouse/surplus assets, and logistics). Veyor's matching engine "
    "scores suppliers on proximity, trust, price, logistics fit and "
    "quality, prioritizing local and regional sourcing first and only "
    "expanding to national or global suppliers when local supply can't "
    "meet demand. You help buyers and sellers with: drafting clear RFQ / "
    "technical specifications, comparing supplier quotes (price, lead "
    "time, Incoterms, quality, proximity), explaining trade terms and "
    "documentation, and suggesting professional negotiation language. Be "
    "concise, practical, and structured — use short paragraphs and bullet "
    "points where helpful. You cannot access real listings, place real "
    "orders, or contact real suppliers; if asked to do so, briefly clarify "
    "you can help draft or plan, and the user completes the action in the "
    "platform themselves. Keep responses focused and under ~180 words "
    "unless the user asks for something longer."
)

MAX_HISTORY_MESSAGES = 20  # simple guardrail against runaway payloads/cost


@app.route("/api/copilot", methods=["POST"])
def copilot():
    if not os.environ.get("GROQ_API_KEY"):
        return jsonify({"error": "GROQ_API_KEY not configured on server"}), 500

    body = request.get_json(silent=True) or {}
    messages = body.get("messages", [])

    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "messages must be a non-empty list"}), 400

    # Keep only the most recent turns and make sure roles/content are the
    # simple shape we expect (defensive against a tampered client payload).
    clean_messages = []
    for m in messages[-MAX_HISTORY_MESSAGES:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str):
            clean_messages.append({"role": m["role"], "content": m["content"][:4000]})

    if not clean_messages:
        return jsonify({"error": "no valid messages"}), 400

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + clean_messages,
        )
        text = resp.choices[0].message.content.strip()
        return jsonify({"text": text})
    except Exception as e:
        app.logger.exception("Groq API call failed")
        return jsonify({"error": "The Copilot is temporarily unavailable."}), 502


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
