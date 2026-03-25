# backend.py
from flask import Flask, request, abort
import requests, os

app = Flask(__name__)

SECRET_TOKEN = "your-secret-token-here-make-it-long"
DISCORD_WEBHOOK = "your-webhook-url"

@app.route("/process", methods=["POST"])
def process():
    token = request.headers.get("X-Secret-Token")
    if token != SECRET_TOKEN:
        abort(403)
    requests.post(DISCORD_WEBHOOK, json={"content": "🏐 Video payload received!"})
    return {"status": "received"}, 200