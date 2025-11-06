# -----------------------------
# File: README.md
# -----------------------------
# yemot_flow – ספריית Flow לפייתון עבור ימות המשיח

<p align="right">גרסה 0.2 • רישיון MIT</p>

**yemot_flow** (להלן *Yemot Flow*) מאפשרת לכתוב מערכות IVR מורכבות ל‑[ימות המשיח](https://f2.freeivr.co.il) בפייתון — בקוד נקי, רציף, וללא כתיבת מחרוזות API ידנית. הספרייה שואבת השראה מה‑Node‑js ‎`yemot-router2` ומספקת ממשק דומה למפתחים בפייתון.

---

## תכונות מרכזיות

| ✔︎ | תכונה | פירוט |
|---|---|---|
| קוד לינארי | כיתות **Flow ו‑Call** מחזיקות מצב (state) בין קריאות HTTP, כך שהקוד שלך נראה כמו סקריפט רציף אחד. |
| אינטגרציה קלה | עובד עם **Flask** או **FastAPI** בכמה שורות קוד. |
| API קריא | מתודות גבוהות‑רמה (`read`, `play_message`, `goto`, `hangup`) שבונות אוטומטית את תגובת הטקסט לימות. |
| ניהול תקלות | `timeout` מובנה לניקוי שיחות תקועות, ולכידת חריגות עם הודעת ברירת‑מחדל למתקשר. |
| דוגמאות וטסטים | קוד מלא לדוגמה (Flask / FastAPI) ובדיקות pytest בסיסיות לשימוש מיידי. |

---

## התקנה

```bash
pip install yemot-flow flask            # עבור Flask
# או:
pip install yemot-flow fastapi uvicorn  # עבור FastAPI
```

> הספרייה דורשת Python 3.10 ומעלה.

---

## דוגמת Flask מהירה

```python
from flask import Flask, request, Response
from yemot_flow import Flow

app = Flask(__name__)
flow = Flow(print_log=True)  # הדפסת לוג לפיתוח

@flow.get("")  # שלוחה ראשית /
def welcome(call):
    call.play_message([("text", "שלום וברכה! להמשך – הקש 1")])
    call.read([("text", "הקש 1 להמשך")], max_digits=1, digits_allowed="1")
    if call.params.get("Digits") == "1":
        call.goto("/thanks")

@flow.get("thanks")
def thanks(call):
    call.play_message([("text", "תודה ולהתראות")])
    call.hangup()

@app.route("/yemot", methods=["GET", "POST"])
def yemot_entry():
    resp = flow.handle_request(request.values.to_dict())
    return Response(resp, mimetype="text/plain; charset=utf-8")

if __name__ == "__main__":
    app.run(port=5000)
```

- כוון ב‑ימות את כתובת API ל‑`http://<server‑ip>:5000/yemot`.
- הפעל את הסקריפט ושמע את ההודעה בטלפון.

---

## דוגמת FastAPI מהירה

```python
from fastapi import FastAPI, Request, Response
from yemot_flow import Flow

app = FastAPI()
flow = Flow()

@flow.get("")
def root(call):
    call.play_message([("text", "שלום מ‑FastAPI!")])
    call.hangup()

@app.api_route("/yemot", methods=["GET", "POST"])
async def yemot_entry(request: Request):
    params = await request.form() if request.method == "POST" else request.query_params
    resp = flow.handle_request(dict(params))
    return Response(resp, media_type="text/plain; charset=utf-8")
```

הרץ עם `uvicorn main:app --host 0.0.0.0 --port 8000`.

---

## מבנה הפרויקט

```text
yemot_flow/
├── __init__.py      # ייצוא Flow ו‑Call
├── flow.py          # ניהול שיחות ומיפוי שלוחות → handlers
├── call.py          # אובייקט שיחה: read / play_message / goto וכו׳
├── actions.py       # מחוללי‑טקסט נמוכי‑רמה לתגובת API
└── utils.py         # עזר: קידוד URL, ניקוי תווים, timestamp
examples/
├── flask_app_example.py
└── fastapi_app_example.py
tests/
└── test_basic_flow.py
pyproject.toml        # מידע התקנה ותלויות
```

---

## API עיקרי

### Flow
```python
flow = Flow(timeout=30000, print_log=True)
flow.get("/sales")(sales_handler)  # רישום שלוחה
```
- **timeout** – מילישניות לפני ששיחה לא פעילה נמחקת (ברירת‑מחדל: 30 שניות).
- **print_log** – הפעלת לוג INFO אוטומטי לניפוי שגיאות.

### Call (עבור כל שיחה)
| מתודה | שימוש |
|-------|--------|
| `play_message(messages)` | השמעת הודעות (טקסט, קובץ, ספרות, מספר וכו׳). |
| `read(messages, mode="tap", **options)` | בקשת קלט מהמשתמש: מקשים (`tap`), זיהוי דיבור (`stt`) או הקלטה (`record`). |
| `goto(folder)` | מעבר לשלוחה אחרת או `hangup` לניתוק. |
| `hangup()` | קיצור ל‑`goto("hangup")`. |

### פורמט הודעה
```python
("text", "שלום")
("file", "welcome")
("digits", "1234")
```

---

## ניהול שיחות (State)
- מזהה השיחה **`ApiCallId`** משמש כמפתח באובייקט `active_calls`‎.
- כל שיחה מחזיקה את `last_activity_ms`; אם עובר זמן **`timeout`** ללא תנועה —
  השיחה נמחקת מזיכרון.
- בקשת `hangup=yes` מוחקת מיד את השיחה.

---

## בדיקות
```
pytest -q tests
```
הבדיקות מדמות קריאה מ‑Yemot ומוודאות שהתגובה בפורמט תקין.

---

## תוכנית פיתוח עתידית
- ✨ תמיכה מלאה ב‑`stt` ו‑`record` (זיהוי דיבור והקלטה).
- ✨ ממשק פלאגינים (סליקת אשראי, TTS חיצוני, WebSocket Debug).
- ✨ CLI ליצירת פרויקט חדש במהירות.

תרומות, Pull‑Requests ושאלות–בפורום ימות או ב‑GitHub. 🙌

---

## רישיון

```
MIT License – עשה כרצונך, קרדיט יתקבל באהבה.
```