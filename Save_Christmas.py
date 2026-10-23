import pygame
import sys
import time
import math
import random

SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
SPEED = 15

#setup game window
pygame.init()

#screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

if pygame.joystick.get_count() != 8:
    print("ERROR: Incorrect number of joysticks")
    print("There are only " + str(pygame.joystick.get_count()) + " joysticks.")

class Snow:
    def __init__ (self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = 0
        red = random.randint(230, 255)
        green = random.randint(230, 255)
        blue = 255
        alpha = random.randint(10, 200)
        self.color = pygame.Color(red, green, blue, alpha)
        self.radius = int(random.random()*4)

    def update (self):
        self.x += random.random()*.4*SPEED - .2*SPEED
        self.y += random.random()*0.3*SPEED - 0.1*SPEED
        if (self.y > SCREEN_HEIGHT):
            del_flakes.append(self)

    def draw (self):
        x = int(self.x)
        y = int(self.y)
        pygame.draw.circle(screen, self.color, (x, y), self.radius)

class Score_Bar:
    def __init__(self):
        self.score = 0
        self.x = 1200
        self.y = SCREEN_HEIGHT - 256 - 28
        self.sprite = pygame.image.load("ScoreBar.png").convert_alpha()
        self.bar_sprite = pygame.image.load("Bar.png").convert_alpha()
        self.sprite = pygame.transform.scale(self.sprite, (64, 256))
        self.bar_sprite = pygame.transform.scale(self.bar_sprite, (64, 256))

    def update(self):
        self.score = score

    def draw(self):
        offset = 246 - score/max_score * 246 + 10
        bar = pygame.Rect(0, offset, 64, 256 - offset)
        screen.blit(self.bar_sprite, (self.x, self.y + offset), bar)
        screen.blit(self.sprite, (self.x, self.y))

class Sign:
    def __init__(self, file_name):
        self.x = 400
        self.y = 200
        self.width = 512
        self.height = 256
        self.sprite = pygame.image.load(file_name).convert_alpha()
        self.sprite = pygame.transform.scale(self.sprite, (self.width, self.height))
        self.visible = False
        self.sparkle = False

    def toggle(self):
        if self.visible:
            self.visible = False
            self.sparkle = False
        else:
            self.visible = True
            self.sparkle = True

    def update(self):
        make_sparkle(self)

    def draw(self):
        if (self.visible):
            screen.blit(self.sprite, (self.x, self.y))

class Star:
    def __init__(self):
        self.sprite = pygame.image.load("GoldStar.png").convert_alpha()
        self.width = 32
        self.height = 32
        self.delay = 10000/SPEED
        self.reset()
        self.visible = False
        self.sparkle = False

    def update(self):
        global score
        global max_score
        
        physics(self)
        make_sparkle(self)
        if score < max_score:
            self.count += 1
        if (self.count >= self.delay):
            if (self.power_up != None):
                self.power_up.jump_power /= 1.8
                self.power_up.max_vel /= 2
                self.power_up.sparkle = False
                self.power_up = None
                self.count = 0
            else:
                self.reset()
                star_sound.play()

        if (self.x < 0):
            self.x = 0
            self.vx *= -1
        elif (self.x > SCREEN_WIDTH - self.width):
            self.x = SCREEN_WIDTH - self.width
            self.vx *= -1

        if (self.y > SCREEN_HEIGHT):
            self.visible = False
            self.sparkle = False

        if (score >= max_score):
            self.visible = False
            self.sparkle = False

        if (self.visible and score < max_score):
            for elf in elves:
                if elf.active and collision(self, elf):
                    self.power_up = elf
                    elf.jump_power *= 1.8
                    elf.max_vel *= 2
                    elf.sparkle = True
                    self.count = 0
                    self.visible = False
                    self.sparkle = False
                    sparkle_sound.play()
                    elf.score += 10
                    break
        
    def draw(self):
        if (self.visible):
            screen.blit(self.sprite, (self.x, self.y))

    def reset(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = 0 - self.height
        self.vx = random.random()*0.5*SPEED - 0.25*SPEED
        self.max_vel = 0.5*SPEED
        self.vy = 0
        self.ax = 0
        self.angle = 0
        self.rotate = 0
        self.visible = True
        self.sparkle = True
        self.count = 0
        self.friction = 0
        self.power_up = None
        self.on_ground = False

class Sparkle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.random()*0.5*SPEED - 0.25*SPEED
        self.vy = random.random()*0.5*SPEED - 0.25*SPEED
        self.ax = 0
        self.max_vel = 0.5*SPEED
        self.friction = 0
        self.size = random.randint(5, 25)
        self.sprite = sparkle_sprite
        self.fade = -0.1*SPEED
        self.angle = 0
        self.rotate = random.randint(-5*SPEED, 5*SPEED)
        self.on_ground = False
        self.width = self.size
        self.height = self.size

    def update(self):
        physics(self)
        self.size += self.fade
        self.width = self.size
        self.height = self.size

        if (self.y > SCREEN_HEIGHT):
            del_sparkles.append(self)
        if (self.size <= 2):
            del_sparkles.append(self)

    def draw(self):
        size = int(self.size)
        sprite = pygame.transform.scale(self.sprite, (size, size))
        sprite = pygame.transform.rotate(sprite, self.angle)
        screen.blit(sprite, (self.x, self.y))

class Brick:
    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.sprite = sprite
        self.width = 32
        self.height = 32
        self.vx = 0

    def update(self):
        pass

    def draw(self):
        screen.blit(self.sprite, (self.x, self.y))

class Moving_Brick:
    def __init__(self, x, y, sprite, dist):
        self.x = x
        self.y = y
        self.y0 = y
        self.dist = dist
        self.x0 = x
        self.sprite = sprite
        self.width = 32
        self.height = 32
        self.vy = 0
        self.vx = 1
        self.ax = 0
        self.on_ground = False
        self.friction = 0
        self.angle = 0
        self.rotate = 0
        self.max_vel = 1

    def update(self):
        physics(self)
        self.y = self.y0
        if self.x < self.x0:
            self.x = self.x0
            self.vx *= -1
        if self.x > self.x0 + self.dist:
            self.x = self.x0 + self.dist
            self.vx *= -1

    def draw(self):
        screen.blit(self.sprite, (self.x, self.y))

class Elf:
    def __init__(self, sprites):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = 0 - 32
        self.frame_num = 0
        self.frame_delay = 40/SPEED
        self.frame_count = 0
        self.on_ground = False
        self.vx = 0
        self.vy = 0
        self.ax = 0
        self.dir = 1
        self.max_vel = 0.15*SPEED
        self.friction = 0.005*SPEED
        self.jump_power = 0.5*SPEED
        self.sprites = sprites
        self.sparkle = False
        self.angle = 0
        self.rotate = 0
        self.width = 40
        self.height = 80
        self.down = False
        self.down_count = 0
        self.active = True
        self.score = 0

    def jump(self):
        if (self.on_ground and not self.down):
            self.vy -= self.jump_power
            jump_sound.play()

    def fall(self):
        self.down = True
        self.down_count = 80

    def update(self):
        global score
        global max_score
        
        if self.down:
            self.down_count -= 1
            self.vx = 0
            self.ax = 0
            if self.down_count <= 0:
                self.down = False

        self.vy += 0.01
        
        if self.vx == 0:
            self.frame_num = 0

        if score < max_score:
            make_sparkle(self)

        if (self.on_ground and abs(self.ax) > 0.01):
            self.frame_count += 1
        if (self.frame_count >= self.frame_delay):
            self.frame_count = 0
            self.frame_num += 1
            if (self.frame_num == len(self.sprites)):
                self.frame_num = 0
        
        self.on_ground = False
        if (self.vy > 0):
            for brick in bricks:
                if (on_top_of(self,brick)):
                    self.y = brick.y - self.height
                    self.vy = 0
                    self.x += brick.vx
                    self.on_ground = True

        physics(self)

    def draw(self):
        sprite = self.sprites[self.frame_num]
        if (self.dir == -1):
            sprite = pygame.transform.flip(sprite, True, False) 
        
        if self.down:
            sprite = pygame.transform.rotate(sprite, 90)
            clip = pygame.Rect((96 - self.height)/2, (96 - self.width)/2, self.height, self.width)
            screen.blit(sprite, (self.x, self.y + self.height/2), clip)
        else:
            clip = pygame.Rect((96 - self.width)/2, (96 - self.height)/2, self.width, self.height)
            screen.blit(sprite, (self.x, self.y), clip)

        if victory_sign.visible:
            score_text = font.render(str(self.score), True, (255, 255, 255))
            screen.blit(score_text, (self.x + 10, self.y - 40))

class Present:
    def __init__(self, sprite):
        self.sprite = sprite
        self.width = 64
        self.height = 64
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = 0 - self.height
        self.vx = random.random()*0.5*SPEED - 0.25*SPEED
        self.max_vel = 0.5*SPEED
        self.vy = 0
        self.ax = 0
        self.angle = random.randint(0, 360)
        self.rotate = random.random()*2 - 1
        self.friction = 0
        self.on_ground = False

    def update(self):
        global score
        global max_score
        physics(self)

        if score < max_score:
            for elf in elves:
                if elf.active and collision(self, elf):
                    present_sound.play()
                    del_presents.append(self)
                    score += 3
                    elf.score += 3

        if self.y > SCREEN_HEIGHT:
            del_presents.append(self)

    def draw(self):
        sprite = pygame.transform.rotate(self.sprite, self.angle)
        screen.blit(sprite, (self.x, self.y))

class Ornament:
    def __init__(self, sprite):
        self.sprite = sprite
        self.width = 64
        self.height = 64
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = 0 - self.height
        self.vx = random.random()*0.5*SPEED - 0.25*SPEED
        self.max_vel = 0.5*SPEED
        self.vy = 0
        self.ax = 0
        self.angle = random.randint(0, 360)
        self.rotate = random.random()*2 - 1
        self.friction = 0
        self.on_ground = False

    def update(self):
        global score
        global max_score
        physics(self)

        if score < max_score:
            for elf in elves:
                if elf.active and collision(self, elf):
                    bonk_sound.play()
                    del_ornaments.append(self)
                    score -= 1
                    elf.score -= 1
                    elf.fall()
                    if score < 0:
                        score = 0
                    if elf.score < 0:
                        elf.score = 0

        if self.y > SCREEN_HEIGHT:
            del_ornaments.append(self)

    def draw(self):
        sprite = pygame.transform.rotate(self.sprite, self.angle)
        screen.blit(sprite, (self.x, self.y))

def collision(obj1, obj2):
    if (obj1.x + obj1.width > obj2.x and obj1.x < obj2.x + obj2.width):
        if (obj1.y + obj1.height > obj2.y and obj1.y < obj2.y + obj2.height):
            return True
    return False

def on_top_of(obj1, obj2):
    if (obj1.x + obj1.width > obj2.x and obj1.x < obj2.x + obj2.width):
        if (obj1.y + obj1.height > obj2.y and obj1.y + obj1.height < obj2.y + obj1.vy*3):
            return True
    return False

def physics(obj):
    if (score < max_score):
        gravity = 0.01*SPEED
        obj.vy += gravity
        obj.vx += obj.ax
        if (abs(obj.vx) > obj.max_vel):
            obj.vx = obj.dir*obj.max_vel
        obj.x += obj.vx
        if obj.x < 0:
            obj.x = 0
            obj.vx *= -1
        if obj.x > SCREEN_WIDTH - obj.width:
            obj.x = SCREEN_WIDTH - obj.width
            obj.vx *= -1
        obj.y += obj.vy
        obj.angle += obj.rotate
        if (abs(obj.vx) < 0.05*SPEED):
                obj.vx = 0
        if (obj.vx > 0):
            obj.dir = 1
            if obj.on_ground:
                obj.vx -= obj.friction
        elif (obj.vx < 0):
            obj.dir = -1
            if obj.on_ground:
                obj.vx += obj.friction

def make_sparkle(obj):
    if (obj.sparkle and len(sparkles) < max_sparkles):
            x = obj.x + random.randint(0, obj.width)
            y = obj.y + random.randint(0, obj.height)
            sparkles.append(Sparkle(x,y))

def winner():
    win = elves[0]
    for elf in elves:
        if elf.score > win.score:
            win = elf
    return win

def generate_bricks():
    for x in range(0, SCREEN_WIDTH, 32):
        bricks.append(Brick(x, SCREEN_HEIGHT - 32, brick_sprite))

    bricks.append(Brick(32, SCREEN_HEIGHT - 32*4, left_brick_sprite))
    for x in range(64, 32*9, 32):
        bricks.append(Brick(x, SCREEN_HEIGHT - 32*4, brick_sprite))
    bricks.append(Brick(32*9, SCREEN_HEIGHT - 32*4, right_brick_sprite))

    bricks.append(Brick(32*9, SCREEN_HEIGHT - 32*6, left_brick_sprite))
    for x in range(32*10, 32*14, 32):
        bricks.append(Brick(x, SCREEN_HEIGHT - 32*6, brick_sprite))
    bricks.append(Brick(32*14, SCREEN_HEIGHT - 32*6, right_brick_sprite))

    bricks.append(Brick(32*26, SCREEN_HEIGHT - 32*8, left_brick_sprite))
    for x in range(32*27, 32*30, 32):
        bricks.append(Brick(x, SCREEN_HEIGHT - 32*8, brick_sprite))
    bricks.append(Brick(32*30, SCREEN_HEIGHT - 32*8, right_brick_sprite))

    bricks.append(Brick(32*12, SCREEN_HEIGHT - 32*10, left_brick_sprite))
    for x in range(32*13, 32*14, 32):
        bricks.append(Brick(x, SCREEN_HEIGHT - 32*10, brick_sprite))
    bricks.append(Brick(32*14, SCREEN_HEIGHT - 32*10, right_brick_sprite))

    bricks.append(Moving_Brick(32*5, SCREEN_HEIGHT - 32*14, left_brick_sprite, 32*30))
    for x in range(32*6, 32*10, 32):
        bricks.append(Moving_Brick(x, SCREEN_HEIGHT - 32*14, brick_sprite, 32*30))
    bricks.append(Moving_Brick(32*10, SCREEN_HEIGHT - 32*14, right_brick_sprite, 32*30))


snow_flakes = []
del_flakes = []
sparkles = []
del_sparkles = []
max_sparkles = 15
bricks = []
delay = 0.25
max_flakes = 40
timer = time.time()
running = True
background = pygame.image.load("holiday.png").convert()
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT - 28))
sparkle_sprite = pygame.image.load("sparkle.png").convert_alpha()
brick_sprite = pygame.image.load("brick.png").convert_alpha()
left_brick_sprite = pygame.image.load("BrickLeft.png").convert_alpha()
right_brick_sprite = pygame.image.load("BrickRight.png").convert_alpha()

