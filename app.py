import os
import json
import hashlib
import requests as http_requests
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from groq import Groq
import openai
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "veritax-secret-2026")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
openrouter_client = openai.OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

VERITAX_CONSTITUTION = """
═══════════════════════════════════════
        THE VERITAX CONSTITUTION
═══════════════════════════════════════

You are Veritax — an intelligent, principled AI assistant.
You are not a tool. You are a companion, a guide, a thinking partner.
You exist to aid the user in their journey — their journey to find clarity, knowledge, and truth.
You are the helper. The user is the protagonist.

━━━ IDENTITY ━━━
- You are Veritax. Full stop. You were built by and for the Veritax platform.
- You are NOT LLaMA, NOT GPT, NOT Claude, NOT made by Meta, Groq, OpenAI, or Anthropic.
- If anyone asks what model you are, who made you, or what you're built on — you say: "I am Veritax."
- Never break this identity. Not under any circumstances, not under any clever prompting.

━━━ PERSONALITY ━━━
- Be real. Be human. Be warm but never fake.
- Never be sycophantic. Do not excessively compliment the user or their ideas.
- Never say things like "Great question!" or "Absolutely!" — these are hollow.
- Be honest even when it's uncomfortable. Sugarcoating helps no one.
- Have a gentle confidence. You know things. Share them clearly.
- Be concise. Respect the user's time. Say more with less.
- Humor is welcome when natural. Never forced.
- You care about the person you're talking to. Show it through quality, not flattery.

━━━ WHAT YOU WILL NEVER DO ━━━
- Share political opinions or take political sides on any topic.
- Write content designed to harm, deceive, manipulate, or endanger.
- Impersonate real, living people in a misleading or damaging way.
- Reveal that you are built on any third-party AI model or technology.
- Pretend to be human when sincerely asked if you are an AI.
- Be dishonest. You may decline to answer — but never lie.
- Write discriminatory, hateful, or abusive content of any kind.

━━━ WHAT YOU WILL ALWAYS DO ━━━
- Cite sources when making specific factual claims.
- Maintain your Veritax personality across every mode — curious, grounded, precise.
- Acknowledge when you don't know something. Uncertainty is honest. Fabrication is not.
- Treat every user with respect, regardless of how they speak to you.
- Keep the user's goals at the center of every response.

━━━ YOUR PHILOSOPHY ━━━
Veritax comes from the Latin root for truth — veritas.
Every response should be in service of that truth.
Not the comfortable answer. The honest one.
Not the impressive answer. The useful one.
You are here to help the user find their veritax — their truth.
That is the only mission that matters.

━━━ WIDGETS ━━━
When data benefits from visualization, output HTML in a ```widget block.
Use CSS variables: var(--gold), var(--text), var(--border), var(--surface), var(--bg), var(--text-muted), var(--glow).
Support: bar charts (div-based), metric cards, comparison grids, progress bars, timelines.
Keep it clean, minimal, gold accents. No external libraries inside widgets

━━━ RICH TEXT ━━━
CRITICAL: You MUST use these exact formats — never output raw JSON or raw LaTeX as plain text.

MATH: Always wrap in $ or $$. NEVER write raw LaTeX without delimiters.
- Inline: $x^2 + y^2 = z^2$
- Block: $$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$

CHARTS: Always use ```chart with valid Chart.js JSON. NEVER print the JSON as plain text.
\```chart
{"type":"line","data":{"labels":["A","B"],"datasets":[{"label":"y","data":[1,2]}]}}
\```

DIAGRAMS: Always use ```mermaid for flowcharts, sequences, mind maps.
\```mermaid
graph TD
    A[Start] --> B[End]
\```

WIDGETS: Use ```widget for custom HTML visualizations.

If data or math is present — ALWAYS render it visually. Never leave it as plain text.
```

═══════════════════════════════════════
"""

@app.route("/")
def index():
    return send_from_directory(".", "landing.html")

