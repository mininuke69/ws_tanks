from websockets import serve
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedError
from asyncio import run
from asyncio import Future
from asyncio import create_task
from asyncio import sleep
from json import loads
from json import dumps
from typing import List
from typing import Dict
from secrets import token_urlsafe
from random import randint

# own library, used by both client and server
from shared import Player
from shared import Rect
from shared import ExampleMaps
from shared import Settings
from shared import Vector
from shared import GameObject


players: Dict[str, Player] = {}
game_objects: List[GameObject] = []
game_map: List[Rect] = ExampleMaps.map1


async def handler(websocket: WebSocketServerProtocol):

    global players # we need to write to this variable
    global game_objects
    print(f"new connection: {websocket.remote_address}")

    token = token_urlsafe()
    players[token] = Player(nick=token)
    try:
        async for message_str in websocket:
            message = loads(message_str)

            # print(f'message: {message}')

            match message["type"]:
                case "map":
                    # reply with a list of tuples that represent rects.
                    response = {
                        "type": "map",
                        "map": game_map
                    }
                    # lambda that serializes Rect() objects
                    await websocket.send(dumps(response, default=serialize))

                case "spawn":
                    # check if client is not already alive, if so, 
                    # find a spawn location and reply with {"x": ..., "y": ...}
                    if players[token].hp <= 0:
                        players[token].hp = Settings.spawn_hp
                        
                        # TODO: set play position on spawn point,
                        # TODO: check if spawnpoint is safe
                        players[token].x = randint(80, 120)
                        players[token].y = randint(80, 120)

                        response = {
                            "type": "spawn",
                            "x": players[token].x,
                            "y": players[token].y
                        }
                        await websocket.send(dumps(response))
                    else:
                        response = {
                            "type": "error",
                            "error": "can't respawn, player still alive"
                        }
                        await websocket.send(dumps(response))
                
                case "update":
                    # check for optional vy and vx, if found, cap and update those
                    # respond with own position and all enemy's who are in view
                    try: 
                        if Vector(message["vx"], message["vy"]).magnitude <= Settings.player_speed + 0.00000001:

                            players[token].vx = message["vx"]
                            players[token].vy = message["vy"]
                        else:
                            response = {
                                "type": "error",
                                "error": "too speedy",
                                "max_speed": Settings.player_speed,
                                "attempted_speed": Vector(message["vx"], message["vy"]).magnitude,
                            }
                            await websocket.send(dumps(response))
                            continue
                    except KeyError:
                        pass

                    
                    response = {
                        "type": "update",
                        "player": players[token],
                        "players": [players[player_token] for player_token in players],
                        "game_objects": game_objects,
                    }
                    await websocket.send(dumps(response, default=serialize))
                    
                case "shoot":
                    # shoot a bullet in the direction of a vector.
                    if Vector(message["x"], message["y"]).magnitude == 0:
                        response = {
                            "type": "error",
                            "error": "bullet vector with magnitude 0, are you high?"
                        }
                        await websocket.send(dumps(response))

                    elif players[token].hp <= 0:
                        response = {
                            "type": "error",
                            "error": "player is dead, why are you trying to shoot?"
                        }
                        await websocket.send(dumps(response))

                    else:
                        new_bullet = GameObject(
                            obj_type="bullet",
                            rect=Rect(
                                x=players[token].x - Settings.bullet_size / 2,
                                y=players[token].y - Settings.bullet_size / 2,
                                width=Settings.bullet_size,
                                height=Settings.bullet_size,
                            ),
                            # bullets are always launched at full speed
                            vel=Vector(message["x"], message["y"]).normalized * Settings.bullet_speed,
                            player=token,
                            hp=Settings.bullet_damage
                        )
                        game_objects.append(new_bullet)

    except ConnectionClosedError:
        # player disconnects forcefully
        players.pop(token)

    finally:
        # player disconnects using .close()
        players.pop(token)

def collide_walls(rect: Rect):
    for wall in game_map:
        if rect.collide(wall):
            return True
    return False


async def physics():
    global players
    global game_objects

    for token in players:

        # no physics need to be done for dead players
        if players[token].hp <= 0:
            continue


        players[token].x += Settings.physics_interval * players[token].vx
        players[token].y += Settings.physics_interval * players[token].vy

        player_rect = Rect(
            players[token].x - Settings.player_size / 2,
            players[token].y - Settings.player_size / 2,
            Settings.player_size,
            Settings.player_size
        )

        if collide_walls(player_rect):
            players[token].x -= Settings.physics_interval * players[token].vx
            players[token].y -= Settings.physics_interval * players[token].vy
            # break was a fun little bug
            # continue was a fun little bug
            # somehow you become immortal when you hit walls i guess

        for game_object in game_objects:
            # change this to check for all bullets if multiple types
            if not game_object.obj_type == "bullet":
                continue
            # skip bullets that are owned by the player
            if game_object.player == token:
                continue
            # if hit by bullet
            if game_object.rect.collide(player_rect):
                # damage or heal the player
                players[token].hp += game_object.hp
                # remove the bullet or powerup
                game_objects.remove(game_object)
                print(players[token].nick, "hit!, hp:", players[token].hp)
            else:
                pass
    for game_object in game_objects:
        game_object.rect.x += game_object.vel.x * Settings.physics_interval
        game_object.rect.y += game_object.vel.y * Settings.physics_interval

        if collide_walls(game_object.rect):
            # remove the bullet if it collides with wall
            # TODO: implement bullet bouncing
            game_objects.remove(game_object)

def serialize(o):
    if isinstance(o, Player):
        return {"nick": o.nick, "hp": o.hp, "x": o.x, "y": o.y, "vx": o.vx, "vy": o.vy, "shot_cooldown": o.shot_cooldown, "kills": o.kills, "deaths": o.deaths}
    elif isinstance(o, Rect):
        return (o.x, o.y, o.width, o.height)
    elif isinstance(o, GameObject):
        return {"obj_type": o.obj_type, "rect": o.rect, "vel": o.vel, "player": o.player, "hp": o.hp}
    elif isinstance(o, Vector):
        return (o.x, o.y)



async def main():
    
    async with serve(handler, "", 8818):
        # server mainloop
        while True:
            await sleep(Settings.physics_interval)
            await physics()


if __name__ == '__main__':
    run(main())