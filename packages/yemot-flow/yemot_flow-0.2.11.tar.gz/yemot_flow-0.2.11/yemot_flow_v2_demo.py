#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎉 yemot-flow החדש - בדיוק כמו

עכשיו אפשר לכתוב קוד פשוט וקריא עם async/await
"""

from flask import Flask, request, Response
from yemot_flow import Flow

app = Flask(__name__)
flow = Flow(print_log=True)

@flow.get("")
async def welcome(call):
    """שלוחה ראשית 🎯"""
    
    choice = await call.read([
        ('text', 'ברוכים הבאים למערכת ימות המשיח. לחברה הקש 1, לשירות הקש 2, להודעה הקש 3')
    ], max_digits=1, digits_allowed="123")
    
    # עכשיו אפשר פשוט לעשות if/else רגיל!
    if choice == "1":
        call.goto("/company-info")
    elif choice == "2":
        call.goto("/customer-service")
    elif choice == "3":
        call.goto("/leave-message")
    else:
        # בחירה לא חוקית
        call.play_message([('text', 'בחירה לא חוקית')])
        call.goto("/")  # חזרה לתפריט

@flow.get("company-info")
async def company_info(call):
    """מידע על החברה"""
    call.play_message([
        ('text', 'אנחנו חברת yemot-flow'),
        ('text', 'מתמחים בפיתוח מערכות IVR בפייתון'),
        ('text', 'עכשיו עם API פשוט כמו ב-Node.js!')
    ])
    
    # חכה לקלט כלשהו
    await call.read([('text', 'הקש כל מקש לחזרה')], max_digits=1)
    call.goto("/")  # חזרה לתפריט ראשי

@flow.get("customer-service")
async def customer_service(call):
    """שירות לקוחות עם תת-תפריט"""
    
    choice = await call.read([
        ('text', 'שירות לקוחות. לדיווח בעיה הקש 1, לשאלות כלליות הקש 2, לחזרה הקש 0')
    ], max_digits=1, digits_allowed="012")
    
    if choice == "1":
        # דיווח בעיה
        call.play_message([('text', 'אנא תאר את הבעיה לאחר הצפצוף')])
        
        file_path = await call.read([('text', 'התחל תיאור הבעיה')], 
                                   mode="record", 
                                   max_length=120,
                                   path="issues",
                                   file_name=f"issue_{call.call_id}")
        
        call.play_message([
            ('text', f'הבעיה נרשמה בקובץ {file_path}'),
            ('text', 'נחזור אליך בהקדם')
        ])
        call.hangup()
        
    elif choice == "2":
        # שאלות כלליות
        call.play_message([('text', 'לשאלות כלליות פנה למייל: info@yemot-flow.com')])
        await call.read([('text', 'הקש כל מקש')], max_digits=1)
        call.goto("/")
        
    elif choice == "0":
        call.goto("/")  # חזרה

@flow.get("leave-message")
async def leave_message(call):
    """השארת הודעה כללית"""
    
    call.play_message([('text', 'השארת הודעה. אנא השאר את הודעתך לאחר הצפצוף')])
    
    # הקלטת ההודעה
    message_file = await call.read([('text', 'התחל הקלטת ההודעה')],
                                  mode="record",
                                  max_length=90,
                                  path="messages",
                                  file_name=f"message_{call.call_id}",
                                  save_on_hangup=True)
    
    call.play_message([
        ('text', 'תודה רבה!'),
        ('text', f'ההודעה נשמרה בקובץ {message_file}'),
        ('text', 'נשמח לחזור אליך בהקדם')
    ])
    call.hangup()

# דוגמה למשהו מתקדם יותר - לולאה
@flow.get("advanced-demo")  
async def advanced_demo(call):
    """דוגמה מתקדמת - לולאה עם מונה"""
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        attempts += 1
        
        choice = await call.read([
            ('text', f'ניסיון {attempts} מתוך {max_attempts}. הקש 1 להצלחה או 2 לניסיון נוסף')
        ], max_digits=1, digits_allowed="12")
        
        if choice == "1":
            call.play_message([('text', 'מצוין! הצלחת')])
            call.hangup()
            return
        elif choice == "2":
            if attempts < max_attempts:
                call.play_message([('text', 'בסדר, ננסה שוב')])
            else:
                call.play_message([('text', 'מצטער, נגמרו הניסיונות')])
                call.hangup()
                return

# דוגמה לאיסוף נתונים מורכב
@flow.get("collect-data")
async def collect_data(call):
    """איסוף נתונים מהמשתמש"""
    
    call.play_message([('text', 'איסוף נתונים. אנא ענה על השאלות הבאות')])
    
    # איסוף שם
    name = await call.read([('text', 'אמור את שמך הפרטי')], 
                          mode="stt", 
                          lang="he-IL")
    
    # איסוף גיל
    age = await call.read([('text', 'הקש את הגיל שלך')], 
                         max_digits=2, 
                         min_digits=1,
                         digits_allowed="0123456789")
    
    # איסוף טלפון
    phone = await call.read([('text', 'הקש את מספר הטלפון שלך ולחץ סולמית')],
                           max_digits=12,
                           min_digits=9, 
                           replace_char="#")
    
    # סיכום
    call.play_message([
        ('text', f'תודה {name}'),
        ('text', f'בן {age}'),
        ('text', f'טלפון שמספרו מסתיים ב-{phone[-4:]}'),
        ('text', 'הנתונים נשמרו במערכת')
    ])
    call.hangup()

@app.route("/yemot", methods=["GET", "POST"]) 
def yemot_entry():
    """נקודת כניסה לימות המשיח"""
    return Response(
        flow.handle_request(request.values.to_dict()),
        mimetype="text/plain; charset=utf-8"
    )

@app.route("/")
def index():
    return """
    <h1>🎉 yemot-flow v2.0 - כמו Node.js!</h1>
    
    <h2>✨ מה חדש:</h2>
    <ul>
        <li>✅ <strong>קוד קריא</strong> - אין יותר בדיקות if/else מורכבות</li>
        <li>✅ <strong>await call.read()</strong> - מחזיר את הקלט ישירות</li>
        <li>✅ <strong>לולאות ותנאים</strong> - עובד כמו קוד רגיל</li>
        <li>✅ <strong>איסוף נתונים פשוט</strong> - אין יותר state management ידני</li>
    </ul>
    
    <h2>📝 דוגמת קוד:</h2>
    <pre><code>@flow.get("")
async def welcome(call):
    choice = await call.read([('text', 'ברוכים הבאים')], max_digits=1)
    
    if choice == "1":
        call.goto("/info")
    elif choice == "2":
        call.goto("/support")
</code></pre>

    <h2>🧪 דוגמאות לבדיקה:</h2>
    <ul>
        <li><a href="/yemot?ApiCallId=test123">תפריט ראשי</a></li>
        <li><a href="/yemot?ApiCallId=test456&ApiExtension=advanced-demo">דוגמה מתקדמת</a></li>
        <li><a href="/yemot?ApiCallId=test789&ApiExtension=collect-data">איסוף נתונים</a></li>
    </ul>
    """

if __name__ == "__main__":
    print("🎉 yemot-flow v2.0 - async/await כמו Node.js!")
    print("📞 כוון את ימות המשיח ל: http://localhost:5000/yemot")
    print("✨ עכשיו עם API פשוט וקריא!")
    
    app.run(host="0.0.0.0", port=5000, debug=True)