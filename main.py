"""
Save Christmas - Holiday in the Den 2019
North Paulding High School Computer Science Honor Society

Santa's sleigh is out of control! Up to 8 elves work together to catch the
falling presents and dodge the ornaments until the score bar is full.

Runs two ways from this same file:
  * PC:      python main.py            (add --fullscreen for the event screen)
  * Browser: pygbag .                  (builds build/web, playable in any modern browser)

Controls
  Start / continue   ENTER, SPACE, mouse click, or gamepad START (button 9)
  Keyboard players   P1: A D move, W jump      P2: arrow keys
                     P3: J L move, I jump      P4: numpad 4 6 move, 8 jump
                     (a keyboard player joins the first time they press a key)
  Gamepads           stick or d-pad to move, any face/shoulder button to jump,
                     SELECT (button 8) to sit out / rejoin
  PC only            F11 toggles fullscreen, ESC quits
"""

import asyncio
import math
import os
import random
import sys

import pygame

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
FPS = 60
SPEED = 15                 # overall game speed; every motion constant scales with it

MAX_SCORE = 150            # team score needed to save Christmas
PRESENT_POINTS = 3
ORNAMENT_PENALTY = 1
STAR_POINTS = 10

MAX_SPARKLES = 15
MAX_FLAKES = 40
FLAKE_DELAY_FRAMES = 15    # a new snowflake every quarter second

PRESENT_DELAY = 100
MAX_PRESENTS = 5
ORNAMENT_DELAY = 120
MAX_ORNAMENTS = 4

GROUND_HEIGHT = 28         # strip at the bottom of the background image

IS_WEB = sys.platform == "emscripten"

# Gamepad buttons (generic USB pads used at the event, and the browser's standard mapping)
BUTTON_SELECT = 8
BUTTON_START = 9
BUTTON_DPAD_LEFT = 14      # browser standard mapping
BUTTON_DPAD_RIGHT = 15
JUMP_BUTTONS = range(0, 8)
AXIS_DEADZONE = 0.1

# Keyboard players: (left keys, right keys, jump keys)
KEYBOARD_SCHEMES = [
    ((pygame.K_a,), (pygame.K_d,), (pygame.K_w,)),
    ((pygame.K_LEFT,), (pygame.K_RIGHT,), (pygame.K_UP,)),
    ((pygame.K_j,), (pygame.K_l,), (pygame.K_i,)),
    ((pygame.K_KP4,), (pygame.K_KP6,), (pygame.K_KP8,)),
]
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)

ELF_COLORS = ["Blue", "Green", "Orange", "Pink", "Purple", "Red", "White", "Yellow"]
PRESENT_COLORS = ["Blue", "Green", "Orange", "Pink", "Purple", "Red"]
ORNAMENT_COLORS = ["Blue", "Green", "Red", "Pink"]

# Game states
DIRECTIONS = "directions"
PLAYING = "playing"
VICTORY = "victory"


def base_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.getcwd()


ASSET_DIR = os.path.join(base_dir(), "assets")


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

class SilentSound:
    """Stand-in used when the computer has no audio device."""

    def play(self, *args, **kwargs):
        pass

    def stop(self):
        pass


