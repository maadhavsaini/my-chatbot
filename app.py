import os
from flask import Flask, request, jsonify, send_from_directory
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")
    system_prompt = data.get("system_prompt", "You are Verithos, a helpful and eloquent assistant.")

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_completion_tokens=1024,
    )

    reply = completion.choices[0].message.content
    return jsonify({"reply": reply})

@app.route("/prime", methods=["POST"])
def prime():
    description = request.json.get("description")

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at writing AI system prompts. Given a user's description of an assistant they want, write a concise, powerful system prompt in 3-5 sentences. Return ONLY the system prompt, nothing else."
            },
            {
                "role": "user",
                "content": f"Create a system prompt for this assistant: {description}"
            }
        ],
        max_completion_tokens=300,
    )

    system_prompt = completion.choices[0].message.content
    return jsonify({"system_prompt": system_prompt})

if __name__ == "__main__":
    app.run(debug=True)