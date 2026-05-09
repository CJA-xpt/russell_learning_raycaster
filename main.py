import pygame
import math

pygame.init()

# =========================================================
# SCREEN SETTINGS
# =========================================================

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Forgot Russell's title")

clock = pygame.time.Clock()

# =========================================================
# PLAYER SETTINGS
# =========================================================

player_x = 3
player_y = 3
player_angle = 0

player_health = 100

MOVE_SPEED = 0.05
ROT_SPEED = 0.04

# =========================================================
# RAYCAST SETTINGS
# =========================================================

FOV = math.pi / 3
HALF_FOV = FOV / 2

NUM_RAYS = 120
MAX_DEPTH = 20

# =========================================================
# MAP
# 1 = wall
# 0 = empty space
# =========================================================

world_map = [
    "111111111111",
    "100000000001",
    "101111011101",
    "100001000001",
    "101101110101",
    "100000000001",
    "101111111101",
    "100000000001",
    "111111111111",
]

# =========================================================
# ENEMIES
# Each enemy:
# [x, y]
# =========================================================

enemies = [
    [5, 6],
    [8, 5],
    [6, 7]
]

# =========================================================
# COLORS
# =========================================================

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

RED = (255, 0, 0)
DARK_RED = (80, 0, 0)

GREEN = (0, 255, 0)

GRAY = (120, 120, 120)

# =========================================================
# FONT
# =========================================================

font = pygame.font.SysFont(None, 36)

# =========================================================
# ENEMY SPRITE
# =========================================================

enemy_img = pygame.Surface((64, 64))
enemy_img.fill(RED)

# ---------------------------------------------------------
#enemy_img = pygame.image.load("ibhohz51sfc41.png").convert_alpha()
# ---------------------------------------------------------

# =========================================================
# WALL TEXTURE PLACEHOLDER
# =========================================================

# Later we can define a wall texture:
#
# wall_texture = pygame.image.load("brick.png")
#
# =========================================================

# =========================================================
# DAMAGE FLASH TIMER
# =========================================================

damage_flash = 0

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)

# =========================================================
# RAYCASTING
# =========================================================

