import socketio
import asyncio

sio = socketio.AsyncClient()

received_chunks = []

@sio.event
async def connect():
    print("Connected to Backend")
    print("Sending test query: 'Say hello in 5 words'...")
    await sio.emit('process_text', {'text': 'Say hello in 5 words', 'model': 'gemini-2.5-flash'})

@sio.event
async def chat_start(data):
    print(f"\n[Stream Started] Conversation ID: {data.get('conversation_id')}")

@sio.event
async def chat_chunk(data):
    chunk = data.get('chunk', '')
    received_chunks.append(chunk)
    print(chunk, end='', flush=True)

@sio.event
async def chat_end(data):
    full_text = "".join(received_chunks)
    print(f"\n\n[Stream Complete] Full response: {full_text}")
    print("AI Response Verified Successfully!")
    await sio.disconnect()

@sio.event
async def response(data):
    print(f"Received Response: {data}")
    if data.get('type') == 'ai_response':
        print("AI Response Verified!")
        await sio.disconnect()

@sio.event
async def disconnect():
    print("Disconnected from Backend")

async def main():
    try:
        await sio.connect('http://127.0.0.1:8000')
        await sio.wait()
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())
