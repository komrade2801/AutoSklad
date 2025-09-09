import asyncio
import websockets

LISTEN_PORT = 8765
PEER_URI = f"ws://192.168.101.154:{LISTEN_PORT}"

async def echo_server(websocket):  # убрали второй аргумент path
    async for message in websocket:
        print(f"Получено сообщение: {message}")
        await websocket.send(message)

async def send_messages(websocket):
    loop = asyncio.get_event_loop()
    while True:
        message = await loop.run_in_executor(None, input, "Введите сообщение для отправки: ")
        if message.lower() == "exit":
            print("Завершение работы")
            await websocket.close()
            break
        await websocket.send(message)
        print(f"Отправлено: {message}")

async def receive_messages(websocket):
    try:
        async for message in websocket:
            print(f"Ответ от партнёра: {message}")
    except websockets.ConnectionClosed:
        print("Соединение закрыто")

async def ws_client():
    async with websockets.connect(PEER_URI) as websocket:
        send_task = asyncio.create_task(send_messages(websocket))
        receive_task = asyncio.create_task(receive_messages(websocket))

        done, pending = await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

async def main():
    server = await websockets.serve(echo_server, "192.168.101.154", LISTEN_PORT)
    print(f"WebSocket-сервер запущен на ws://192.168.101.154:{LISTEN_PORT}")
    try:
        await ws_client()
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":    # исправлено
    asyncio.run(main())
