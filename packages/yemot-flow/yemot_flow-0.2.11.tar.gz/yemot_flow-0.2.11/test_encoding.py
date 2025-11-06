#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקה מהירה של הפתרון החדש
"""

from flask import Flask, request, Response
from yemot_flow import Flow

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
def test_encoding(call):
    """בדיקת הפרמטר החדש"""
    
    # בדיקה 1: עם URL encoding (ברירת מחדל)
    print("=== TEST 1: With URL encoding (default) ===")
    call.play_message([('text', 'ברוכים הבאים')])
    
    # בדיקה 2: ללא URL encoding
    print("=== TEST 2: Without URL encoding ===")
    call.play_message([('text', 'ברוכים הבאים')], url_encode=False)
    
    # בדיקה 3: read עם URL encoding
    print("=== TEST 3: Read with URL encoding ===")
    call.read([('text', 'הקש מקש')], max_digits=1)
    
    # בדיקה 4: read ללא URL encoding
    print("=== TEST 4: Read without URL encoding ===") 
    call.read([('text', 'הקש מקש')], max_digits=1, url_encode=False)
    
    call.hangup()

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    return Response(
        flow.handle_request(request.values.to_dict()),
        mimetype="text/plain; charset=utf-8"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)