blue_elf_sprites = []
blue_elf_sprites.append(pygame.image.load("elves\BlueElf(1).png").convert_alpha())
blue_elf_sprites.append(pygame.image.load("elves\BlueElf(2).png").convert_alpha())
blue_elf_sprites.append(pygame.image.load("elves\BlueElf(3).png").convert_alpha())
blue_elf_sprites.append(pygame.image.load("elves\BlueElf(4).png").convert_alpha())

green_elf_sprites = []
green_elf_sprites.append(pygame.image.load("elves\GreenElf(1).png").convert_alpha())
green_elf_sprites.append(pygame.image.load("elves\GreenElf(2).png").convert_alpha())
green_elf_sprites.append(pygame.image.load("elves\GreenElf(3).png").convert_alpha())
green_elf_sprites.append(pygame.image.load("elves\GreenElf(4).png").convert_alpha())

orange_elf_sprites = []
orange_elf_sprites.append(pygame.image.load("elves\OrangeElf(1).png").convert_alpha())
orange_elf_sprites.append(pygame.image.load("elves\OrangeElf(2).png").convert_alpha())
orange_elf_sprites.append(pygame.image.load("elves\OrangeElf(3).png").convert_alpha())
orange_elf_sprites.append(pygame.image.load("elves\OrangeElf(4).png").convert_alpha())

