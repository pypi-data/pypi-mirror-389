#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
✅ בדיקת IntelliSense עם Type Hints - אמור לעבוד עכשיו! 🎯
"""

from flask import Flask, request, Response
from yemot_flow import Flow, Call

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
async def welcome(call: Call):
    """
    🎯 עכשיו כשתקליד call. אמור להראות לך את כל האופציות!
    
    נסה להקליד:
    - call.read(  ← אמור להראות את כל הפרמטרים
    - call.play_  ← autocomplete ל-play_message
    - call.goto(  ← אמור להראות שזה מקבל folder: str
    - call.hangup()  ← אמור להראות שזה לא מקבל פרמטרים
    """
    
    # 🔍 כאן נסה להקליד call. ולראות את הרשימה
    digits = await call.read([
        ('text', 'הקש מספר')
    ], max_digits=1, digits_allowed="123")
    
    # גם כאן נסה call.
    if digits == "1":
        call.goto("info")
    else:
        call.play_message([('text', 'תודה')])
        call.hangup()

@flow.get("info") 
async def info_page(call: Call):
    """גם כאן אמור לעבוד autocomplete"""
    
    # נסה להקליד call. כאן
    choice = await call.read([
        ('text', 'זוהי דף המידע')
    ])
    
    call.goto("")

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    return Response(
        flow.handle_request(request.values.to_dict()),
        mimetype="text/plain; charset=utf-8"
    )

if __name__ == "__main__":
    print("🎯 בדיקת IntelliSense עם Type Hints")
    print("נסה להקליד call. בפונקציות ולראות את ההשלמות!")
    app.run(host="0.0.0.0", port=5010, debug=True)