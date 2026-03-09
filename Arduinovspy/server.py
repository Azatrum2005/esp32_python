import asyncio
import websockets

async def handle_connection(websocket):
    print(f"--- Phone Connected! ({websocket.remote_address}) ---")
    try:
        async for message in websocket:
            print(f"Received: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("--- Connection Closed by Phone ---")

async def main():
    # 0.0.0.0 listens on all available network interfaces (Wi-Fi, Ethernet)
    print("Starting WebSocket Server on port 8765...")
    print("Waiting for connection...")
    async with websockets.serve(handle_connection, "0.0.0.0", 8765):
        await asyncio.get_running_loop().create_future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")