class Assets:
    def __init__(self):
        img = self.image
        self.background = pygame.transform.scale(
            img("holiday.png", alpha=False), (SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT))
        self.sparkle = img("Sparkle.png")
        self.brick = img("Brick.png")
        self.brick_left = img("BrickLeft.png")
        self.brick_right = img("BrickRight.png")
        self.star = img("GoldStar.png")
        self.score_bar = pygame.transform.scale(img("ScoreBar.png"), (64, 256))
        self.score_fill = pygame.transform.scale(img("Bar.png"), (64, 256))
        self.victory_sign = pygame.transform.scale(img("Sign.png"), (512, 256))
        self.directions_sign = pygame.transform.scale(img("Directions.png"), (512, 256))

        self.elves = [[img("elves", f"{color}Elf({n}).png") for n in range(1, 5)]
                      for color in ELF_COLORS]
        self.presents = [img("presents", f"{color}Present.png") for color in PRESENT_COLORS]
        self.ornaments = [img("ornaments", f"{color}Ornament.png") for color in ORNAMENT_COLORS]

        self.audio = pygame.mixer.get_init() is not None
        self.bonk = self.sound("bonk.ogg")
        self.jump = self.sound("jump.ogg")
        self.present = self.sound("present.ogg")
        self.sparkle_sound = self.sound("sparkle.ogg")
        self.star_sound = self.sound("star.ogg")
        self.victory = self.sound("victory.ogg")
        self.music = os.path.join(ASSET_DIR, "sounds", "holiday.ogg")

        self.font = make_font(24)
        self.small_font = make_font(22)

    @staticmethod
    def image(*parts, alpha=True):
        surface = pygame.image.load(os.path.join(ASSET_DIR, "images", *parts))
        return surface.convert_alpha() if alpha else surface.convert()

    def sound(self, name):
        if not self.audio:
            return SilentSound()
        return pygame.mixer.Sound(os.path.join(ASSET_DIR, "sounds", name))

    def play_music(self):
        if not self.audio:
            return
        try:
            pygame.mixer.music.load(self.music)
            pygame.mixer.music.play(-1)
        except pygame.error as err:
            print("Music could not play:", err)


def make_font(size):
    if not IS_WEB:
        try:
            if pygame.font.match_font("comicsansms"):
                return pygame.font.SysFont("comicsansms", size)
        except Exception:
            pass
    return pygame.font.Font(None, int(size * 1.35))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def collision(a, b):
    return (a.x + a.width > b.x and a.x < b.x + b.width
            and a.y + a.height > b.y and a.y < b.y + b.height)


def on_top_of(a, b):
    """True when a is falling onto the top edge of b this frame."""
    return (a.x + a.width > b.x and a.x < b.x + b.width
            and a.y + a.height > b.y and a.y + a.height < b.y + a.vy * 3)


class Body:
    """Anything that moves with the shared 2019 physics."""

    def __init__(self, game, x, y, width, height):
        self.game = game
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.vx = self.vy = self.ax = 0.0
        self.max_vel = 0.5 * SPEED
        self.friction = 0.0
        self.angle = 0.0
        self.rotate = 0.0
        self.on_ground = False
        self.dir = 1
        self.sparkle = False

    def physics(self):
        if self.game.frozen:
            return
        self.vy += 0.01 * SPEED
        self.vx += self.ax
        if abs(self.vx) > self.max_vel:
            self.vx = math.copysign(self.max_vel, self.vx)
        self.x += self.vx
        if self.x < 0:
            self.x = 0
            self.vx *= -1
        if self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
            self.vx *= -1
        self.y += self.vy
        self.angle += self.rotate
        if abs(self.vx) < 0.05 * SPEED:
            self.vx = 0
        if self.vx > 0:
            self.dir = 1
            if self.on_ground:
                self.vx -= self.friction
        elif self.vx < 0:
            self.dir = -1
            if self.on_ground:
                self.vx += self.friction

    def make_sparkle(self):
        self.game.add_sparkle(self)


# ---------------------------------------------------------------------------
# Game objects
# ---------------------------------------------------------------------------

class Snow:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = 0.0
        self.color = pygame.Color(random.randint(230, 255), random.randint(230, 255), 255,
                                  random.randint(10, 200))
        self.radius = int(random.random() * 4)
        self.dead = False

    def update(self):
        self.x += random.random() * 0.4 * SPEED - 0.2 * SPEED
        self.y += random.random() * 0.3 * SPEED - 0.1 * SPEED
        if self.y > SCREEN_HEIGHT:
            self.dead = True

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)


