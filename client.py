import asyncio, websockets, json

SERVER = "ws://192.168.0.53:8000"

async def run(t):
    ws = await websockets.connect(SERVER)
    await ws.send(json.dumps({
        "command": "register",
        "payload": {"id": "pi3"}
    }))

    if t == 0:
        msg = {
            "command": "stop_control",
        }
    elif t == 1:
        msg = {
            "command": "motor_control",
            "payload": {"left": 50, "right": 50}
        }
    elif t == 2:
        msg = {
            "command": "yolo_detection",
            "payload": {"label": "knife", "confidence": 0.92}
        }

    await ws.send(json.dumps(msg))

asyncio.run(run(2))