# SPDX-FileCopyrightText: 2023-present luxluth <delphin.blehoussi93@gmail.com>
#
# SPDX-License-Identifier: MIT

from pygame_hotreload import HotReload, set_caption
# imports-start-hotreload
import pygame
# imports-end-hotreload

# Initialize pygame
pygame.init()

# Set the window caption
set_caption("Hot Reload Example")
clock = pygame.time.Clock()
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))

# globals-start-hotreload
global dt
global player_pos
global player_pos_2
# globals-end-hotreload

# init-start-hotreload
def init():
    global dt
    global player_pos
    global player_pos_2
    dt = 0
    player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
    player_pos_2 = pygame.Vector2(screen.get_width() // 3, screen.get_height() // 3)
# init-end-hotreload


# loop-start-hotreload
def loop():
    global dt
    global player_pos
    global player_pos_2
    screen.fill("black")
    pygame.draw.rect(screen, "purple", 
                     pygame.Rect(player_pos.x, player_pos.y, 100, 100))
    pygame.draw.rect(screen, "purple", 
                     pygame.Rect(player_pos_2.x, player_pos_2.y, 100, 100), 1)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_z] or keys[pygame.K_UP]:
        player_pos.y -= 300 * dt
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        player_pos.y += 300 * dt
    if keys[pygame.K_q] or keys[pygame.K_LEFT]:
        player_pos.x -= 300 * dt
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player_pos.x += 300 * dt

    dt = clock.tick(60) / 1000
# loop-end-hotreload

# Initialize the hot reload
hotreload = HotReload(
    main_file=__file__,
    screen=screen,
    clock=clock,
    clock_tick=60,
    gen_script_name="gen.py",
)

hotreload.run()