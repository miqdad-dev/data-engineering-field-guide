"""Lane Runner - a pseudo-3D lane switching car game built with pygame.

Use the left and right arrow keys to change lanes and avoid incoming traffic.
Press P to pause/resume the action and R to restart after a crash.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from typing import List

import pygame


# Screen configuration
WIDTH, HEIGHT = 480, 720
FPS = 60

# Road configuration to create a faux-3D look
ROAD_TOP_Y = 80
ROAD_BOTTOM_Y = HEIGHT
ROAD_TOP_WIDTH = WIDTH * 0.35
ROAD_BOTTOM_WIDTH = WIDTH * 0.85
LANES = (-1, 0, 1)

# Car sizing
PLAYER_SIZE = (60, 110)
ENEMY_SIZE = (56, 100)

# Gameplay tuning
BASE_SPEED = 280  # pixels per second that enemies travel
SCORE_RATE = 75   # score points gained per second at level 0
LEVEL_UP_EVERY = 800  # score threshold for each new level
MAX_LEVEL = 12
SPAWN_INTERVAL = 1.05  # seconds between enemy spawns at level 0


@dataclass
class Car:
    lane_index: int
    y: float
    color: pygame.Color
    size: tuple[int, int]

    @property
    def lane(self) -> int:
        return LANES[self.lane_index]

    def rect(self) -> pygame.Rect:
        width, height = self.size
        center_x = lane_to_screen_x(self.lane, self.y + height / 2)
        top_left_x = center_x - width / 2
        top_left_y = self.y
        return pygame.Rect(int(top_left_x), int(top_left_y), width, height)


@dataclass
class GameState:
    player: Car
    enemies: List[Car]
    score: float
    level: int
    speed: float
    spawn_cooldown: float
    status: str  # "running", "paused", "game_over"


def lane_to_screen_x(lane: int, y_pos: float) -> float:
    """Map a logical lane (-1, 0, 1) to an x position with basic perspective."""
    perspective = (y_pos - ROAD_TOP_Y) / (ROAD_BOTTOM_Y - ROAD_TOP_Y)
    perspective = max(0.0, min(1.0, perspective))

    road_width = ROAD_TOP_WIDTH + (ROAD_BOTTOM_WIDTH - ROAD_TOP_WIDTH) * perspective
    lane_width = road_width / len(LANES)

    road_center = WIDTH / 2
    center_offset = (lane + 0.5) * lane_width - road_width / 2
    return road_center + center_offset


def create_player() -> Car:
    start_lane_index = 1  # middle lane
    start_y = HEIGHT - PLAYER_SIZE[1] - 40
    return Car(lane_index=start_lane_index, y=start_y, color=pygame.Color(80, 220, 120), size=PLAYER_SIZE)


def create_enemy(level: int) -> Car:
    lane_index = random.randrange(len(LANES))
    spawn_y = -ENEMY_SIZE[1] - 20
    color = random.choice(
        [
            pygame.Color(220, 80, 80),
            pygame.Color(240, 220, 100),
            pygame.Color(100, 180, 240),
            pygame.Color(200, 120, 220),
        ]
    )
    enemy = Car(lane_index=lane_index, y=spawn_y, color=color, size=ENEMY_SIZE)

    # Stagger spawn so cars don't overlap immediately
    for other in range(random.randint(0, 1)):
        enemy.y -= (ENEMY_SIZE[1] + 40) * (other + 1)
    return enemy


def reset_state() -> GameState:
    player = create_player()
    return GameState(
        player=player,
        enemies=[],
        score=0.0,
        level=0,
        speed=BASE_SPEED,
        spawn_cooldown=0.0,
        status="running",
    )


def update_state(state: GameState, dt: float) -> None:
    if state.status != "running":
        return

    state.score += SCORE_RATE * dt * (1 + state.level * 0.1)
    state.level = min(MAX_LEVEL, int(state.score // LEVEL_UP_EVERY))
    state.speed = BASE_SPEED + state.level * 35

    state.spawn_cooldown -= dt
    spawn_threshold = SPAWN_INTERVAL / (1 + state.level * 0.2)
    if state.spawn_cooldown <= 0:
        state.enemies.append(create_enemy(state.level))
        state.spawn_cooldown = spawn_threshold

    # Move enemies
    for enemy in state.enemies:
        enemy.y += state.speed * dt

    # Remove off-screen enemies and increment score for successful dodge
    remaining_enemies = []
    for enemy in state.enemies:
        if enemy.y > HEIGHT + 20:
            state.score += 25
        else:
            remaining_enemies.append(enemy)
    state.enemies = remaining_enemies

    # Collision detection
    player_rect = state.player.rect()
    for enemy in state.enemies:
        if player_rect.colliderect(enemy.rect()):
            state.status = "game_over"
            break


def handle_player_input(state: GameState, key: int) -> None:
    if key == pygame.K_LEFT:
        state.player.lane_index = max(0, state.player.lane_index - 1)
    elif key == pygame.K_RIGHT:
        state.player.lane_index = min(len(LANES) - 1, state.player.lane_index + 1)


def draw_text(surface: pygame.Surface, text: str, size: int, position: tuple[int, int], color: pygame.Color = pygame.Color(250, 250, 250)) -> None:
    font = pygame.font.SysFont("arial", size, bold=True)
    rendered = font.render(text, True, color)
    surface.blit(rendered, position)


def draw_background(screen: pygame.Surface) -> None:
    screen.fill((25, 30, 40))

    road_color = pygame.Color(60, 60, 70)
    shoulder_color = pygame.Color(80, 80, 90)

    # Draw shoulder for faux depth
    shoulder_points = [
        (WIDTH * 0.12, ROAD_TOP_Y - 30),
        (WIDTH * 0.88, ROAD_TOP_Y - 30),
        (WIDTH * 0.98, HEIGHT),
        (WIDTH * 0.02, HEIGHT),
    ]
    pygame.draw.polygon(screen, shoulder_color, shoulder_points)

    road_points = [
        (WIDTH / 2 - ROAD_TOP_WIDTH / 2, ROAD_TOP_Y),
        (WIDTH / 2 + ROAD_TOP_WIDTH / 2, ROAD_TOP_Y),
        (WIDTH / 2 + ROAD_BOTTOM_WIDTH / 2, ROAD_BOTTOM_Y),
        (WIDTH / 2 - ROAD_BOTTOM_WIDTH / 2, ROAD_BOTTOM_Y),
    ]
    pygame.draw.polygon(screen, road_color, road_points)

    # Lane markers with perspective
    for lane in range(1, len(LANES)):
        top_x = lane_to_screen_x(-1 + lane, ROAD_TOP_Y + 10)
        bottom_x = lane_to_screen_x(-1 + lane, HEIGHT)
        pygame.draw.line(screen, (200, 200, 210), (top_x, ROAD_TOP_Y + 30), (bottom_x, HEIGHT), 4)

    # Horizon glow
    pygame.draw.rect(screen, (120, 180, 220), pygame.Rect(0, 0, WIDTH, ROAD_TOP_Y), border_radius=0)


def draw_car(screen: pygame.Surface, car: Car, outline: bool = False) -> None:
    rect = car.rect()
    pygame.draw.rect(screen, car.color, rect, border_radius=6)
    windshield = pygame.Rect(rect.x + 8, rect.y + rect.height * 0.15, rect.width - 16, rect.height * 0.25)
    pygame.draw.rect(screen, (200, 240, 255), windshield, border_radius=6)

    if outline:
        pygame.draw.rect(screen, (20, 20, 20), rect, width=3, border_radius=6)


def render(screen: pygame.Surface, state: GameState) -> None:
    draw_background(screen)

    for enemy in sorted(state.enemies, key=lambda c: c.y):
        draw_car(screen, enemy)

    draw_car(screen, state.player, outline=True)

    draw_text(screen, f"Score: {int(state.score):05d}", 28, (20, 20))
    draw_text(screen, f"Level: {state.level}", 24, (20, 60))

    if state.status == "paused":
        draw_text(screen, "PAUSED", 64, (WIDTH // 2 - 120, HEIGHT // 2 - 40), pygame.Color(255, 220, 100))
        draw_text(screen, "Press P to continue", 28, (WIDTH // 2 - 150, HEIGHT // 2 + 20))
    elif state.status == "game_over":
        draw_text(screen, "CRASHED!", 64, (WIDTH // 2 - 160, HEIGHT // 2 - 80), pygame.Color(240, 80, 80))
        draw_text(screen, f"Final score: {int(state.score)}", 32, (WIDTH // 2 - 140, HEIGHT // 2))
        draw_text(screen, "Press R to restart", 28, (WIDTH // 2 - 150, HEIGHT // 2 + 50))


def main() -> None:
    pygame.init()
    pygame.mixer.quit()  # avoid audio init errors on systems without audio

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Lane Runner")
    clock = pygame.time.Clock()

    state = reset_state()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p and state.status in {"running", "paused"}:
                    state.status = "paused" if state.status == "running" else "running"
                elif event.key == pygame.K_r and state.status == "game_over":
                    state = reset_state()
                elif state.status == "running" and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    handle_player_input(state, event.key)

        if state.status == "running":
            update_state(state, dt)

        render(screen, state)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
