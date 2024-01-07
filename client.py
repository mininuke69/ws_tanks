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

        self.time_last_prediction = perf_counter()


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
        




if __name__ == '__main__':
    from processing_py import App
    app = App(400, 300)

    client = Client()
    client.ws_map()
    client.ws_spawn()

    target = Vector(randint(30, 170), randint(30, 170))

    

    while True:
        # go in some direction
        client.ws_update(
            (Vector(target.x - client.player.x, target.y - client.player.y).normalized * Settings.player_speed).x,
            (Vector(target.x - client.player.x, target.y - client.player.y).normalized * Settings.player_speed).y
        )

        sleep(1/25)
        if randint(0, 25) == 0: client.ws_shoot(Vector(client.predicted_players[0].x - client.player.x, client.predicted_players[0].y - client.player.y))
        
        app.background(40, 40, 40)
        app.fill(200, 200, 200)
        for rect in client.map:
            app.rect(
                rect.x,
                rect.y,
                rect.width,
                rect.height
            )
        app.fill(100, 100, 180)
        for player in client.predicted_players:
            if player.hp <= 0:
                continue

            app.rect(
                player.x - (Settings.player_size / 2),
                player.y - (Settings.player_size / 2),
                Settings.player_size,
                Settings.player_size
            )
        app.fill(200, 20, 20)
        for game_object in client.game_objects:

            app.rect(
                game_object.rect.x - game_object.rect.width / 2,
                game_object.rect.y - game_object.rect.height / 2,
                game_object.rect.width,
                game_object.rect.height,
            )
        app.redraw()
        