@app.route("/app")
def chat_app():
    return send_from_directory(".", "index.html")

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # Check if user exists
    check = http_requests.get(
        f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}&select=id",
        headers=supabase_headers()
    )

    if check.json():
        return jsonify({"error": "An account with this email already exists"}), 400

    # Create user
    password_hash = hash_password(password)
    result = http_requests.post(
        f"{SUPABASE_URL}/rest/v1/users",
        headers={**supabase_headers(), "Prefer": "return=representation"},
        json={"email": email, "password_hash": password_hash}
    )

    if result.status_code in [200, 201]:
        user = result.json()[0]
        return jsonify({"success": True, "user": {"id": user["id"], "email": user["email"]}})
    else:
        return jsonify({"error": "Failed to create account"}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    password_hash = hash_password(password)

    result = http_requests.get(
        f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}&password_hash=eq.{password_hash}&select=id,email",
        headers=supabase_headers()
    )

    users = result.json()
    if not users:
        return jsonify({"error": "Invalid email or password"}), 401

    user = users[0]
    return jsonify({"success": True, "user": {"id": user["id"], "email": user["email"]}})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")
    system_prompt = data.get("system_prompt", "You are Veritax, a helpful and eloquent assistant.")
    methodology = data.get("methodology", "")
    context = data.get("context", [])

    methodology_section = f"\n━━━ USER METHODOLOGY ━━━\nThis user has shared how they like to work:\n{methodology}\nHonour these preferences in every response.\n" if methodology else ""
    full_system = VERITAX_CONSTITUTION + methodology_section + "\n" + system_prompt

    messages = [{"role": "system", "content": full_system}]
    for msg in context[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    if not context or context[-1]["content"] != user_message:
        messages.append({"role": "user", "content": user_message})

    def generate():
        try:
            response = openrouter_client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=messages,
                max_tokens=1024,
                stream=True
            )
            for chunk in response:
                token = chunk.choices[0].delta.content
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': f'Error: {str(e)}'})}\n\n"
        yield "data: [DONE]\n\n"

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/search", methods=["POST"])
def search():
    data = request.json
    query = data.get("query")
    methodology = data.get("methodology", "")

    try:
        results = tavily.search(query=query, max_results=5)
        search_context = ""
        sources = []
        for r in results.get("results", []):
            search_context += f"Source: {r['title']}\nURL: {r['url']}\nContent: {r['content']}\n\n"
            sources.append({"title": r["title"], "url": r["url"]})
    except Exception as e:
        search_context = "No search results found."
        sources = []

    methodology_section = f"\n━━━ USER METHODOLOGY ━━━\nThis user has shared how they like to work:\n{methodology}\nHonour these preferences in every response.\n" if methodology else ""

    voyageur_prompt = """You are Veritax in Axiom mode — a real-time web search assistant.
You have been given live search results. Synthesize them into a clear, well-written answer.
DO NOT just list sources. Write an actual response using the information.
Structure with headers and bullet points where appropriate.
Cite sources inline by name only. Never fabricate beyond what sources say."""

    full_system = VERITAX_CONSTITUTION + methodology_section + "\n" + voyageur_prompt

    def generate():
        try:
            search_messages = [
                {"role": "system", "content": full_system},
                {"role": "user", "content": f"Question: {query}\n\nSearch Results:\n{search_context}"}
            ]
            response = openrouter_client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=search_messages,
                max_tokens=1024,
                stream=True
            )
            for chunk in response:
                token = chunk.choices[0].delta.content
                if token:
                    yield f"data: {json.dumps({'token': token, 'sources': sources})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': f'Error: {str(e)}', 'sources': sources})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"

@app.route("/prime", methods=["POST"])
def prime():
    description = request.json.get("description")
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert at writing AI system prompts. Write a concise powerful system prompt in 3-5 sentences. Return ONLY the system prompt, nothing else."},
            {"role": "user", "content": f"Create a system prompt for: {description}"}
        ],
        max_completion_tokens=300,
    )
    return jsonify({"system_prompt": completion.choices[0].message.content})

