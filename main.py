import asyncio
import json
import itertools

from websockets import ConnectionClosedOK
from websockets.asyncio.server import serve, ServerConnection
from hyperon import MeTTa

MESSAGE_TYPE_SYSTEM: str = "SYSTEM"
MESSAGE_TYPE_USER: str = "USER"

async def handle_connection(websocket: ServerConnection):
    # Initialize a new MeTTa (Hyperon) instance for the connected user
    metta = MeTTa()
    metta.run("""
        (: valley1 Location) ; sets the type of valley1 to Location
        (= (Location valley1 name) "Duskrend Valley") ; sets the name of valley1
        
        (: glade1 Location)
        (= (Location glade1 name) "Emberbloom Glade ")
        
        (: city1 Location)
        (= (Location city1 name) "Ironspire")
        
        (: cavern1 Location)
        (= (Location cavern1 name) "Gloomshear Cavern")
        
        (: road1 Location)
        (= (Location road1 name) "Ashen Hollow Road")
        
        (: road2 Location)
        (= (Location road2 name) "Veilshade Path")
        
        (: road3 Location)
        (= (Location road3 name) "Bloodthorn Trail")
        
        (: road4 Location)
        (= (Location road4 name) "Echo Run")
        
        (: road5 Location)
        (= (Location road5 name) "Iron Hollow Way")
        
        (= (Route valley1 road1)) ; creates a connection between two locations
        (= (Route road1 city1))
        (= (Route city1 road2))
        (= (Route road2 glade1))
        (= (Route road5 road4))
        (= (Route road4 road3))
        (= (Route road3 cavern1))
        (= (Route city1 road4))
        
        (: hero Character) ; sets the type of hero to Character
        (= (Character hero name) "John") ; sets the name of hero
        (= (Character hero hp) 100)
        (= (Character hero speed) 2)
        (= (Character hero attack) 5)
        (= (Character hero defense) 10)
        (= (Character hero location) city1)
        
        (: goblin Monster) ; sets the type of goblin to Monster
        (= (Monster goblin name) "Grimzle Snaggletooth") ; sets the name of goblin
        (= (Monster goblin hp) 20)
        (= (Monster goblin speed) 5)
        (= (Monster goblin attack) 2)
        (= (Monster goblin defense) 0)
        (= (Monster goblin location) road4)
        
        (: dragon Monster) ; sets the type of dragon to Monster
        (= (Monster dragon name) "Vortharyx the Emberfang") ; sets the name of dragon
        (= (Monster dragon hp) 200)
        (= (Monster dragon speed) 3)
        (= (Monster dragon attack) 20)
        (= (Monster dragon defense) 15)
        (= (Monster dragon location) cavern1)
        
        (= (Damages hero goblin) 10) ; hero applies damage to goblin
        (= (Damages goblin hero) 2) ; goblin applies damage to hero
        (= (Damages hero goblin) 8)
        (= (Damages goblin hero) 3)     

        ; cheat sheet
        ; match all atoms of a type:          ! (match &self (: $x Monster) $x)
        ; get a specific property of an atom: ! (Monster dragon hp)
        ; get damage done by hero to goblin:  ! (Damages hero $x)
        ; get all damage taken by hero:       ! (Damages $x hero)
        
        ; to do
        ; damage function
        ; get hp function
        ; get location function
        ; get available routes
        ; move function
        ; is_defeated function
        ; add quests with rewards
        ; add items
        ; add non-player characters (with dialogues that dynamically changes, based on reputation and other things)
        ; add puzzles (riddle with open answer, locks with combinations, wordle-like)
        
    """)

    message_counter = itertools.count(0)

    # Send a welcome message
    welcome_message = "Try writing some MeTTa code in the input below!"
    await websocket.send(create_message(next(message_counter), MESSAGE_TYPE_SYSTEM, welcome_message))

    async for message in websocket:
        try:
            # Process incoming messages and evaluate them using MeTTa
            await websocket.send(create_message(next(message_counter), MESSAGE_TYPE_USER, message))
            result = metta.run(message)

            # Send the result back to the client
            await websocket.send(create_message(next(message_counter), MESSAGE_TYPE_SYSTEM, str(result)))
        except ConnectionClosedOK:
            print("Connection closed.")


def create_message(message_id: int, message_type: str, message_text: str):
    return json.dumps({
        "id": message_id,
        "type": message_type,
        "text": message_text
    })


async def main():
    host = "localhost"
    port = 6789
    async with serve(handle_connection, host, port) as server:
        print(f"Server started at ws://{host}:{port}")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