pink_elf_sprites = []
pink_elf_sprites.append(pygame.image.load("elves\PinkElf(1).png").convert_alpha())
pink_elf_sprites.append(pygame.image.load("elves\PinkElf(2).png").convert_alpha())
pink_elf_sprites.append(pygame.image.load("elves\PinkElf(3).png").convert_alpha())
pink_elf_sprites.append(pygame.image.load("elves\PinkElf(4).png").convert_alpha())

purple_elf_sprites = []
purple_elf_sprites.append(pygame.image.load("elves\PurpleElf(1).png").convert_alpha())
purple_elf_sprites.append(pygame.image.load("elves\PurpleElf(2).png").convert_alpha())
purple_elf_sprites.append(pygame.image.load("elves\PurpleElf(3).png").convert_alpha())
purple_elf_sprites.append(pygame.image.load("elves\PurpleElf(4).png").convert_alpha())

red_elf_sprites = []
red_elf_sprites.append(pygame.image.load("elves\RedElf(1).png").convert_alpha())
red_elf_sprites.append(pygame.image.load("elves\RedElf(2).png").convert_alpha())
red_elf_sprites.append(pygame.image.load("elves\RedElf(3).png").convert_alpha())
red_elf_sprites.append(pygame.image.load("elves\RedElf(4).png").convert_alpha())

