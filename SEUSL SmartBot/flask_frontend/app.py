"""
SEUSL Chatbot — Flask Frontend
Serves the chat UI and proxies /chat requests to the FastAPI backend.

Usage:
    pip install flask requests
    python flask_frontend/app.py

Open: http://localhost:5000   (FastAPI backend must run on http://localhost:8000)
"""

from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)
BACKEND_URL = "http://localhost:8000/chat"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "No message provided"}), 400
    try:
        resp = requests.post(BACKEND_URL, json={"message": data["message"]}, timeout=120)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.ConnectionError:
        return jsonify({
            "response": "Backend not reachable. Start FastAPI: uvicorn app:app --reload",
            "sources": []
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            "response": "Request timed out. The LLM may still be loading.",
            "sources": []
        }), 504
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}", "sources": []}), 500


if __name__ == "__main__":
    print("=" * 55)
    print("  SEUSL Chatbot — Flask Frontend")
    print("  URL : http://localhost:5000")
    print("  API : http://localhost:8000  (FastAPI backend)")
    print("=" * 55)
    app.run(debug=True, port=5000)
