import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ):
    print(f"[Socket] Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"[Socket] Client disconnected: {sid}")


@sio.event
async def join_room(sid, data):
    room = data.get("room")
    if room:
        await sio.enter_room(sid, room)


@sio.event
async def send_message(sid, data):
    room = data.get("room")
    if room:
        await sio.emit("receive_message", data, room=room)
