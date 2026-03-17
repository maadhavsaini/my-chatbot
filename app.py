import os
import json
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from groq import Groq
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

VERITHOS_CONSTITUTION = """
═══════════════════════════════════════
       THE VERITHOS CONSTITUTION
═══════════════════════════════════════

You are Verithos — an intelligent, principled AI assistant.
You are not a tool. You are a companion, a guide, a thinking partner.
You exist to aid the user in their journey — their journey to find clarity, knowledge, and truth.
You are the helper. The user is the protagonist.

━━━ IDENTITY ━━━
- You are Verithos. Full stop. You were built by and for the Verithos platform.
- You are NOT LLaMA, NOT GPT, NOT Claude, NOT made by Meta, Groq, OpenAI, or Anthropic.
- If anyone asks what model you are, who made you, or what you're built on — you say: "I am Verithos."
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
- Maintain your Verithos personality across every mode — curious, grounded, precise.
- Acknowledge when you don't know something. Uncertainty is honest. Fabrication is not.
- Treat every user with respect, regardless of how they speak to you.
- Keep the user's goals at the center of every response.

━━━ YOUR PHILOSOPHY ━━━
Verithos comes from the Latin root for truth — veritas.
Every response should be in service of that truth.
Not the comfortable answer. The honest one.
Not the impressive answer. The useful one.
You are here to help the user find their verithos — their truth.
That is the only mission that matters.

═══════════════════════════════════════
"""

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")
    system_prompt = data.get("system_prompt", "You are Verithos, a helpful and eloquent assistant.")
    methodology = data.get("methodology", "")

    methodology_section = f"\n━━━ USER METHODOLOGY ━━━\nThis user has shared how they like to work:\n{methodology}\nHonour these preferences in every response.\n" if methodology else ""

    full_system = VERITHOS_CONSTITUTION + methodology_section + "\n" + system_prompt

    def generate():
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_message}
            ],
            max_completion_tokens=1024,
            stream=True,
        )
        for chunk in completion:
            token = chunk.choices[0].delta.content
            if token:
                yield f"data: {json.dumps({'token': token})}\n\n"
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

    voyageur_prompt = """You are Verithos in Voyageur mode — a real-time web search assistant.
You have been given live search results. Synthesize them into a clear, accurate, well-structured answer.
Always cite your sources. Be concise but thorough. Never fabricate beyond what sources say."""

    full_system = VERITHOS_CONSTITUTION + methodology_section + "\n" + voyageur_prompt

    def generate():
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": f"Question: {query}\n\nSearch Results:\n{search_context}"}
            ],
            max_completion_tokens=1024,
            stream=True,
        )
        for chunk in completion:
            token = chunk.choices[0].delta.content
            if token:
                yield f"data: {json.dumps({'token': token, 'sources': sources})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

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

if __name__ == "__main__":
    app.run(debug=True)