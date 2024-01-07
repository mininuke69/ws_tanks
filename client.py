from websockets.sync.client import connect
from json import loads
from json import dumps
from time import sleep
from typing import List
from time import perf_counter
from random import randint


# own library, used by both client and server
from shared import Player
from shared import Rect
from shared import Vector
from shared import GameObject
from shared import Settings

class Client:
    def __init__(self, ws_url="ws://localhost:8818") -> None:
        self.websocket = connect(ws_url)
        self.player = Player(
            nick=None,
            hp=0,
            x=0,
            y=0,
            vx=0,
            vy=0,
            shot_cooldown=0,
            kills=0,
            deaths=0,
        )
        self.map: List[Rect] | None = None
        self.players: List[Player] | None = None
        self.game_objects: List[GameObject] | None = None

        self.time_last_update = perf_counter()


    def ws_map(self):
        message = {
            "type": "map"
        }
        self.websocket.send(dumps(message))

        response = loads(self.websocket.recv())
        assert response["type"] == "map"

        self.map = []
        for rect in response["map"]:
            self.map.append(Rect(*rect))
        print(f'updated map: {self.map}')


    def ws_spawn(self):
        message = {
            "type": "spawn"
        }
        self.websocket.send(dumps(message))
        response = loads(self.websocket.recv())
        assert response["type"] == "spawn"

        self.player.x = response["x"]
        self.player.y = response["y"]
        self.player.vx = 0.0
        self.player.vy = 0.0

        print(f'spawned at ({self.player.x};{self.player.y})')


    def ws_update(self, *args):
        if args:
            vx, vy = args
            message = {
                "type": "update",
                "vx": vx,
                "vy": vy
            }
        else:
            message = {
                "type": "update"
            }
    

        self.websocket.send(dumps(message))
        response = loads(self.websocket.recv())
        try:
            assert response["type"] == "update"
        except AssertionError:
            print("problem problem: ", response)
            return

        self.player = Player(**response["player"])

        self.players = []
        for player in response["players"]:
            self.players.append(Player(
                nick=player["nick"],
                hp=player["hp"],
                x=player["x"],
                y=player["y"],
                vx=player["vx"],
                vy=player["vy"],
                shot_cooldown=player["shot_cooldown"],
                kills=player["kills"],
                deaths=player["deaths"],
            ))

        self.game_objects = []
        for game_object in response["game_objects"]:
            self.game_objects.append(GameObject(
                obj_type=game_object["obj_type"],
                rect=Rect(*game_object["rect"]),
                vel=Vector(*game_object["vel"]),
                player=game_object["player"],
                hp=game_object["hp"],
            ))


        # used for prediction
        self.time_last_update = perf_counter()


    def ws_shoot(self, direction: Vector):
        message = {
            "type": "shoot",
            "x": direction.x,
            "y": direction.y,
        }
        self.websocket.send(dumps(message))


    @property
    def predicted_players(self):
        dt = perf_counter() - self.time_last_update
        predicted = [Player(nick=player.nick, hp=player.hp, x=player.x + player.vx * dt, y=player.y + player.vy * dt, vx=player.vx, vy=player.vy, shot_cooldown=player.shot_cooldown - dt, kills=player.kills, deaths=player.deaths) for player in self.players]
        return predicted