class Sparkle(Body):
    def __init__(self, game, x, y):
        size = random.randint(5, 25)
        super().__init__(game, x, y, size, size)
        self.size = float(size)
        self.vx = random.random() * 0.5 * SPEED - 0.25 * SPEED
        self.vy = random.random() * 0.5 * SPEED - 0.25 * SPEED
        self.rotate = random.randint(-5 * SPEED, 5 * SPEED)
        self.dead = False

    def update(self):
        self.physics()
        self.size -= 0.1 * SPEED
        self.width = self.height = self.size
        if self.y > SCREEN_HEIGHT or self.size <= 2:
            self.dead = True

    def draw(self, screen):
        size = max(1, int(self.size))
        sprite = pygame.transform.scale(self.game.assets.sparkle, (size, size))
        screen.blit(pygame.transform.rotate(sprite, self.angle), (self.x, self.y))


class ScoreBar:
    def __init__(self, game):
        self.game = game
        self.x = 1200
        self.y = SCREEN_HEIGHT - 256 - GROUND_HEIGHT

    def draw(self, screen):
        ratio = min(max(self.game.score / MAX_SCORE, 0), 1)
        offset = 246 - ratio * 246 + 10
        fill = pygame.Rect(0, offset, 64, 256 - offset)
        screen.blit(self.game.assets.score_fill, (self.x, self.y + offset), fill)
        screen.blit(self.game.assets.score_bar, (self.x, self.y))


class Sign:
    def __init__(self, game, sprite):
        self.game = game
        self.sprite = sprite
        self.x, self.y = 400, 200
        self.width, self.height = 512, 256
        self.visible = False
        self.sparkle = False

    def show(self, visible):
        self.visible = self.sparkle = visible

    def update(self):
        self.game.add_sparkle(self)

    def draw(self, screen):
        if self.visible:
            screen.blit(self.sprite, (self.x, self.y))


class Brick:
    def __init__(self, x, y, sprite):
        self.x, self.y = x, y
        self.sprite = sprite
        self.width = self.height = 32
        self.vx = 0

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))


class MovingBrick(Body):
    def __init__(self, game, x, y, sprite, dist):
        super().__init__(game, x, y, 32, 32)
        self.sprite = sprite
        self.x0, self.y0 = x, y
        self.dist = dist
        self.vx = 1
        self.max_vel = 1

    def update(self):
        self.physics()
        self.y = self.y0
        self.vy = 0
        if self.x < self.x0:
            self.x = self.x0
            self.vx *= -1
        if self.x > self.x0 + self.dist:
            self.x = self.x0 + self.dist
            self.vx *= -1

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))


class Elf(Body):
    def __init__(self, game, sprites, color):
        super().__init__(game, random.randint(0, SCREEN_WIDTH), -32, 40, 80)
        self.sprites = sprites
        self.color = color
        self.frame_num = 0
        self.frame_delay = 40 / SPEED
        self.frame_count = 0
        self.max_vel = 0.15 * SPEED
        self.friction = 0.005 * SPEED
        self.jump_power = 0.5 * SPEED
        self.down = False
        self.down_count = 0
        self.active = False
        self.score = 0
        self.input_x = 0.0     # -1..1 from whoever controls this elf

    def jump(self):
        if self.on_ground and not self.down:
            self.vy -= self.jump_power
            self.game.assets.jump.play()

    def fall(self):
        self.down = True
        self.down_count = 80

    def update(self):
        if self.down:
            self.down_count -= 1
            self.vx = 0
            self.ax = 0
            if self.down_count <= 0:
                self.down = False
        else:
            self.ax = 0.08 * SPEED * self.input_x

        self.vy += 0.01

        if self.vx == 0:
            self.frame_num = 0

        if not self.game.frozen:
            self.make_sparkle()

        if self.on_ground and abs(self.ax) > 0.01:
            self.frame_count += 1
        if self.frame_count >= self.frame_delay:
            self.frame_count = 0
            self.frame_num = (self.frame_num + 1) % len(self.sprites)

        self.on_ground = False
        if self.vy > 0:
            for brick in self.game.bricks:
                if on_top_of(self, brick):
                    self.y = brick.y - self.height
                    self.vy = 0
                    self.x += brick.vx
                    self.on_ground = True

        self.physics()

    def draw(self, screen):
        sprite = self.sprites[self.frame_num]
        if self.dir == -1:
            sprite = pygame.transform.flip(sprite, True, False)

        if self.down:
            sprite = pygame.transform.rotate(sprite, 90)
            clip = pygame.Rect((96 - self.height) / 2, (96 - self.width) / 2, self.height, self.width)
            screen.blit(sprite, (self.x, self.y + self.height / 2), clip)
        else:
            clip = pygame.Rect((96 - self.width) / 2, (96 - self.height) / 2, self.width, self.height)
            screen.blit(sprite, (self.x, self.y), clip)

        if self.game.state == VICTORY:
            text = self.game.assets.font.render(str(self.score), True, (255, 255, 255))
            screen.blit(text, (self.x + 10, self.y - 40))


