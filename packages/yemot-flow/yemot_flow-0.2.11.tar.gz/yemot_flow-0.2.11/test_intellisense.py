#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת IntelliSense וAutocomplete - אמור לעבוד עכשיו! 🎯
"""

from flask import Flask, request, Response
from yemot_flow import Flow

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
async def welcome(call):
    """
    עכשיו כשתקליד call. אמור להראות לך:
    - call.read()
    - call.play_message() 
    - call.goto()
    - call.hangup()
    """
    
    # בדוק שכשאתה מקליד call. מופיעות האופציות!
    digits = await call.read([
        ('text', 'ברוכים הבאים! הקש 1 למידע')
    ], max_digits=1, digits_allowed="1")
    
    if digits == "1":
        # גם כאן אמור לעבוד autocomplete
        call.goto("info")
    else:
        # ובכאן גם כן
        call.play_message([('text', 'תודה!')])
        call.hangup()

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    return Response(
        flow.handle_request(request.values.to_dict()),
        mimetype="text/plain; charset=utf-8"
    )

if __name__ == "__main__":
    print("🎯 בדיקת IntelliSense - נסה לקלדד call. ולראות את האופציות!")
    app.run(host="0.0.0.0", port=5010, debug=True)