import asyncio
import json
import itertools
import os
import random
import textwrap
import threading

from typing import List, Dict
from flask import Flask, send_from_directory
from websockets import ConnectionClosedOK, ConnectionClosedError
from websockets.asyncio.server import serve, ServerConnection
from hyperon import MeTTa
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

FILES_DIR = "/tmp"

NLP_CANONICALS = {
    "show me the intro": "intro",
    "talk to strange figure": "talk strange_figure",
    "talk to player": "talk player",
    "get lever": "get lever",
    "ask strange figure about lever": "ask strange_figure lever",
    "move to white room": "move white_room",
    "move to red room": "move red_room",
    "move to blue room": "move blue_room",
    "move to yellow room": "move yellow_room",
    "examine door": "examine door",
    "examine hole": "examine hole",
    "examine lever": "examine lever",
    "examine mechanism": "examine mechanism1",
    "examine strange figure": "examine strange_figure",
    "take a look around": "look-around",
    "use lever": "use lever",
    "use lever on mechanism": "use lever mechanism1",
    "user lever on hole": "use lever hole",
    "leave": "leave",
    "stay": "stay"
}

nlp_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

canonical_embeddings = nlp_model.encode(list(NLP_CANONICALS.keys()), normalize_embeddings=True)

async def handle_connection(websocket: ServerConnection):
    metta_code = generate_metta_code()

    # Initialize a new MeTTa (Hyperon) instance for the connected user
    metta = MeTTa()
    output_raw = metta.run(metta_code)

    message_counter = itertools.count(1)

    output = clean_metta_output(output_raw)

    await websocket.send(create_message(True, next(message_counter), "", metta_code, output, str(output_raw)))

    try:
        async for message in websocket:
            # Process incoming messages and evaluate them using MeTTa
            inference_raw = to_metta(message)
            if inference_raw is not None:
                output_raw = metta.run(inference_raw)
                output = clean_metta_output(output_raw)
                # Send the result back to the client
                await websocket.send(create_message(True, next(message_counter), message, inference_raw, output, str(output_raw)))
            else:
                await websocket.send(create_message(False, next(message_counter), message, "", "", ""))
    except (ConnectionClosedOK, ConnectionClosedError):
        print("Connection closed.")


def clean_metta_output(metta_output: list) -> str:
    def flatten(xs):
        for x in xs:
            if isinstance(x, (list, tuple)):
                yield from flatten(x)
            elif x is None:
                continue
            else:
                yield str(x)

    return " ".join(flatten(metta_output)).replace("\"", "")


def create_message(valid: bool, message_number: int, inference: str, inference_raw: str, output: str, output_raw: str):
    return json.dumps({
        "valid": valid,
        "number": message_number,
        "inference": inference,
        "inferenceRaw": inference_raw,
        "output": output,
        "outputRaw": output_raw
    })


def to_metta(user_text: str, threshold: float = 0.6) -> str | None:
    u = nlp_model.encode([user_text], normalize_embeddings=True)
    sims = util.cos_sim(u, canonical_embeddings)[0]
    idx = int(sims.argmax())
    score = float(sims[idx])
    if score < threshold:
        return None

    canonical = list(NLP_CANONICALS.values())[idx]

    return f"!({canonical})"


def create_room_mapping(rooms: List[str]) -> Dict[str, List[str]]:
    start, others = rooms[0], rooms[1:]

    # Randomly split the other rooms into two non-empty groups
    split = random.randint(1, len(others) - 1)
    group1 = random.sample(others, split)
    group2 = [r for r in others if r not in group1]

    # Shuffle inside each branch to randomize order
    random.shuffle(group1)
    random.shuffle(group2)

    # Initialize mapping: every room -> empty list
    mapping = {room: [] for room in rooms}

    # White room points to first of each branch
    mapping[start] = [group1[0], group2[0]]

    # Chain each branch so each room points to its successor
    for branch in (group1, group2):
        for curr, nxt in zip(branch, branch[1:]):
            mapping[curr] = [nxt]
        # last room already has [] by default

    return mapping