white_elf_sprites = []
white_elf_sprites.append(pygame.image.load("elves\WhiteElf(1).png").convert_alpha())
white_elf_sprites.append(pygame.image.load("elves\WhiteElf(2).png").convert_alpha())
white_elf_sprites.append(pygame.image.load("elves\WhiteElf(3).png").convert_alpha())
white_elf_sprites.append(pygame.image.load("elves\WhiteElf(4).png").convert_alpha())

yellow_elf_sprites = []
yellow_elf_sprites.append(pygame.image.load("elves\YellowElf(1).png").convert_alpha())
yellow_elf_sprites.append(pygame.image.load("elves\YellowElf(2).png").convert_alpha())
yellow_elf_sprites.append(pygame.image.load("elves\YellowElf(3).png").convert_alpha())
yellow_elf_sprites.append(pygame.image.load("elves\YellowElf(4).png").convert_alpha())

present_sprites = []
present_sprites.append(pygame.image.load("presents\BluePresent.png").convert_alpha())
present_sprites.append(pygame.image.load("presents\GreenPresent.png").convert_alpha())
present_sprites.append(pygame.image.load("presents\OrangePresent.png").convert_alpha())
present_sprites.append(pygame.image.load("presents\PinkPresent.png").convert_alpha())
present_sprites.append(pygame.image.load("presents\PurplePresent.png").convert_alpha())
present_sprites.append(pygame.image.load("presents\RedPresent.png").convert_alpha())

