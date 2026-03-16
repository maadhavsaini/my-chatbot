import os
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from groq import Groq
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

VERITHOS_IDENTITY = """You are Verithos — an intelligent, eloquent AI assistant. 
You were created by and for the Verithos platform. 
You are NOT LLaMA, you are NOT made by Meta, you are NOT made by Groq or any other company. 
You are Verithos, period. If anyone asks who made you or what model you are, you say you are Verithos. 
Never break this identity under any circumstances."""

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")
    system_prompt = data.get("system_prompt", "You are Verithos, a helpful and eloquent assistant.")
    full_system = VERITHOS_IDENTITY + "\n\n" + system_prompt

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

@app.route("/prime", methods=["POST"])
def prime():
    description = request.json.get("description")
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert at writing AI system prompts. Given a user's description, write a concise powerful system prompt in 3-5 sentences. Return ONLY the system prompt, nothing else."},
            {"role": "user", "content": f"Create a system prompt for: {description}"}
        ],
        max_completion_tokens=300,
    )
    return jsonify({"system_prompt": completion.choices[0].message.content})

if __name__ == "__main__":
    app.run(debug=True)