class Faller(Body):
    """A present or an ornament tumbling out of Santa's sleigh."""

    def __init__(self, game, sprite):
        super().__init__(game, random.randint(0, SCREEN_WIDTH), -64, 64, 64)
        self.sprite = sprite
        self.vx = random.random() * 0.5 * SPEED - 0.25 * SPEED
        self.angle = random.randint(0, 360)
        self.rotate = random.random() * 2 - 1
        self.dead = False

    def update(self):
        self.physics()
        if self.game.state == PLAYING:
            for elf in self.game.active_elves():
                if collision(self, elf):
                    self.caught_by(elf)
                    self.dead = True
                    break
        if self.y > SCREEN_HEIGHT:
            self.dead = True

    def caught_by(self, elf):
        pass

    def draw(self, screen):
        if self.game.state == PLAYING:
            screen.blit(pygame.transform.rotate(self.sprite, self.angle), (self.x, self.y))


class Present(Faller):
    def caught_by(self, elf):
        self.game.assets.present.play()
        self.game.add_score(PRESENT_POINTS)
        elf.score += PRESENT_POINTS


class Ornament(Faller):
    def caught_by(self, elf):
        self.game.assets.bonk.play()
        self.game.add_score(-ORNAMENT_PENALTY)
        elf.score = max(0, elf.score - ORNAMENT_PENALTY)
        elf.fall()


