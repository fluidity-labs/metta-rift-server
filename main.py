import asyncio

from websockets import ConnectionClosedOK
from websockets.asyncio.server import serve, ServerConnection
from hyperon import MeTTa


async def handle_connection(websocket: ServerConnection):
    # Initialize a new MeTTa (Hyperon) instance for the connected user
    metta = MeTTa()

    # Send a welcome message
    await websocket.send("Welcome! MeTTa (Hyperon) instance initialized.")

    async for message in websocket:
        try:
            if message == "exit":
                await websocket.send("Closing connection...")
                await websocket.close()
            # Process incoming messages and evaluate them using MeTTa
            result = metta.run(message)
            # Send the result back to the client
            await websocket.send(f"Result: {result}")
        except ConnectionClosedOK:
            print("Connection closed.")


async def main():
    async with serve(handle_connection, "localhost", 6789) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
