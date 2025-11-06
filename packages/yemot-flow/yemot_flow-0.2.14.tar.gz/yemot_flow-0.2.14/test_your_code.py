#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקה של הקוד שלך - צריך לעבוד מושלם
"""

from flask import Flask, request, Response
from yemot_flow import Flow, Call

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("test")
async def test_flow(call: Call):
    """נקודת בדיקה פשוטה"""
    test_input1 = await call.read([('text', 'אנא הקש 1')], val_name="test_input1", max_digits=1, digits_allowed="1")
    
    # בואו נוסיף משהו שיראה שזה עבד
    call.play_message([('text', f'קיבלתי: {test_input1}')])

@flow.get("")
async def main_menu(call: Call):
    """תפריט ראשי שיכוון לבדיקה"""
    choice = await call.read([('text', 'לבדיקה הקש 1')], val_name="main_choice", max_digits=1, digits_allowed="1")
    
    if choice == "1":
        call.goto("test")

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    print(f"📞 Request: {request.values.to_dict()}")
    response = flow.handle_request(request.values.to_dict())
    print(f"📤 Response: {response}")
    return Response(response, mimetype="text/plain; charset=utf-8")

@app.route("/")
def index():
    return """
    <h1>🧪 בדיקת הקוד שלך</h1>
    
    <h3>בדיקות:</h3>
    <ul>
        <li><a href="/yemot?ApiCallId=test123" target="_blank">תפריט ראשי</a></li>
        <li><a href="/yemot?ApiCallId=test123&ApiExtension=test" target="_blank">בדיקה ישירה של test</a></li>
    </ul>
    """

if __name__ == "__main__":
    print("🧪 בדיקת הקוד שלך")
    app.run(host="0.0.0.0", port=5002, debug=True)