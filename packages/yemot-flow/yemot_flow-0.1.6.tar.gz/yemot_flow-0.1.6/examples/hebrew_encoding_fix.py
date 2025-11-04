#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
דוגמה לפתרון בעיית קידוד עברית ב-yemot-flow

הבעיה: טקסט עברי מקודד ב-URL encoding
הפתרון: שימוש בפרמטר url_encode=False או שימוש נכון במבנה המסרים
"""

from flask import Flask, request, Response
from yemot_flow import Flow

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
def welcome_wrong(call):
    """דרך שגויה - זה יוצר URL encoding של עברית"""
    # ⚠️ זה יוצר: read=t-%D7%91%D7%A8%D7%95%D7%9A...
    call.read(
        [('text', 'ברוכים הבאים למערכת ימות המשיח')],
        val_name="Digits",
        max_digits=1,
        digits_allowed="123456789"
    )
    # המשך הקוד...

@flow.get("solution1")  
def welcome_solution1(call):
    """פתרון 1: השבתת URL encoding"""
    call.read(
        [('text', 'ברוכים הבאים למערכת ימות המשיח')],
        val_name="Digits",
        max_digits=1,
        digits_allowed="123456789",
        url_encode=False  # 🔧 זה מונע את הקידוד
    )
    
    digits = call.params.get("Digits")
    if digits == "1":
        call.goto("/company-info")
    elif digits == "2":
        call.goto("/customer-service")

@flow.get("solution2")
def welcome_solution2(call):
    """פתרון 2: הפרדה בין הצגת הודעה לקבלת קלט"""
    
    # 🔧 תחילה הצג הודעה
    call.play_message([
        ('text', 'ברוכים הבאים למערכת ימות המשיח'),
        ('text', 'לחברה - הקש 1'),
        ('text', 'לשירות לקוחות - הקש 2'),
        ('text', 'להשארת הודעה - הקש 3')
    ])
    
    # אחר כך בקש קלט עם הודעה קצרה באנגלית או בלי טקסט
    call.read(
        [('text', 'Enter choice')],  # הודעה באנגלית
        val_name="Digits",
        max_digits=1,
        digits_allowed="123"
    )
    
    digits = call.params.get("Digits")
    if digits == "1":
        call.goto("/company-info")
    elif digits == "2":
        call.goto("/customer-service")
    elif digits == "3":
        call.goto("/leave-message")

@flow.get("solution3")
def welcome_solution3(call):
    """פתרון 3: שימוש בקובץ קול במקום טקסט"""
    
    call.play_message([
        ('file', 'welcome'),  # 🔧 קובץ קול במקום טקסט
        ('text', 'Press 1 for company info'),
        ('text', 'Press 2 for customer service')
    ])
    
    call.read(
        [('text', '')],  # הודעה ריקה או קצרה
        val_name="Digits", 
        max_digits=1,
        digits_allowed="12"
    )
    
    digits = call.params.get("Digits")
    if digits == "1":
        call.goto("/company-info")
    elif digits == "2":
        call.goto("/customer-service")

@flow.get("best-practice")
def welcome_best_practice(call):
    """השיטה המומלצת - הפרדה מלאה"""
    
    # 🏆 השיטה הטובה ביותר
    call.play_message([
        ('text', 'שלום וברכה! ברוכים הבאים למערכת שירות הלקוחות'),
        ('text', 'למידע כללי על החברה - הקש 1'),  
        ('text', 'לשירות לקוחות - הקש 2'),
        ('text', 'להשארת הודעה - הקש 3'),
        ('text', 'לחזרה לתפריט הראשי - הקש 0')
    ])
    
    # בקשת קלט פשוטה
    call.read(
        [('text', 'הקש את בחירתך')],
        val_name="Digits",
        max_digits=1, 
        digits_allowed="0123",
        sec_wait=10,
        amount_attempts=3
    )
    
    digits = call.params.get("Digits")
    if digits == "1":
        call.goto("/company-info")
    elif digits == "2":
        call.goto("/customer-service") 
    elif digits == "3":
        call.goto("/leave-message")
    elif digits == "0":
        call.goto("/")
    else:
        # אם לא הוקש כלום או בחירה לא חוקית
        call.play_message([('text', 'לא הובנה בחירתך')])
        call.goto("/best-practice")  # חזרה לתפריט

@flow.get("company-info")
def company_info(call):
    """מידע על החברה"""
    call.play_message([
        ('text', 'אנחנו חברת טכנולוגיה מובילה'),
        ('text', 'מתמחים בפתרונות IVR מתקדמים'),
        ('text', 'לחזרה לתפריט הראשי - הקש כל מקש')
    ])
    
    call.read([('text', '')], max_digits=1)
    call.goto("/best-practice")

@flow.get("customer-service")
def customer_service(call):
    """שירות לקוחות"""
    call.play_message([
        ('text', 'שירות לקוחות'),
        ('text', 'כרגע כל הנציגים עסוקים'),
        ('text', 'אנא השאר הודעה ונחזור אליך')
    ])
    call.goto("/leave-message")

@flow.get("leave-message")
def leave_message(call):
    """השארת הודעה"""
    call.play_message([('text', 'אנא השאר הודעתך לאחר הצפצוף')])
    
    call.read(
        [('text', 'החל הקלטה')],
        mode="record",
        path="messages",
        file_name=f"msg_{call.call_id}",
        max_length=60,
        save_on_hangup=True
    )
    
    call.play_message([
        ('text', 'תודה! ההודעה נקלטה בהצלחה'),
        ('text', 'נחזור אליך בהקדם')
    ])
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
    <h1>🔧 פתרון בעיית קידוד עברית</h1>
    <p>דוגמאות לפתרון הבעיה:</p>
    <ul>
        <li><strong>הבעיה:</strong> URL encoding של טקסט עברית</li>
        <li><strong>פתרון 1:</strong> url_encode=False</li>
        <li><strong>פתרון 2:</strong> הפרדת הצגה מקבלת קלט</li>
        <li><strong>פתרון 3:</strong> שימוש בקבצי קול</li>
        <li><strong>מומלץ:</strong> השיטה הטובה ביותר</li>
    </ul>
    <p>התחל עם: <code>/best-practice</code></p>
    """

if __name__ == "__main__":
    print("🔧 פתרון בעיית קידוד עברית - יemot Flow")
    print("📞 כוון לכתובת: http://localhost:5000/yemot")
    print("🏆 נסה את הנתיב: /best-practice")
    app.run(host="0.0.0.0", port=5000, debug=True)