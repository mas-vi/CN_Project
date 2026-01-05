from flask import Flask, request, jsonify
from google import genai
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
app = Flask(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.route("/generate_report", methods=["POST"])
def ai_worker():
    network_data = request.get_json()
    
    prompt = f"""
    You are a Network Security Analyst. Analyze the following network logs and provide a report in Markdown:
    {network_data}
    
    Include:
    - A summary of total ALLOW vs DENY actions.
    - Identification of any suspicious IP addresses.
    - Recommendations for firewall rules.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        
        return jsonify({

            "report": response.text,
            "timestamp": datetime.datetime.now(),
            "status": "created",
            "priority":"none"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