def generate_metta_code():
    rooms = ['white_room', 'red_room', 'blue_room', 'yellow_room']
    rooms_mapping = create_room_mapping(rooms)
    route_lines = "\n".join(
        f"(Route {room} {nxt})"
        for room, succs in rooms_mapping.items()
        for nxt in succs
    )

    others = rooms[1:]
    mech1_room = random.choice(others)
    lever_room = random.choice([r for r in others if r != mech1_room])

    at_lines = "\n".join([
        f"(At mechanism1 {mech1_room})",
        f"(At lever {lever_room})"
    ])

    TEMPLATE = textwrap.dedent("""\
        ; Types

        (: player Character)
        (: strange_figure Character)

        (: white_room Location)
        (: red_room Location)
        (: blue_room Location)
        (: yellow_room Location)

        (: mechanism1 Object)
        (: mechanism2 Object)
        (: lever Object)

        ; Facts

        (Character player)
        (Character strange_figure)

        (Location white_room)
        (Location red_room)
        (Location blue_room)
        (Location yellow_room)

        {route_lines}

        (Object door)
        (Object hole)
        (Object mechanism1)
        (Object mechanism2)
        (Object lever)

        ; Dynamic

        (At hole white_room)
        (At door white_room)
        (At mechanism2 white_room)
        (At player white_room)
        (At strange_figure white_room)

        {at_lines}

        ; Functions

        (= (do $a $b) (match &self $a (match &self $b True)))

        (= (exists $atom)
            (case (match &self $atom True)
            (
                (True   True)
                (Empty  False)
            ))
        )

        (= (same-location $a $b)
            (if (and
                    (exists (At $a $x))
                    (exists (At $b $x))
                )
                (== 
                    (match &self (At $a $x) $x) 
                    (match &self (At $b $x) $x)
                )
                False
            )
        )

        (= (talk $who) 
            (if (same-location player $who) 
                (do-talk $who)
                "Talk to... whom?" 
            )
        )

        (= (do-talk player) "Talking to yourself now? That's... fine. Probably.")
        (= (do-talk strange_figure) "Without saying a word, the strange figure just points at the door.")

        (= (get $what) 
            (if (same-location player $what)
                (do-get $what)
                "Get... what?"
            )
        )

        (= (do-get lever) 
            (do
                (match &self (At lever $x) (remove-atom &self (At lever $x))) 
                (add-atom &self (Has player lever))
            )
        )
        (= (do-get lever) "You pick up the lever.")

        (= (ask $who $what) 
            (if (same-location player $who)
                (do-ask $who $what)
                "Ask... whom?"
            )
        )

        (= (do-ask strange_figure lever)
            "The strange figure silently raises a finger and points toward a small hole in the wall."
        )

        (= (describe-location white_room) "You are in a white room.")
        (= (describe-location red_room) "You are in a red room.")
        (= (describe-location blue_room) "You are in a blue room.")
        (= (describe-location yellow_room) "You are in a yellow room.")
        (= (describe-location $what) (empty))

        (= (move $where)
            (match &self (At player $x)
                (if 
                    (or 
                        (exists (Route $x $where))
                        (exists (Route $where $x))
                    )
                    (do-move $where)
                    "Go... where?"
                )
            )
        )

        (= (do-move $where)
            (do
                (match &self (At player $x) (remove-atom &self (At player $x))) 
                (add-atom &self (At player $where))
            )
        )

        (= (do-move $where) (describe-location $where))

        (= (examine $what) 
            (if (same-location player $what)
                (do-examine $what)
                "Examine... what?"
            )
        )

        (= (do-examine door) "A large wooden door.")

        (= (do-examine door)
            (if (and 
                    (exists (Unlocked lock1))
                    (exists (Unlocked lock2))
                )
                "Hey! The door is open now, revealing the path beyond. What do you want to do?"
                (if (or
                        (exists (Unlocked lock1))
                        (exists (Unlocked lock2))
                    )
                    "It's still locked... but something feels different."
                    "It is locked."
                )
            )
        )

        (= (do-examine hole ) "A round hole sits in the wall. It doesn't look like damage—it's precise, as if designed to hold something.")
        (= (do-examine lever) "A common lever. Maybe you can use it somewhere.")
        (= (do-examine mechanism1) "Some kind of mechanism — incomplete, perhaps?")
        (= (do-examine strange_figure) "A tall figure cloaked in dark, tattered robes, its face hidden under a deep hood. ")
        (= (do-examine $what) (empty))

        (= (look-around) "You find:") 

        (= (look-around) 
            (match &self (At player $where)
                (do-look-around (match &self (At $what $where) $what))
            )
        )

        (= (look-around) 
            (match &self (At player $where)
                (do-look-around (match &self (Route $where $whereto) $whereto))
            )
        )

        (= (look-around) 
            (match &self (At player $where)
                (do-look-around (match &self (Route $whereto $where) $whereto))
            )
        )

        (= (do-look-around door) "A door.")
        (= (do-look-around mechanism1) "A mechanism.")
        (= (do-look-around lever) "A lever.")
        (= (do-look-around strange_figure) "A strange figure.")
        (= (do-look-around white_room) "The white room entrance.")
        (= (do-look-around red_room) "The red room entrance.")
        (= (do-look-around blue_room) "The blue room entrance.")
        (= (do-look-around yellow_room) "The yellow room entrance.")

        (= (do-look-around $what) (empty))

        (= (can-use $what) (exists (Has player $what)))

        (= (use $what)
            (if (can-use $what)
                (do-use lever)
                "Use... what?"
            )
        )

        (= (use $what $onwhat)
            (if (and
                    (same-location player $onwhat)
                    (can-use $what)
                )
                (do-use $what $onwhat)
                "Use... on what?"
            )
        )

        (= (do-use lever) "Use the lever where... exactly?")

        (= (do-use lever mechanism1) "You use the lever on the mechanism. It must've done something... right?")
        (= (do-use lever mechanism1) (add-atom &self (Unlocked lock1)))

        (= (do-use lever hole) "You insert the lever into the hole and give it a turn. What now?")
        (= (do-use lever hole) (add-atom &self (Unlocked lock2)))

        (= (leave) 
            (if (and 
                    (exists (Unlocked lock1))
                    (exists (Unlocked lock2))
                )
                "You step through the door, leaving the white room behind. The strange figure watches in silence, a flicker of sadness in its eyes — but it doesn't stop you."
                "You can't leave — the main door is locked."
            )
        )

        (= (stay) 
            (do
                (remove-atom &self (Unlocked lock1))
                (remove-atom &self (Unlocked lock2))
            )
        )
        (= (stay) "The door locks again. Great. The creepy figure actually looks... happy?")

        (= (intro) "You wake in a white room, sterile and silent. No memory of how you got here. Better take a look around.")
    """)

    return TEMPLATE.format(
        at_lines=at_lines,
        route_lines=route_lines
    )


@app.route("/api/generated/metta/<filename>")
def serve_file(filename):
    return send_from_directory(FILES_DIR, filename, mimetype="text/plain")


def start_flask():
    host = os.getenv("FLASK_HOST", "localhost")
    port = os.getenv("FLASK_PORT", 8080)
    print(f"Flask serving on http://{host}:{port} (in background)")
    app.run(host=host, port=port, use_reloader=False)


async def main():
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    host = os.getenv("WS_HOST", "localhost")
    port = os.getenv("WS_PORT", 6789)
    async with serve(handle_connection, host, port) as server:
        print(f"Server started at ws://{host}:{port}")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
