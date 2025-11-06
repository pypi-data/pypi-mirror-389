#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הדרך החדשה והנכונה - async/await כמו Node.js!
"""

from flask import Flask, request, Response
from yemot_flow import Flow

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
async def welcome(call):
    """שלוחה ראשית - הדרך החדשה! 🎯"""
    
    # פשוט וישיר - בדיוק כמו ב-Node.js!
    digits = await call.read([
        ('text', 'ברוכים הבאים למערכת ימות המשיח. למידע הקש 1, לתמיכה הקש 2, למכירות הקש 3, לסיום הקש 0')
    ], val_name="Digits", max_digits=1, digits_allowed="1230")
    
    # עכשיו פשוט עושים if/else רגיל - בלי בדיקות מסורבלות!
    if digits == "1":
        call.goto("info")  # עובר ישירות לשלוחה
    elif digits == "2":
        call.goto("support")  # עובר ישירות לשלוחה
    elif digits == "3":
        call.goto("sales")  # עובר ישירות לשלוחה
    elif digits == "0":
        call.play_message([('text', 'תודה שהתקשרת. להתראות!')])
        call.hangup()
    else:
        # לא אמור להגיע לכאן בגלל digits_allowed, אבל ליתר הביטחון
        call.play_message([('text', 'בחירה לא חוקית')])
        call.goto("")  # חזרה לתפריט

@flow.get("info")
async def info(call):
    """שלוחה מידע - גם כאן async"""
    
    choice = await call.read([
        ('text', 'זוהי שלוחה המידע. אנו חברת טכנולוגיה מובילה. לחזרה לתפריט הראשי הקש 0, לסיום השיחה הקש 9')
    ], val_name="InfoChoice", max_digits=1, digits_allowed="09")
    
    if choice == "0":
        call.goto("")  # חזרה לתפריט הראשי
    elif choice == "9":
        call.play_message([('text', 'תודה שהתקשרת. להתראות!')])
        call.hangup()

@flow.get("support")
async def support(call):
    """שלוחה תמיכה טכנית - עם אפשרויות מתקדמות"""
    
    choice = await call.read([
        ('text', 'תמיכה טכנית. לדיווח בעיה הקש 1, לשאלות כלליות הקש 2, לחזרה הקש 0')
    ], val_name="SupportChoice", max_digits=1, digits_allowed="012")
    
    if choice == "1":
        # דיווח בעיה עם הקלטה - עכשיו עם הודעה והקלטה באותה תגובה!
        issue_file = await call.read([
            ('text', 'התחל לתאר את הבעיה')
        ], mode="record",
           pre_message=[('text', 'אנא תאר את הבעיה לאחר הצפצוף')],
           path="support_issues",
           file_name=f"issue_{call.call_id}",
           max_length=120)  # 2 דקות
        
        call.play_message([
            ('text', 'תודה! הבעיה נרשמה במערכת'),
            ('text', f'מספר פנייה: {call.call_id[-6:]}'),  # 6 ספרות אחרונות
            ('text', 'נחזור אליך תוך 24 שעות')
        ])
        call.hangup()
        
    elif choice == "2":
        call.play_message([('text', 'לשאלות כלליות פנה למייל: support@example.com או לטלפון 03-1234567')])
        
        # שאלה אם רוצה לחזור או לסיים
        back_choice = await call.read([
            ('text', 'לחזרה לתפריט הראשי הקש 0, לסיום הקש 9')
        ], max_digits=1, digits_allowed="09")
        
        if back_choice == "0":
            call.goto("")
        else:
            call.hangup()
            
    elif choice == "0":
        call.goto("")  # חזרה לתפריט הראשי

@flow.get("sales")
async def sales(call):
    """שלוחה מכירות - עם איסוף פרטי לקוח"""
    
    choice = await call.read([
        ('text', 'מכירות. לקבלת הצעת מחיר הקש 1, למידע על מוצרים הקש 2, לחזרה הקש 0')
    ], val_name="SalesChoice", max_digits=1, digits_allowed="012")
    
    if choice == "1":
        # איסוף פרטים להצעת מחיר
        # איסוף שם - עם הודעה מקדימה באותה תגובה
        name = await call.read([
            ('text', 'אמור את שמך המלא')
        ], mode="stt", 
           lang="he-IL",
           pre_message=[('text', 'נשמח להכין לך הצעת מחיר מותאמת אישית')])
        
        # איסוף טלפון
        phone = await call.read([
            ('text', 'הקלד את מספר הטלפון שלך ולחץ סולמית')
        ], max_digits=12, min_digits=9, replace_char="#")
        
        # איסוף סוג המוצר המעניין
        product_type = await call.read([
            ('text', 'איזה מוצר מעניין אותך? למערכות IVR הקש 1, לפיתוח אפליקציות הקש 2, לייעוץ טכנולוגי הקש 3')
        ], max_digits=1, digits_allowed="123")
        
        # סיכום ושמירה
        products = {"1": "מערכות IVR", "2": "פיתוח אפליקציות", "3": "ייעוץ טכנולוגי"}
        selected_product = products.get(product_type, "כללי")
        
        call.play_message([
            ('text', f'תודה {name}'),
            ('text', f'נציג המכירות שלנו יחזור אליך לטלפון {phone[-4:]} בנוגע ל{selected_product}'),
            ('text', 'תוך 24 שעות')
        ])
        call.hangup()
        
    elif choice == "2":
        call.play_message([
            ('text', 'המוצרים שלנו: מערכות IVR מתקדמות, פיתוח אפליקציות מותאמות, ייעוץ טכנולוגי'),
            ('text', 'למידע מפורט בקר באתר שלנו או התקשר למכירות')
        ])
        
        back_choice = await call.read([
            ('text', 'לחזרה לתפריט הראשי הקש 0, לסיום הקש 9')
        ], max_digits=1, digits_allowed="09")
        
        if back_choice == "0":
            call.goto("")
        else:
            call.hangup()
            
    elif choice == "0":
        call.goto("")

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    """נקודת הכניסה לקריאות מימות המשיח"""
    return Response(
        flow.handle_request(request.values.to_dict()),
        mimetype="text/plain; charset=utf-8"
    )

@app.route("/")
def index():
    return """
    <h1>🎉 Yemot Flow v0.2.0 - הדרך החדשה!</h1>
    
    <h2>✅ מה השתנה:</h2>
    <ul>
        <li><strong>async/await</strong> - פשוט כמו Node.js</li>
        <li><strong>await call.read()</strong> - מחזיר קלט ישירות</li>
        <li><strong>קוד קריא</strong> - בלי בדיקות ידניות</li>
        <li><strong>תכונות מתקדמות</strong> - הקלטה, זיהוי דיבור</li>
    </ul>
    
    <h2>📞 בדיקות:</h2>
    <ul>
        <li><a href="/yemot?ApiCallId=test123">תפריט ראשי</a></li>
        <li><a href="/yemot?ApiCallId=test456&ApiExtension=sales">מכירות</a></li>
    </ul>
    
    <p><code>/yemot</code> - כוון את ימות המשיח לכתובת זו</p>
    """

if __name__ == "__main__":
    print("🎉 yemot-flow v0.2.0 - הדרך החדשה והנכונה!")
    print("📞 כוון את ימות המשיח לכתובת: http://your-server-ip:5010/yemot")
    print("✨ עכשיו עם async/await פשוט כמו Node.js!")
    
    app.run(host="0.0.0.0", port=5010, debug=True)