class Star(Body):
    """Gold star power-up: higher jumps and double speed for a while."""

    def __init__(self, game):
        super().__init__(game, 0, -32, 32, 32)
        self.sprite = game.assets.star
        self.delay = 10000 / SPEED
        self.power_up = None
        self.reset()
        self.visible = False
        self.sparkle = False

    def reset(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = -self.height
        self.vx = random.random() * 0.5 * SPEED - 0.25 * SPEED
        self.vy = 0
        self.visible = True
        self.sparkle = True
        self.count = 0

    def end_power_up(self):
        if self.power_up is not None:
            self.power_up.jump_power /= 1.8
            self.power_up.max_vel /= 2
            self.power_up.sparkle = False
            self.power_up = None
        self.count = 0

    def update(self):
        game = self.game
        self.physics()
        self.make_sparkle()
        if game.state == PLAYING:
            self.count += 1
        if self.count >= self.delay:
            if self.power_up is not None:
                self.end_power_up()
            else:
                self.reset()
                game.assets.star_sound.play()

        if self.y > SCREEN_HEIGHT or game.state != PLAYING:
            self.visible = self.sparkle = False

        if self.visible and game.state == PLAYING:
            for elf in game.active_elves():
                if collision(self, elf):
                    self.power_up = elf
                    elf.jump_power *= 1.8
                    elf.max_vel *= 2
                    elf.sparkle = True
                    elf.score += STAR_POINTS
                    self.count = 0
                    self.visible = self.sparkle = False
                    game.assets.sparkle_sound.play()
                    break

    def draw(self, screen):
        if self.visible:
            screen.blit(self.sprite, (self.x, self.y))


# ---------------------------------------------------------------------------
# Players: gamepads and keyboard schemes, each driving one elf
# ---------------------------------------------------------------------------

class Controls:
    def __init__(self, game):
        self.game = game
        self.joysticks = {}        # instance_id -> pygame Joystick
        self.joy_slot = {}         # instance_id -> elf index
        self.key_slot = {}         # keyboard scheme index -> elf index
        self.held = set()

    def taken_slots(self):
        return set(self.joy_slot.values()) | set(self.key_slot.values())

    def free_slot(self):
        taken = self.taken_slots()
        for i in range(len(self.game.elves)):
            if i not in taken:
                return i
        return None

    # -- gamepads --
    def add_joystick(self, device_index):
        joystick = pygame.joystick.Joystick(device_index)
        joystick.init()
        iid = joystick.get_instance_id()
        if iid in self.joysticks:
            return
        self.joysticks[iid] = joystick
        slot = self.free_slot()
        if slot is not None:
            self.joy_slot[iid] = slot
            self.game.elves[slot].active = True
        print(f"Gamepad connected: {joystick.get_name()} -> elf {slot}")

    def remove_joystick(self, iid):
        self.joysticks.pop(iid, None)
        slot = self.joy_slot.pop(iid, None)
        if slot is not None:
            elf = self.game.elves[slot]
            elf.active = False
            elf.input_x = 0

    def joy_elf(self, event):
        iid = getattr(event, "instance_id", getattr(event, "joy", None))
        slot = self.joy_slot.get(iid)
        return None if slot is None else self.game.elves[slot]

    # -- keyboard --
    def key_scheme(self, key):
        for index, (left, right, jump) in enumerate(KEYBOARD_SCHEMES):
            if key in left or key in right or key in jump:
                return index
        return None

    def key_elf(self, scheme, join):
        slot = self.key_slot.get(scheme)
        if slot is None and join:
            slot = self.free_slot()
            if slot is None:
                return None
            self.key_slot[scheme] = slot
            self.game.elves[slot].active = True
        return None if slot is None else self.game.elves[slot]

    def update_keyboard(self):
        for scheme, slot in self.key_slot.items():
            left, right, _ = KEYBOARD_SCHEMES[scheme]
            x = (any(k in self.held for k in right)) - (any(k in self.held for k in left))
            self.game.elves[slot].input_x = float(x)

    def handle(self, event):
        game = self.game
        if event.type == pygame.JOYDEVICEADDED:
            self.add_joystick(event.device_index)
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.remove_joystick(event.instance_id)

        elif event.type == pygame.JOYBUTTONDOWN:
            elf = self.joy_elf(event)
            if event.button == BUTTON_START:
                game.press_start()
            elif event.button == BUTTON_SELECT and elf is not None:
                elf.active = not elf.active
            elif elf is not None and elf.active:
                if event.button in JUMP_BUTTONS:
                    elf.jump()
                elif event.button == BUTTON_DPAD_LEFT:
                    elf.input_x = -1.0
                elif event.button == BUTTON_DPAD_RIGHT:
                    elf.input_x = 1.0
        elif event.type == pygame.JOYBUTTONUP:
            elf = self.joy_elf(event)
            if elf is not None and event.button in (BUTTON_DPAD_LEFT, BUTTON_DPAD_RIGHT):
                elf.input_x = 0.0
        elif event.type == pygame.JOYAXISMOTION and event.axis == 0:
            elf = self.joy_elf(event)
            if elf is not None:
                elf.input_x = event.value if abs(event.value) > AXIS_DEADZONE else 0.0
        elif event.type == pygame.JOYHATMOTION:
            elf = self.joy_elf(event)
            if elf is not None:
                elf.input_x = float(event.value[0])

        elif event.type == pygame.KEYDOWN:
            self.held.add(event.key)
            if event.key in START_KEYS:
                game.press_start()
                return
            scheme = self.key_scheme(event.key)
            if scheme is not None:
                elf = self.key_elf(scheme, join=True)
                if elf is not None and event.key in KEYBOARD_SCHEMES[scheme][2]:
                    elf.jump()
        elif event.type == pygame.KEYUP:
            self.held.discard(event.key)

        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            game.press_start()


# ---------------------------------------------------------------------------
# The game
# ---------------------------------------------------------------------------

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.assets = Assets()
        self.state = DIRECTIONS
        self.score = MAX_SCORE          # the bar starts full behind the directions sign

        self.elves = [Elf(self, sprites, color)
                      for sprites, color in zip(self.assets.elves, ELF_COLORS)]
        self.controls = Controls(self)
        self.bricks = self.build_level()
        self.presents = []
        self.ornaments = []
        self.sparkles = []
        self.flakes = []
        self.present_count = 0
        self.ornament_count = 0
        self.flake_count = 0

        self.score_bar = ScoreBar(self)
        self.victory_sign = Sign(self, self.assets.victory_sign)
        self.directions_sign = Sign(self, self.assets.directions_sign)
        self.directions_sign.show(True)
        self.star = Star(self)

    # -- state --
    @property
    def frozen(self):
        return self.state != PLAYING

    def active_elves(self):
        return [elf for elf in self.elves if elf.active]

    def add_score(self, points):
        self.score = max(0, self.score + points)

    def add_sparkle(self, obj):
        if obj.sparkle and len(self.sparkles) < MAX_SPARKLES:
            x = obj.x + random.randint(0, int(obj.width))
            y = obj.y + random.randint(0, int(obj.height))
            self.sparkles.append(Sparkle(self, x, y))

    def winner(self):
        return max(self.elves, key=lambda elf: elf.score)

    def press_start(self):
        if self.state == VICTORY:
            self.assets.victory.stop()
            self.victory_sign.show(False)
            self.directions_sign.show(True)
            self.winner().sparkle = False
            for elf in self.elves:
                elf.score = 0
            self.state = DIRECTIONS
        elif self.state == DIRECTIONS and self.active_elves():
            self.start_round()

    def back_to_directions(self):
        self.victory_sign.show(False)
        self.directions_sign.show(True)
        self.star.end_power_up()
        self.score = MAX_SCORE
        self.state = DIRECTIONS

    def start_round(self):
        self.score = 0
        self.presents.clear()
        self.ornaments.clear()
        self.star.end_power_up()
        self.star.visible = self.star.sparkle = False
        for elf in self.elves:
            elf.y = -elf.height
            elf.vx = elf.vy = 0
            elf.down = False
            elf.sparkle = False
        self.directions_sign.show(False)
        self.state = PLAYING

    def win(self):
        self.state = VICTORY
        self.victory_sign.show(True)
        self.assets.victory.play()
        self.star.end_power_up()
        for elf in self.elves:
            elf.sparkle = False
        self.winner().sparkle = True

    # -- level --
    def build_level(self):
        a = self.assets
        bricks = []

        def platform(row, first, last, moving_dist=None):
            y = SCREEN_HEIGHT - 32 * row
            for col in range(first, last + 1):
                sprite = a.brick_left if col == first else a.brick_right if col == last else a.brick
                if moving_dist is None:
                    bricks.append(Brick(32 * col, y, sprite))
                else:
                    bricks.append(MovingBrick(self, 32 * col, y, sprite, moving_dist))

        for x in range(0, SCREEN_WIDTH, 32):
            bricks.append(Brick(x, SCREEN_HEIGHT - 32, a.brick))
        platform(4, 1, 9)
        platform(6, 9, 14)
        platform(8, 26, 30)
        platform(10, 12, 14)
        platform(14, 5, 10, moving_dist=32 * 30)
        return bricks

    # -- loop --
    def handle_event(self, event):
        self.controls.handle(event)

    def spawn(self):
        self.present_count += 1
        if self.present_count >= PRESENT_DELAY:
            self.present_count = random.randint(0, int(PRESENT_DELAY * 0.8))
            if len(self.presents) < MAX_PRESENTS:
                self.presents.append(Present(self, random.choice(self.assets.presents)))

        self.ornament_count += 1
        if self.ornament_count >= ORNAMENT_DELAY:
            self.ornament_count = random.randint(0, int(ORNAMENT_DELAY * 0.5))
            if len(self.ornaments) < MAX_ORNAMENTS:
                self.ornaments.append(Ornament(self, random.choice(self.assets.ornaments)))

        self.flake_count += 1
        if self.flake_count >= FLAKE_DELAY_FRAMES:
            self.flake_count = 0
            if len(self.flakes) < MAX_FLAKES:
                self.flakes.append(Snow())

    def update(self):
        self.controls.update_keyboard()

        if self.state == PLAYING and self.score >= MAX_SCORE:
            self.win()
        elif self.state == PLAYING and not self.active_elves():
            self.back_to_directions()      # everyone left; don't get stuck mid-round

        if self.state != PLAYING:
            for i, elf in enumerate(self.elves):
                elf.x = 100 + i * 120
                elf.y = 80
            if self.state == VICTORY:
                self.add_sparkle(self.winner())

        self.spawn()

        for brick in self.bricks:
            brick.update()
        for elf in self.active_elves():
            elf.update()
        for thing in self.presents + self.ornaments:
            thing.update()
        self.victory_sign.update()
        self.directions_sign.update()
        self.star.update()
        for sparkle in self.sparkles:
            sparkle.update()
        for flake in self.flakes:
            flake.update()

        self.presents = [p for p in self.presents if not p.dead]
        self.ornaments = [o for o in self.ornaments if not o.dead]
        self.sparkles = [s for s in self.sparkles if not s.dead]
        self.flakes = [f for f in self.flakes if not f.dead]

    def draw(self):
        screen = self.screen
        screen.fill((0, 0, 0))
        screen.blit(self.assets.background, (0, 0))
        self.score_bar.draw(screen)
        for brick in self.bricks:
            brick.draw(screen)
        for elf in self.active_elves():
            elf.draw(screen)
        for thing in self.presents + self.ornaments:
            thing.draw(screen)
        self.victory_sign.draw(screen)
        self.directions_sign.draw(screen)
        self.star.draw(screen)
        for sparkle in self.sparkles:
            sparkle.draw(screen)
        for flake in self.flakes:
            flake.draw(screen)
        self.draw_hints(screen)

    def draw_hints(self, screen):
        if self.state == PLAYING:
            return
        if self.state == DIRECTIONS:
            if self.active_elves():
                first = "Press ENTER, click, or press START on a gamepad to play"
            else:
                first = "Press a player's keys or connect a gamepad to add an elf"
            lines = [first,
                     "Keyboard: P1  W A D    P2  arrow keys    P3  I J L    P4  numpad 8 4 6",
                     "Gamepads: stick or d-pad to move, buttons to jump, SELECT to sit out"]
        else:
            lines = ["Press ENTER, click, or START to play again"]
        font = self.assets.small_font
        texts = [font.render(line, True, (255, 255, 255)) for line in lines]
        gap = 6
        width = max(t.get_width() for t in texts) + 40
        height = sum(t.get_height() for t in texts) + gap * (len(texts) - 1) + 20
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((10, 20, 40, 185))
        top = 468
        screen.blit(panel, ((SCREEN_WIDTH - width) // 2, top))
        y = top + 10
        for text in texts:
            screen.blit(text, ((SCREEN_WIDTH - text.get_width()) // 2, y))
            y += text.get_height() + gap


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def open_window(fullscreen):
    if IS_WEB:
        return pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    flags = pygame.SCALED
    flags |= pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.mouse.set_visible(not fullscreen)
    return screen


async def main(fullscreen=False, max_frames=None):
    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error as err:
        print("No audio device, playing without sound:", err)
    pygame.joystick.init()
    pygame.display.set_caption("Save Christmas - Holiday in the Den 2019")

    screen = open_window(fullscreen)
    game = Game(screen)
    game.assets.play_music()
    clock = pygame.time.Clock()

    frames = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not IS_WEB and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and not IS_WEB and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            else:
                game.handle_event(event)

        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)     # hands control back to the browser each frame

        frames += 1
        if max_frames is not None and frames >= max_frames:
            running = False

    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main(fullscreen="--fullscreen" in sys.argv))
