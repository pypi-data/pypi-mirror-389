#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הדרך הנכונה לכתוב את הקוד
"""

from flask import Flask, request, Response
from yemot_flow import Flow

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
def welcome(call):
    """שלוחה ראשית - הדרך הנכונה"""
    
    # 🔍 קודם בודקים אם יש כבר קלט מהמשתמש
    digits = call.params.get("Digits")
    
    if digits:
        # 🎯 יש קלט - מעבדים אותו ומציגים הודעה
        if digits == "1":
            call.play_message([('text', 'העברתך לשלוחה מידע')])
        elif digits == "2":
            call.play_message([('text', 'העברתך לשלוחה תמיכה טכנית')])
        elif digits == "3":
            call.play_message([('text', 'העברתך לשלוחה מכירות')])
        elif digits == "0":
            call.play_message([('text', 'תודה שהתקשרת. להתראות!')])
        else:
            # בחירה לא חוקית - חוזרים להתחלה
            call.play_message([('text', 'בחירה לא חוקית')])
    else:
        # 🎵 אין קלט - זו הפעם הראשונה, מציגים תפריט
        call.read(
            [('text', 'ברוכים הבאים למערכת ימות המשיח')],
            val_name="Digits",
            max_digits=1,
            digits_allowed="123456789"
        )

@flow.get("company-info")
def company_info(call):
    """מידע חברה"""
    digits = call.params.get("Digits")
    
    if digits:
        call.goto("/")  # חזרה לתפריט הראשי
    else:
        call.play_message([('text', 'זה מידע על החברה שלנו')])
        call.read([('text', 'הקש כל מקש לחזרה לתפריט הראשי')], 
                  val_name="Digits", max_digits=1)

@flow.get("customer-service")
def customer_service(call):
    """שירות לקוחות"""
    digits = call.params.get("Digits")
    
    if digits:
        call.goto("/")  # חזרה לתפריט הראשי
    else:
        call.play_message([('text', 'ברוכים הבאים לשירות לקוחות')])
        call.read([('text', 'הקש כל מקש לחזרה')], 
                  val_name="Digits", max_digits=1)

@flow.get("leave-message")
def leave_message(call):
    """השארת הודעה"""
    call.play_message([('text', 'אנא השאר הודעתך לאחר הצפצוף')])
    call.read(
        [('text', 'התחל הקלטה')],
        mode="record",
        path="messages",
        file_name=f"msg_{call.call_id}",
        max_length=60
    )
    call.play_message([('text', 'תודה! ההודעה נקלטה')])
    call.hangup()

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    return Response(
        flow.handle_request(request.values.to_dict()),
        mimetype="text/plain; charset=utf-8"
    )

@app.route("/")
def index():
    return """
    <h1>✅ הדרך הנכונה</h1>
    <h3>בדיקות:</h3>
    <ul>
        <li><a href="/yemot?ApiCallId=test123">קריאה 1: יציג תפריט</a></li>
        <li><a href="/yemot?ApiCallId=test123&Digits=1">קריאה 2: יעבור לחברה</a></li>
        <li><a href="/yemot?ApiCallId=test123&ApiExtension=company-info">קריאה 3: יציג מידע חברה</a></li>
        <li><a href="/yemot?ApiCallId=test123&ApiExtension=company-info&Digits=1">קריאה 4: יחזור לתפריט</a></li>
    </ul>
    """

if __name__ == "__main__":
    print("✅ הדרך הנכונה - yemot Flow")
    app.run(host="0.0.0.0", port=5000, debug=True)