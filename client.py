import asyncio, websockets, json

SERVER = "ws://192.168.0.53:8000"

async def run():
    ws = await websockets.connect(SERVER)

    msg = {
        "command": "motor_control",
        "payload": {"left": 20, "right": 50}
    }

    msg = {
        "command": "yolo_detection",
        "payload": {"label": "cat", "confidence": 0.92}
    }
    await ws.send(json.dumps(msg))

asyncio.run(run())