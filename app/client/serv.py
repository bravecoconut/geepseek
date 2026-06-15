# app/client/serv.py
import json
from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)


@app.route("/chat/<session_id>")
def home(session_id):
    return render_template("chat.html", session_id=session_id)

@app.route("/chat/new")
def new_chat():                          # ✅ this is missing
    return render_template("chat.html", session_id="new")

@app.route('/chat/')
@app.route('/chat')
def redirect_to_new():
    return redirect(url_for('new_chat')) # references new_chat — needs the route above


@app.route("/")
def root():
    return redirect(url_for('new_chat'))
    
if __name__ == "__main__":
    app.run(debug=True, port=5001)

