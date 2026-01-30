import socketio
import asyncio

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("✅ Connected to Backend")
    print("Sending 'hello'...")
    await sio.emit('process_text', {'text': 'hello', 'model': 'gemini-2.5-flash-preview-09-2025'})

@sio.event
async def response(data):
    print(f"📩 Received Response: {data}")
    if data.get('type') == 'ai_response':
        print("✅ AI Response Verified!")
        await sio.disconnect()

@sio.event
async def disconnect():
    print("Disconnected")

async def main():
    try:
        await sio.connect('http://127.0.0.1:8000')
        await sio.wait()
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())
