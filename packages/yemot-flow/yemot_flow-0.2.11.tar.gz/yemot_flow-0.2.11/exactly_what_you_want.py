#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
דוגמה מדויקת למה שאתה רוצה
"""

from flask import Flask, request, Response
from yemot_flow import Flow

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
def welcome(call):
    """שלוחה ראשית - בדיוק כמו שאתה רוצה"""
    
    # 🔍 בודקים אם יש קלט מהמשתמש
    digits = call.params.get("Digits")
    
    if digits:
        # 🎯 יש קלט - מציגים הודעה בהתאם
        if digits == "1":
            call.play_message([('text', 'העברתך לשלוחה מידע')])
        elif digits == "2":
            call.play_message([('text', 'העברתך לשלוחה תמיכה טכנית')])
        elif digits == "3":
            call.play_message([('text', 'העברתך לשלוחה מכירות')])
        elif digits == "0":
            call.play_message([('text', 'תודה שהתקשרת. להתראות!')])
        else:
            call.play_message([('text', 'בחירה לא חוקית')])
    else:
        # 🎵 אין קלט - זו הפעם הראשונה
        call.read(
            [('text', 'ברוכים הבאים למערכת ימות המשיח')],
            val_name="Digits",
            max_digits=1,
            digits_allowed="123456789"
        )

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    print(f"📞 Request: {request.values.to_dict()}")
    response = flow.handle_request(request.values.to_dict())
    print(f"📤 Response: {response}")
    return Response(response, mimetype="text/plain; charset=utf-8")

@app.route("/")
def index():
    return """
    <h1>🎯 בדיוק מה שאתה רוצה</h1>
    <h3>בדיקות:</h3>
    <ul>
        <li><a href="/yemot?ApiCallId=test123" target="_blank">קריאה 1: יציג תפריט</a></li>
        <li><a href="/yemot?ApiCallId=test123&Digits=1" target="_blank">קריאה 2: רק הודעה על מידע</a></li>
        <li><a href="/yemot?ApiCallId=test123&Digits=2" target="_blank">קריאה 3: רק הודעה על תמיכה</a></li>
        <li><a href="/yemot?ApiCallId=test123&Digits=3" target="_blank">קריאה 4: רק הודעה על מכירות</a></li>
    </ul>
    
    <h3>התוצאות הצפויות:</h3>
    <ul>
        <li><strong>קריאה 1:</strong> <code>read=t-ברוכים הבאים...</code></li>
        <li><strong>קריאה 2:</strong> <code>id_list_message=t-העברתך לשלוחה מידע</code></li>
        <li><strong>קריאה 3:</strong> <code>id_list_message=t-העברתך לשלוחה תמיכה טכנית</code></li>
        <li><strong>קריאה 4:</strong> <code>id_list_message=t-העברתך לשלוחה מכירות</code></li>
    </ul>
    """

if __name__ == "__main__":
    print("🎯 מה שאתה רוצה - yemot Flow")
    print("📞 נסה: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)