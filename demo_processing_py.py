from client import Client
from shared import Vector
from shared import Settings
from time import sleep
from random import randint


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
        target_player_idx = randint(0, len(client.players) - 1)
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