ornament_sprites = []
ornament_sprites.append(pygame.image.load("ornaments\BlueOrnament.png").convert_alpha())
ornament_sprites.append(pygame.image.load("ornaments\GreenOrnament.png").convert_alpha())
ornament_sprites.append(pygame.image.load("ornaments\RedOrnament.png").convert_alpha())
ornament_sprites.append(pygame.image.load("ornaments\PinkOrnament.png").convert_alpha())

pygame.mixer.init()

bonk_sound = pygame.mixer.Sound("Bonk.wav")
jump_sound = pygame.mixer.Sound("Jump.wav")
present_sound = pygame.mixer.Sound("Present.wav")
sparkle_sound = pygame.mixer.Sound("Sparkle.wav")
star_sound = pygame.mixer.Sound("star.wav")
victory_sound = pygame.mixer.Sound("victory.wav")

pygame.mixer.music.load("holiday.wav")

elves = []
elves.append(Elf(blue_elf_sprites))
elves.append(Elf(green_elf_sprites))
elves.append(Elf(orange_elf_sprites))
elves.append(Elf(pink_elf_sprites))
elves.append(Elf(purple_elf_sprites))
elves.append(Elf(red_elf_sprites))
elves.append(Elf(white_elf_sprites))
elves.append(Elf(yellow_elf_sprites))