def cast_rays():
    start_angle = player_angle - HALF_FOV
    global z_buffer
    z_buffer = [float('inf')] * NUM_RAYS

    for ray in range(NUM_RAYS):
        angle = start_angle + ray * (FOV / NUM_RAYS)

        for depth in range(1, int(MAX_DEPTH * 100)):
            depth /= 100
            target_x = player_x + math.cos(angle) * depth
            target_y = player_y + math.sin(angle) * depth

            map_x = int(target_x)
            map_y = int(target_y)

            if world_map[map_y][map_x] == "1":
                corrected_depth = depth * math.cos(player_angle - angle)
                wall_height = HEIGHT / (corrected_depth + 0.0001)

                brightness = 255 / (1 + corrected_depth * corrected_depth * 0.1)
                wall_color = (brightness, brightness, brightness)

                pygame.draw.rect(
                    screen,
                    wall_color,
                    (
                        ray * (WIDTH // NUM_RAYS),
                        HEIGHT // 2 - wall_height // 2,
                        WIDTH // NUM_RAYS + 1,
                        wall_height
                    )
                )

                # Save depth for this ray
                z_buffer[ray] = corrected_depth
                break
            
# =========================================================
# SHOOTING MECHANIC
# =========================================================

def shoot():
    global enemies
    # Ray straight ahead
    angle = player_angle
    for depth in range(1, int(MAX_DEPTH * 100)):
        depth /= 100
        target_x = player_x + math.cos(angle) * depth
        target_y = player_y + math.sin(angle) * depth

        map_x = int(target_x)
        map_y = int(target_y)

        # Stop if wall hit
        if world_map[map_y][map_x] == "1":
            break

        # Check enemies and copy list to allow removal
        for enemy in enemies[:]:
            ex, ey = enemy
            dist = distance(target_x, target_y, ex, ey)
        # hit threshold
            if dist < 0.3:
                enemies.remove(enemy)
                return


# =========================================================
# DRAW ENEMIES
# =========================================================

def draw_enemies():
    enemy_render_list = []

    for enemy in enemies:
        ex, ey = enemy
        dx = ex - player_x
        dy = ey - player_y
        dist = math.sqrt(dx * dx + dy * dy)

        angle_to_enemy = math.atan2(dy, dx)
        angle_diff = angle_to_enemy - player_angle

        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        if abs(angle_diff) < HALF_FOV:
            screen_x = (angle_diff + HALF_FOV) / FOV * WIDTH
            size = HEIGHT / (dist + 0.0001)

            enemy_render_list.append((dist, screen_x, size))

    enemy_render_list.sort(reverse=True)

    for dist, screen_x, size in enemy_render_list:
        enemy_scaled = pygame.transform.scale(enemy_img, (int(size), int(size)))
        draw_x = int(screen_x - size / 2)
        draw_y = int(HEIGHT / 2 - size / 2)

        # Z-buffer check
        ray_index = int(screen_x / (WIDTH / NUM_RAYS))
        if 0 <= ray_index < NUM_RAYS and dist < z_buffer[ray_index]:
            screen.blit(enemy_scaled, (draw_x, draw_y))


# =========================================================
# ENEMY MOVEMENT + DAMAGE
# =========================================================

def update_enemies():

    global player_health
    global damage_flash

    for enemy in enemies:

        ex, ey = enemy

        dx = player_x - ex
        dy = player_y - ey

        dist = math.sqrt(dx * dx + dy * dy)

        # -------------------------------------------------
        # MOVE TOWARD PLAYER
        # -------------------------------------------------

        if dist > 0.5:

            dx /= dist
            dy /= dist

            speed = 0.015

            new_x = ex + dx * speed
            new_y = ey + dy * speed

            # Wall collision
            if world_map[int(new_y)][int(new_x)] == "0":

                enemy[0] = new_x
                enemy[1] = new_y

        # -------------------------------------------------
        # DAMAGE PLAYER
        # -------------------------------------------------

        if dist < 0.6:

            player_health -= 0.1

            damage_flash = 5

            if player_health < 0:
                player_health = 0

# =========================================================
# HEALTH BAR
# =========================================================

def draw_health_bar():

    # Background
    pygame.draw.rect(
        screen,
        DARK_RED,
        (20, 20, 200, 25)
    )

    # Current HP
    health_width = int(200 * (player_health / 100))

    pygame.draw.rect(
        screen,
        RED,
        (20, 20, health_width, 25)
    )

    # Text
    hp_text = font.render(
        f"HP: {int(player_health)}",
        True,
        WHITE
    )

    screen.blit(hp_text, (20, 55))

# =========================================================
# CROSSHAIR
# =========================================================

def draw_crosshair():

    center_x = WIDTH // 2
    center_y = HEIGHT // 2

    pygame.draw.line(
        screen,
        WHITE,
        (center_x - 10, center_y),
        (center_x + 10, center_y),
        2
    )

    pygame.draw.line(
        screen,
        WHITE,
        (center_x, center_y - 10),
        (center_x, center_y + 10),
        2
    )

# =========================================================
# MINIMAP
# =========================================================

def draw_minimap():

    tile_size = 20

    for y, row in enumerate(world_map):

        for x, tile in enumerate(row):

            color = BLACK

            if tile == "1":
                color = GRAY

            pygame.draw.rect(
                screen,
                color,
                (
                    x * tile_size,
                    y * tile_size,
                    tile_size,
                    tile_size
                )
            )

    # Draw enemies
    for ex, ey in enemies:

        pygame.draw.circle(
            screen,
            RED,
            (
                int(ex * tile_size),
                int(ey * tile_size)
            ),
            5
        )

    # Draw player
    pygame.draw.circle(
        screen,
        GREEN,
        (
            int(player_x * tile_size),
            int(player_y * tile_size)
        ),
        5
    )

# =========================================================
# GAME OVER
# =========================================================

def draw_game_over():

    text = font.render(
        "GAME OVER",
        True,
        RED
    )

    screen.blit(
        text,
        (WIDTH // 2 - 100, HEIGHT // 2)
    )

# =========================================================
# MAIN LOOP
# =========================================================

running = True

while running:

    # =====================================================
    # EVENTS
    # =====================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    # =====================================================
    # INPUT
    # =====================================================

    keys = pygame.key.get_pressed()

    if player_health > 0:

        # Rotation
        if keys[pygame.K_a]:
            player_angle -= ROT_SPEED

        if keys[pygame.K_d]:
            player_angle += ROT_SPEED

        # Movement
        move_x = 0
        move_y = 0

        if keys[pygame.K_w]:
            move_x += math.cos(player_angle) * MOVE_SPEED
            move_y += math.sin(player_angle) * MOVE_SPEED

        if keys[pygame.K_s]:
            move_x -= math.cos(player_angle) * MOVE_SPEED
            move_y -= math.sin(player_angle) * MOVE_SPEED

        new_x = player_x + move_x
        new_y = player_y + move_y

        # Wall collision
        if world_map[int(new_y)][int(new_x)] == "0":
            player_x = new_x
            player_y = new_y
            
        if keys[pygame.K_SPACE]:
            shoot()


    # =====================================================
    # UPDATE
    # =====================================================

    update_enemies()

    # =====================================================
    # DRAW SKY + FLOOR
    # =====================================================

    screen.fill((60, 60, 60))

    pygame.draw.rect(
        screen,
        (100, 100, 255),
        (0, 0, WIDTH, HEIGHT // 2)
    )

    pygame.draw.rect(
        screen,
        (50, 50, 50),
        (0, HEIGHT // 2, WIDTH, HEIGHT // 2)
    )


    # =====================================================
    # DRAW 3D WORLD
    # =====================================================

    cast_rays()

    draw_enemies()

    # =====================================================
    # DRAW UI
    # =====================================================

    draw_health_bar()

    draw_crosshair()

    draw_minimap()

    # =====================================================
    # DAMAGE FLASH
    # =====================================================

    if damage_flash > 0:

        red_overlay = pygame.Surface((WIDTH, HEIGHT))
        red_overlay.set_alpha(60)
        red_overlay.fill((255, 0, 0))

        screen.blit(red_overlay, (0, 0))

        damage_flash -= 1

    # =====================================================
    # GAME OVER
    # =====================================================

    if player_health <= 0:
        draw_game_over()

    # =====================================================
    # UPDATE SCREEN
    # =====================================================

    pygame.display.flip()

    clock.tick(60)

pygame.quit()

