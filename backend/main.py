import os
import json
import uuid
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient, DESCENDING, ASCENDING
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")

client = MongoClient('mongodb://localhost:27017/')
db = client['cn_project']

app.config['SESSION_TYPE'] = 'mongodb'
app.config['SESSION_MONGODB'] = client
app.config['SESSION_MONGODB_DB'] = 'cn_project'
app.config['SESSION_MONGODB_COLLECT'] = 'sessions'
Session(app)
bcrypt = Bcrypt(app)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        un = request.form.get("username")
        pw = request.form.get("password")
        if db.users.find_one({"username": un}): return "User exists", 400
        db.users.insert_one({"username": un, "password": bcrypt.generate_password_hash(pw).decode('utf-8')})
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        un = request.form.get("username")
        pw = request.form.get("password")
        user = db.users.find_one({"username": un})
        if user and bcrypt.check_password_hash(user['password'], pw):
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        return "Invalid credentials", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect(url_for("login"))
    reports = list(db.reports.find().sort("timestamp", DESCENDING))
    return render_template("dashboard.html", reports=reports)

@app.route("/reports/table")
def reports_table():
    if "user_id" not in session: return redirect(url_for("login"))
    reports = list(db.reports.find().sort("timestamp", DESCENDING))
    return render_template("reports_table.html", reports=reports)

@app.route("/report/<report_id>")
def report_details(report_id):
    if "user_id" not in session: return redirect(url_for("login"))
    report = db.reports.find_one({"report_id": report_id})
    activities = list(db.activities.find({"report_id": report_id}))
    return render_template("report_details.html", report=report, activities=activities)

@app.route("/report/delete/<report_id>", methods=["POST"])
def delete_report(report_id):
    if "user_id" not in session: return redirect(url_for("login"))
    db.reports.delete_one({"report_id": report_id})
    db.activities.delete_many({"report_id": report_id})
    return redirect(url_for("dashboard"))

@app.route("/report", methods=["POST"])
def generate_report():
    try:
        with open("../logs_script/network_logs.json") as logs:
            data = json.load(logs)
        response = requests.post("http://127.0.0.1:5001/generate_report", json=data)
        res = response.json() 
        rid = str(uuid.uuid4())
        db.reports.insert_one({
            "report_id": rid,
            "report_data": res["report"],
            "status": res["status"],
            "priority": res.get("priority", "medium"),
            "timestamp": res["timestamp"],
            "activity_ids": []
        })
        return jsonify({"status": "success", "report_id": rid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/activity", methods=["POST"])
def create_activity():
    data = request.get_json()
    rid = data.get("report_id")
    aid = str(uuid.uuid4())
    db.activities.insert_one({
        "activity_id": aid,
        "report_id": rid,
        "assessed_threats": data.get("assessed_threats", ""),
        "implemented_solution": data.get("implemented_solution", ""),
    })
    db.reports.update_one({"report_id": rid}, {"$push": {"activity_ids": aid}})
    return jsonify({"status": "success"})

@app.route("/activity/delete/<activity_id>", methods=["POST"])
def delete_activity(activity_id):
    act = db.activities.find_one({"activity_id": activity_id})
    if act:
        rid = act['report_id']
        db.activities.delete_one({"activity_id": activity_id})
        db.reports.update_one({"report_id": rid}, {"$pull": {"activity_ids": activity_id}})
        return redirect(url_for('report_details', report_id=rid))
    return "Not found", 404