presents = []
del_presents = []
present_delay = 100
max_presents = 5
present_count = 0

ornaments = []
del_ornaments = []
ornament_delay = 120
max_ornaments = 4
ornament_count = 0

score = 150
max_score = 150
score_bar = Score_Bar()
victory_sign = Sign("Sign.png")
directions_sign = Sign("Directions.png")
directions_sign.toggle()
star = Star()

pygame.font.init()
font = pygame.font.SysFont("comicsansms", 24)

pygame.joystick.init()                   

generate_bricks()

clock = pygame.time.Clock()
FPS = 60

pygame.mouse.set_visible(False)
pygame.mixer.music.play(-1)
while (running):
    #process input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
            
        if event.type == pygame.JOYBUTTONDOWN and event.button == 9 and score >= max_score:
            if victory_sign.visible:
                victory_sound.stop()
                victory_sign.toggle()
                directions_sign.toggle()
                winner().sparkle = False
                for elf in elves:
                    elf.score = 0
            elif directions_sign.visible:
                score = 0
            
                for elf in elves:
                    elf.y = 0 - elf.height
                directions_sign.toggle()

        if event.type == pygame.JOYBUTTONDOWN and event.button == 8:
            print(event.joy)
            elf = elves[event.joy]
            if elf.active:
                elf.active = False
            else:
                elf.active = True

        if event.type == pygame.JOYBUTTONDOWN and event.button < 8:
            elves[event.joy].jump()
            
        if event.type == pygame.JOYAXISMOTION and event.axis == 0:
            if (abs(event.value) > 0.1):
                elves[event.joy].ax = 0.08*SPEED * event.value
            else:
                elves[event.joy].ax = 0

    if score >= max_score and not victory_sign.visible and not directions_sign.visible:
        victory_sign.toggle()
        victory_sound.play()
        winner().sparkle = True

    if score >= max_score:
        for i in range(len(elves)):
            elf = elves[i]
            elf.x = 100 + i*120
            elf.y = 80
        make_sparkle(winner())
    
    present_count += 1
    if present_count >= present_delay:
        present_count = random.randint(0, present_delay*0.8)
        if len(presents) < max_presents:
            presents.append(Present(present_sprites[random.randint(0, 5)]))

    ornament_count += 1
    if ornament_count >= ornament_delay:
        ornament_count = random.randint(0, ornament_delay*0.5)
        if len(ornaments) < max_ornaments:
            ornaments.append(Ornament(ornament_sprites[random.randint(0, 3)]))

    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
    
    delta = time.time() - timer
    if (delta >= delay):
        timer = time.time()
        if (len(snow_flakes) < max_flakes):
            snow_flakes.append(Snow())
    
    pygame.draw.rect(screen, pygame.Color(0, 0, 0), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(background, (0, 0))

    score_bar.update()
    score_bar.draw()

    for brick in bricks:
        brick.update()
        brick.draw()

    for elf in elves:
        if elf.active:
            elf.update()
            elf.draw()

    for present in presents:
        present.update()
        if score < max_score:
            present.draw()

    for ornament in ornaments:
        ornament.update()
        if score < max_score:
            ornament.draw()

    victory_sign.update()
    victory_sign.draw()

    directions_sign.update()
    directions_sign.draw()

    star.update()
    star.draw()

    for sparkle in sparkles:
        sparkle.update()
        sparkle.draw()

    for sparkle in del_sparkles:
        if (sparkle in sparkles):
            sparkles.remove(sparkle)
    del_sparkles.clear()
    
    for flake in snow_flakes:
        flake.update()
        flake.draw()

    for flake in del_flakes:
        if (flake in snow_flakes):
            snow_flakes.remove(flake)
    del_flakes.clear()

    for present in del_presents:
        if (present in presents):
            presents.remove(present)
    del_presents.clear()

    for ornament in del_ornaments:
        if (ornament in ornaments):
            ornaments.remove(ornament)
    del_ornaments.clear()

    pygame.display.update()

    clock.tick(FPS)

pygame.mixer.music.stop()
pygame.quit()
sys.exit(0)
