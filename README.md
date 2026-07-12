# Veyor — deployment notes

## What changed from the original mockup

1. **AI Copilot now goes through a backend proxy** (`/server/app.py`) instead of
   calling a model API straight from the browser. It runs on **Groq's free
   tier** (`openai/gpt-oss-120b`) — no card required, generous enough for a
   demo. Set your real backend URL in `veyor.html` under `AI_BACKEND_URL`
   near the top of the `<script>` block.

2. **Live market data strip** added below the ticker (`renderTicker`), pulling
   real, current data from two free, keyless, CORS-enabled APIs:
   - USD/INR — `https://open.er-api.com/v6/latest/USD` (ExchangeRate-API's open endpoint, updates daily)
   - Gold / Silver / Copper spot prices — `https://api.gold-api.com/price/{XAU|XAG|HG}` (Gold-API, real-time)

   This refreshes every 60 seconds on the page. If either API is briefly
   unreachable it fails gracefully and just omits that card.

3. **Listings, suppliers, RFQs, and order history are still illustrative
   sample data** — not real, identifiable companies. I kept this
   intentionally: attaching fabricated prices/ratings/quotes to real small
   businesses pulled off a directory would misrepresent them, which isn't
   something to ship even in a demo. The footer now says this plainly.

## Deploying the site itself

`veyor.html` is a static single file — host it anywhere static:
Netlify, Vercel, GitHub Pages, Cloudflare Pages, S3, etc. Drag-and-drop the
file onto Netlify's dashboard is the fastest path if you just want a shareable link.

## Deploying the AI Copilot backend

The `/server` folder is a small Flask app.

**Local test:**
```bash
cd server
pip install -r requirements.txt
export GROQ_API_KEY=gsk_...
python app.py
```
Then in `veyor.html`, set:
```js
const AI_BACKEND_URL = "http://localhost:5000/api/copilot";
```

**Real deployment (Render, free tier, easiest for this):**
1. Push the `server/` folder to a GitHub repo (or a subfolder of one).
2. On Render: New → Web Service → connect the repo, root directory `server`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add environment variable `GROQ_API_KEY` with your key from console.groq.com.
6. Once deployed, copy the Render URL and set in `veyor.html`:
   ```js
   const AI_BACKEND_URL = "https://your-app.onrender.com/api/copilot";
   ```
Railway and Fly.io work the same way if you prefer those. Render's own free
web service tier spins down after inactivity and takes ~30s to wake up on
the first request after a while — normal, not a bug.

**Before going properly live**, lock `CORS(app, origins="*")` in `app.py`
down to your actual deployed site's origin, so nobody else can call your
Copilot backend (and spend your Anthropic credits) from a different site.
