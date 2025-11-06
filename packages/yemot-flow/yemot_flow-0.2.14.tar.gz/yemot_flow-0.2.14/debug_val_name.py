#!/usr/bin/env python3
"""בדיקה פשוטה של val_name בלי שרת"""

from yemot_flow import Flow, Call
from yemot_flow.actions import build_read

print("🔍 בדיקות val_name:")
print()

# בדיקה 1 - ישירות של build_read
print("1️⃣ בדיקה ישירה של build_read:")
result = build_read([('text', 'אנא הקש 1')], val_name="test_input1", max_digits=1, digits_allowed="1")
print(f"תוצאה: {result}")
print()

# בדיקה 2 - דרך Flow
print("2️⃣ בדיקה דרך Flow:")
flow = Flow()

@flow.get("")
async def test_func(call):
    return await call.read([('text', 'אנא הקש 1')], val_name="test_input1", max_digits=1, digits_allowed="1")

# דימוי הקריאה
import asyncio

async def run_test():
    call = Call({'ApiCallId': 'test123'}, flow=flow)
    try:
        await test_func(call)
    except Exception as e:
        if hasattr(e, 'response'):
            print(f"תוצאה מ-Flow: {e.response}")
        else:
            print(f"שגיאה: {e}")

asyncio.run(run_test())