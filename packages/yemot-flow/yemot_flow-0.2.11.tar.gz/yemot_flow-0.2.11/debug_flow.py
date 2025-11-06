#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת הבעיה - למה הקוד רץ שוב?
"""

from flask import Flask, request, Response
from yemot_flow import Flow

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
def welcome(call):
    """שלוחה ראשית - ברוכים הבאים"""
    print(f"DEBUG: welcome called with params: {call.params}")
    
    # בדיקה אם כבר יש קלט מהמשתמש
    digits = call.params.get("Digits")
    print(f"DEBUG: Digits received: {digits}")
    
    if digits:  # אם יש כבר קלט
        print(f"DEBUG: Processing user input: {digits}")
        if digits == "1":
            call.goto("/company-info")
        elif digits == "2":
            call.goto("/customer-service") 
        elif digits == "3":
            call.goto("/leave-message")
        elif digits == "0":
            call.goto("/")
        else:
            print(f"DEBUG: Invalid input: {digits}")
            call.play_message([('text', 'בחירה לא חוקית')])
            # לא קוראים שוב ל-read, רק חוזרים להתחלה
            call.goto("/")
    else:  # אם אין קלט - זו הפעם הראשונה
        print("DEBUG: First time - showing menu and asking for input")
        call.read(
            [('text', 'ברוכים הבאים למערכת ימות המשיח')],
            val_name="Digits",
            max_digits=1,
            digits_allowed="123456789"
        )

@flow.get("company-info")
def company_info(call):
    """מידע חברה"""
    call.play_message([('text', 'זה מידע על החברה')])
    call.read([('text', 'הקש כל מקש לחזרה')], max_digits=1)
    call.goto("/")

@flow.get("customer-service")
def customer_service(call):
    """שירות לקוחות"""
    call.play_message([('text', 'זה שירות לקוחות')])
    call.read([('text', 'הקש כל מקש לחזרה')], max_digits=1)
    call.goto("/")

@flow.get("leave-message")
def leave_message(call):
    """השארת הודעה"""
    call.play_message([('text', 'זה השארת הודעה')])
    call.read([('text', 'הקש כל מקש לחזרה')], max_digits=1)
    call.goto("/")

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    """נקודת כניסה לימות המשיח"""
    print(f"DEBUG: Request received: {request.values.to_dict()}")
    response = flow.handle_request(request.values.to_dict())
    print(f"DEBUG: Response sent: {response}")
    return Response(response, mimetype="text/plain; charset=utf-8")

@app.route("/")
def index():
    return """
    <h1>🐛 Debug Example</h1>
    <p>בדיקת הבעיה עם הקלט</p>
    <h3>בדיקות:</h3>
    <ul>
        <li><a href="/yemot?ApiCallId=test123">קריאה ראשונה (ללא קלט)</a></li>
        <li><a href="/yemot?ApiCallId=test123&Digits=1">קריאה שנייה (עם קלט 1)</a></li>
    </ul>
    """

if __name__ == "__main__":
    print("🐛 Debug mode - יemot Flow")
    print("📞 נסה: http://localhost:5000/yemot?ApiCallId=test123")
    print("📞 ואז: http://localhost:5000/yemot?ApiCallId=test123&Digits=1")
    app.run(host="0.0.0.0", port=5000, debug=True)