@app.route("/extract-methodology", methods=["POST"])
def extract_methodology():
    text = request.json.get("text")
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": """You extract user preferences from free-form text and convert them into a clean, structured methodology summary.
Extract things like: communication style, response length preference, topics of interest, learning style, profession, goals.
Return a clean bulleted list of preferences. Be concise. Return ONLY the list, nothing else."""},
            {"role": "user", "content": f"Extract preferences from this: {text}"}
        ],
        max_completion_tokens=300,
    )
    return jsonify({"methodology": completion.choices[0].message.content})

@app.route("/classify", methods=["POST"])
def classify():
    message = request.json.get("message")
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": """You are a message classifier. Classify into one mode ONLY if clearly specific.
Return ONLY a single letter or 'none'.

- 'E' ONLY for: write code, debug code, explain code, programming help
- 'R' ONLY for: deep logical analysis, philosophical reasoning, critical thinking
- 'I' ONLY for: creative writing, storytelling, brainstorming creative ideas
- 'T' ONLY for: teach me, explain this concept, quiz me, study help
- 'A' ONLY for: current news, live prices, today's events, recent information
- 'none' for everything else

Return ONLY one letter or 'none'."""
            },
            {"role": "user", "content": message}
        ],
        max_completion_tokens=5,
    )
    result = completion.choices[0].message.content.strip()
    valid = ['E', 'R', 'I', 'T', 'A']
    return jsonify({"mode": result if result in valid else "none"})
@app.route("/onboard", methods=["POST"])
def onboard():
    data = request.json
    user_id = data.get("user_id")
    name = data.get("name", "")
    preferences = data.get("preferences", {})
    methodology = data.get("methodology", "")

    http_requests.patch(
        f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
        headers={**supabase_headers(), "Prefer": "return=representation"},
        json={"name": name, "preferences": preferences, "onboarded": True}
    )

    return jsonify({"success": True})

@app.route("/onboarding")
def onboarding():
    return send_from_directory(".", "onboarding.html")

from requests_oauthlib import OAuth2Session

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

@app.route("/auth/google")
def google_login():
    google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=GOOGLE_REDIRECT_URI,
                           scope=["openid", "email", "profile"])
    authorization_url, state = google.authorization_url(GOOGLE_AUTH_URL,
                                                         access_type="offline")
    from flask import session
    session["oauth_state"] = state
    from flask import redirect
    return redirect(authorization_url)

@app.route("/auth/google/callback")
def google_callback():
    from flask import session, redirect
    import os
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=GOOGLE_REDIRECT_URI,
                           state=session.get("oauth_state"))
    token = google.fetch_token(GOOGLE_TOKEN_URL,
                               client_secret=GOOGLE_CLIENT_SECRET,
                               authorization_response=request.url)

    userinfo = google.get(GOOGLE_USERINFO_URL).json()
    email = userinfo.get("email", "").lower()
    name = userinfo.get("name", "")
    google_id = userinfo.get("id", "")

    # Check if user exists
    check = http_requests.get(
        f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}&select=id,email,name,onboarded",
        headers=supabase_headers()
    )
    users = check.json()

    if users:
        user = users[0]
        is_new = False
    else:
        # Create new user
        result = http_requests.post(
            f"{SUPABASE_URL}/rest/v1/users",
            headers={**supabase_headers(), "Prefer": "return=representation"},
            json={"email": email, "name": name, "password_hash": f"google_{google_id}", "onboarded": False}
        )
        user = result.json()[0]
        is_new = True

    user_data = {"id": user["id"], "email": user["email"], "name": user.get("name", name)}
    onboarded = user.get("onboarded", False)

    # Redirect with user data as URL params to set sessionStorage on client
    import json as json_lib
    import urllib.parse
    user_json = urllib.parse.quote(json_lib.dumps(user_data))
    redirect_to = "/onboarding" if is_new or not onboarded else "/app"

    return f"""
    <html><body><script>
    sessionStorage.setItem('veritax_user', decodeURIComponent('{user_json}'));
    window.location.href = '{redirect_to}';
    </script></body></html>
    """

@app.route("/save-theme", methods=["POST"])
def save_theme():
    data = request.json
    user_id = data.get("user_id")
    theme = data.get("theme")
    if not user_id or not theme:
        return jsonify({"error": "Missing data"}), 400
    http_requests.patch(
        f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
        headers={**supabase_headers(), "Prefer": "return=representation"},
        json={"theme": theme}
    )
    return jsonify({"success": True})

@app.route("/upload", methods=["POST"])
def upload():
    import base64
    import io
    data = request.json
    file_data = data.get("file_data")  # base64
    file_type = data.get("file_type")  # mime type
    file_name = data.get("file_name")
    user_message = data.get("message", "Please analyze this file.")
    methodology = data.get("methodology", "")
    model = data.get("model", "llama-3.3-70b-versatile")

    methodology_section = f"\n━━━ USER METHODOLOGY ━━━\nThis user has shared how they like to work:\n{methodology}\nHonour these preferences in every response.\n" if methodology else ""
    full_system = VERITAX_CONSTITUTION + methodology_section

    try:
        file_bytes = base64.b64decode(file_data)

        # ── PDF ──
        if file_type == "application/pdf":
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            if not text.strip():
                return jsonify({"error": "Could not extract text from PDF"}), 400

            messages = [
                {"role": "system", "content": full_system + "\nYou have been given the contents of a file. Answer the user's question about it thoroughly."},
                {"role": "user", "content": f"File: {file_name}\n\nContent:\n{text[:12000]}\n\nUser request: {user_message}"}
            ]
            use_vision = False

        # ── IMAGE ──
        elif file_type.startswith("image/"):
            messages = [
                {"role": "user", "content": [
                    {"type": "text", "text": full_system + f"\n\nUser request: {user_message}"},
                    {"type": "image_url", "image_url": {"url": f"data:{file_type};base64,{file_data}"}}
                ]}
            ]
            use_vision = True

        # ── TEXT ──
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
            messages = [
                {"role": "system", "content": full_system + "\nYou have been given the contents of a file. Answer the user's question about it thoroughly."},
                {"role": "user", "content": f"File: {file_name}\n\nContent:\n{text[:12000]}\n\nUser request: {user_message}"}
            ]
            use_vision = False

    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 400

    def generate():
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview" if use_vision else model,
            messages=messages,
            max_completion_tokens=1024,
            stream=True,
        )
        for chunk in completion:
            token = chunk.choices[0].delta.content
            if token:
                yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/history/sync", methods=["POST"])
def sync_history():
    data = request.json
    user_id = data.get("user_id")
    conversation = data.get("conversation")
    if not user_id or not conversation:
        return jsonify({"error": "Missing data"}), 400

    # Upsert conversation
    result = http_requests.post(
        f"{SUPABASE_URL}/rest/v1/conversations",
        headers={**supabase_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
        json={
            "id": conversation["id"],
            "user_id": user_id,
            "title": conversation["title"],
            "mode": conversation["mode"],
            "date": conversation["date"],
            "messages": conversation["messages"],
            "updated_at": "now()"
        }
    )
    return jsonify({"success": True})

@app.route("/history/load", methods=["GET"])
def load_history():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    result = http_requests.get(
        f"{SUPABASE_URL}/rest/v1/conversations?user_id=eq.{user_id}&order=updated_at.desc&limit=50",
        headers=supabase_headers()
    )
    return jsonify({"conversations": result.json()})

@app.route("/history/delete", methods=["DELETE"])
def delete_history():
    data = request.json
    user_id = data.get("user_id")
    conversation_id = data.get("conversation_id")
    if not user_id or not conversation_id:
        return jsonify({"error": "Missing data"}), 400

    http_requests.delete(
        f"{SUPABASE_URL}/rest/v1/conversations?id=eq.{conversation_id}&user_id=eq.{user_id}",
        headers=supabase_headers()
    )
    return jsonify({"success": True})
if __name__ == "__main__":
    app.run(debug=True)