import asyncio
import websockets
import queue

input_queue = None  # Global queue reference

async def handle_connection(websocket, path):
    global input_queue
    async for message in websocket:
        print(f"Received from Web: {message}")
        if input_queue is not None:
            input_queue.put(message)  # Send to terminal program

def start_websocket_server(queue_ref):
    global input_queue
    input_queue = queue_ref
    print("WebSocket Server Started at ws://localhost:8765")

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)  # Set this as the current thread's loop

    # Create the server coroutine
    start_server = websockets.serve(handle_connection, "0.0.0.0", 8765)

    try:
        # Run the server
        server = loop.run_until_complete(start_server)
        print("WebSocket server is running...")
        loop.run_forever()
    except Exception as e:
        print(f"WebSocket server error: {e}")
    finally:
        server.close()
        rprint("WebSocket server closed.")
        loop.run_until_complete(server.wait_closed())
        loop.close()