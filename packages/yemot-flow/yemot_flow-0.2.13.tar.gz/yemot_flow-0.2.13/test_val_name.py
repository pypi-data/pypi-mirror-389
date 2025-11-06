#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת val_name - אמור לעבוד עכשיו עם השם הנכון!
"""

from flask import Flask, request, Response
from yemot_flow import Flow, Call

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
async def test_val_name(call: Call):
    """בדיקה שval_name עובד נכון"""
    
    # בדיקה עם השם שאתה רוצה
    test_input1 = await call.read([
        ('text', 'אנא הקש 1')
    ], val_name="test_input1", max_digits=1, digits_allowed="1")
    
    # אמור להחזיר את הקלט שהתקבל
    call.play_message([('text', f'קיבלתי: {test_input1}')])

@flow.get("another_test")
async def another_test(call: Call):
    """עוד בדיקה עם שם אחר"""
    
    user_choice = await call.read([
        ('text', 'בחר אפשרות')
    ], val_name="user_choice", max_digits=1, digits_allowed="123")
    
    call.play_message([('text', f'בחרת: {user_choice}')])

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    """נקודת הכניסה לקריאות מימות המשיח"""
    print(f"📞 Request: {request.values.to_dict()}")
    response = flow.handle_request(request.values.to_dict())
    print(f"📤 Response: {response}")
    return Response(response, mimetype="text/plain; charset=utf-8")

@app.route("/")
def index():
    return """
    <h1>🎯 בדיקת val_name</h1>
    
    <h3>בדיקות:</h3>
    <ul>
        <li><a href="/yemot?ApiCallId=test123" target="_blank">בדיקה 1: צריך להציג test_input1 במקום val_1</a></li>
        <li><a href="/yemot?ApiCallId=test456&ApiExtension=another_test" target="_blank">בדיקה 2: צריך להציג user_choice</a></li>
    </ul>
    
    <p><strong>אמור לראות:</strong> השמות שאתה נתת במקום val_1</p>
    """

if __name__ == "__main__":
    print("🎯 בדיקת val_name - גרסה 0.2.12")
    app.run(host="0.0.0.0", port=5000, debug=True)