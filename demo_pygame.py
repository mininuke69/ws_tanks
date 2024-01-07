from pygame import init
from pygame import display
from pygame import time
from pygame import event
from pygame import QUIT
from pygame import KEYDOWN, KEYUP
from pygame import K_w, K_a, K_s, K_d
from pygame import MOUSEBUTTONDOWN
from pygame import Surface
from time import sleep
from threading import Thread

from client import Client
from shared import Vector
from shared import Settings


client = Client()
client.ws_map()
client.ws_spawn()
client.ws_update()

init()
WIDTH, HEIGHT = 800, 600
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
running = True





def update_loop():
    while True:
        sleep(1/15)
        client.ws_update(
            (movement_dir.normalized * Settings.player_speed).x,
            (movement_dir.normalized * Settings.player_speed).y,
        )


movement_dir = Vector(0, 0)
Thread(target=update_loop, daemon=True).start()




while running:

    
    for ev in event.get():
        if ev.type == QUIT:
            quit()

        if ev.type == KEYDOWN:
            
            key = ev.dict["key"]
        
            movement_dir.y -= (key == K_w)
            movement_dir.y += (key == K_s)
            movement_dir.x += (key == K_d)
            movement_dir.x -= (key == K_a)

        if ev.type == KEYUP:

            key = ev.dict["key"]

            movement_dir.y += (key == K_w)
            movement_dir.y -= (key == K_s)
            movement_dir.x -= (key == K_d)
            movement_dir.x += (key == K_a)

        if ev.type == MOUSEBUTTONDOWN:
            pos = ev.dict["pos"]
            client.ws_shoot(Vector(pos[0] - WIDTH / 2, pos[1] - HEIGHT / 2))

    screen.fill("gray")
    for wall in client.map:

        wall_surface = Surface((wall.width, wall.height))
        wall_surface.fill((50, 50, 50))
        screen.blit(wall_surface, (wall.x - client.player.x + WIDTH / 2, wall.y - client.player.y + HEIGHT / 2))    


    for player in client.predicted_players:

        if player.hp <= 0:
            continue

        player_surface = Surface((Settings.player_size, Settings.player_size))
        player_surface.fill((100, 100, 200)) if player.nick == client.player.nick else player_surface.fill((200, 100, 100))
        screen.blit(player_surface, (player.x - client.player.x - Settings.player_size / 2 + WIDTH / 2, player.y - client.player.y - Settings.player_size / 2 + HEIGHT / 2))

    for game_object in client.game_objects:

        if game_object.obj_type == "bullet":
            game_object_surface = Surface((Settings.bullet_size, Settings.bullet_size))
            game_object_surface.fill((10, 10, 10)) if game_object.player == client.player.nick else game_object_surface.fill((220, 50, 50))
            screen.blit(game_object_surface, (game_object.rect.x - client.player.x + Settings.bullet_size / 2 + WIDTH / 2, game_object.rect.y - client.player.y + Settings.bullet_size / 2 + HEIGHT / 2))
    
    test = Surface((2, 2))
    screen.blit(test, (WIDTH / 2 - 1, HEIGHT / 2 - 1))
    display.flip()

    clock.tick(60)