# === PART 1: BASE SETUP ===
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random, sys, math

WIDTH, HEIGHT = 640, 480
HERO_SIZE = 32
HERO_SPEED = 12
MAX_STARS = 200

hero = {"size": HERO_SIZE, "color": (1,1,1), "world_x":0, "world_y":0}
stars, shots = [], []
keys = {}
enemies, enemy_shots = [], []
zones = {}

# === PART 2: ENEMIES (Mother, Shield, Sword) ===
def spawn_mother(x, y):
    dx = random.choice([-2,2])
    dy = random.choice([-2,2])
    enemies.append({
        "x":x,"y":y,"size":28,"color":(1,0,1),
        "isMother":True,"active":True,"dx":dx,"dy":dy,
        "hp": 50,
        "shield_cooldown": 0,
        "attack_cooldown": 0
    })

def fire_sword(mother):
    cx, cy = WIDTH//2, HEIGHT//2
    angle = math.atan2(cy - mother["y"], cx - mother["x"])
    enemy_shots.append({
        "x": mother["x"],
        "y": mother["y"],
        "angle": angle,
        "swing_phase": 0,
        "active": True,
        "parent": mother
    })

# === PART 3: UPDATES & COLLISIONS ===
def update_enemies():
    cx, cy = WIDTH//2, HEIGHT//2
    for e in enemies:
        if not e["active"]:
            continue
        if e.get("isBlock"):
            continue
        if e["isMother"]:
            dx = cx - e["x"]
            dy = cy - e["y"]
            dist = math.hypot(dx, dy)

            move_x, move_y = 0, 0
            if dist > 1:  # рух аж до центру героя
                move_x = dx/dist * 2
                move_y = dy/dist * 2

            if not mother_collides_with_blocks(e, move_x, move_y):
                e["x"] += move_x
                e["y"] += move_y

            if e["attack_cooldown"] > 0:
                e["attack_cooldown"] -= 1
            elif dist < 200 and random.randint(0,100) < 10:
                fire_sword(e)
                e["attack_cooldown"] = 80
        else:
            if "parent" in e:
                update_child_shield(e)
                
def update_enemy_shots():
    for s in enemy_shots:
        if not s["active"]: 
            continue
        mother = s.get("parent")
        if not mother or not mother["active"]:
            s["active"] = False
            continue
        # меч замахується по герою
        s["swing_phase"] += 0.2
        swing_radius = 60
        s["x"] = mother["x"] + math.cos(s["angle"]) * swing_radius * math.sin(s["swing_phase"])
        s["y"] = mother["y"] + math.sin(s["angle"]) * swing_radius * math.sin(s["swing_phase"])
        if s["swing_phase"] > math.pi:
            s["active"] = False

def check_collisions():
    for s in shots:
        if s["active"]:
            # перевірка зі щитом
            for e in enemies:
                if e["active"] and not e["isMother"]:
                    if (s["x"] > e["x"]-e["size"] and s["x"] < e["x"]+e["size"] and
                        s["y"] > e["y"]-e["size"] and s["y"] < e["y"]+e["size"]):
                        s["active"] = False
                        e["hp"] -= 1
                        if e["hp"] <= 0: e["active"] = False
                        break
            # перевірка з матір’ю (лише якщо щит знищено)
            for e in enemies:
                if e["active"] and e["isMother"]:
                    if not any(c["active"] and not c["isMother"] and c["parent"]==e for c in enemies):
                        if (s["x"] > e["x"] and s["x"] < e["x"]+e["size"] and
                            s["y"] > e["y"] and s["y"] < e["y"]+e["size"]):
                            s["active"] = False
                            e["hp"] -= 5
                            if e["hp"] <= 0: e["active"] = False

# === PART 4: DRAWING ===
def draw_square(x, y, size, color):
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x+size, y)
    glVertex2f(x+size, y+size)
    glVertex2f(x, y+size)
    glEnd()

def draw_circle(x, y, radius, color, alpha=1.0):
    glColor4f(color[0], color[1], color[2], alpha)
    glBegin(GL_TRIANGLE_FAN)
    for i in range(24):
        angle = 2*math.pi*i/24
        glVertex2f(x+math.cos(angle)*radius, y+math.sin(angle)*radius)
    glEnd()

def draw_stars():
    for s in stars:
        if s["layer"] == 1: glColor3f(1,1,1)
        elif s["layer"] == 2: glColor3f(0.7,0.7,0.7)
        else: glColor3f(0.3,0.3,0.3)
        glBegin(GL_POINTS)
        glVertex2f(s["x"], s["y"])
        glEnd()

def draw_hero():
    cx, cy = WIDTH//2, HEIGHT//2
    draw_square(cx-hero["size"]//2, cy-hero["size"]//2, hero["size"], hero["color"])

def draw_enemies():
    for e in enemies:
        if e["active"]:
            if e["isMother"]:
                # Матір — квадрат
                draw_square(e["x"], e["y"], e["size"], (1,0,1))
            else:
                # Щит — напівпрозорий зелений круг
                draw_circle(e["x"], e["y"], e["size"], (0.3,0.8,0.3), alpha=0.6)

def draw_enemy_shots():
    for s in enemy_shots:
        if s["active"]:
            # Мечі — червоні кулі з білим контуром
            draw_circle(s["x"], s["y"], 5, (1,0,0), alpha=0.9)
            glColor3f(1,1,1)
            glBegin(GL_LINE_LOOP)
            for i in range(12):
                angle = 2*math.pi*i/12
                glVertex2f(s["x"]+math.cos(angle)*5, s["y"]+math.sin(angle)*5)
            glEnd()

def draw_shots():
    for s in shots:
        if s["active"]:
            # Постріли героя — яскраві жовті кулі
            draw_circle(s["x"], s["y"], 4, (1,1,0), alpha=1.0)
# === PART 5: HERO, INPUT, WORLD ===
def fire_shot():
    cx, cy = WIDTH//2, HEIGHT//2
    shots.append({"x": cx, "y": cy+hero["size"]//2, "active": True})

def update_shots():
    for s in shots:
        if s["active"]:
            s["y"] += 15
            if s["y"] > HEIGHT: s["active"] = False

def scroll_world(dx, dy):
    # рух світу (parallax для зірок, ворогів і снарядів)
    for s in stars:
        speed = 4 - s["layer"]
        s["x"] -= dx // speed
        s["y"] -= dy // speed
        if s["x"] < 0: s["x"] = WIDTH
        if s["x"] > WIDTH: s["x"] = 0
        if s["y"] < 0: s["y"] = HEIGHT
        if s["y"] > HEIGHT: s["y"] = 0
    for e in enemies:
        e["x"] -= dx
        e["y"] -= dy
    for s in enemy_shots:
        s["x"] -= dx
        s["y"] -= dy
    hero["world_x"] += dx
    hero["world_y"] += dy
    check_zone_transition()

def keyboard(key, x, y):
    if key == b'\x1b': sys.exit()
    elif key == b' ': fire_shot()
    keys[key] = True

def keyboard_up(key, x, y): 
    keys[key] = False

def special_keys(key, x, y): 
    keys[key] = True

def special_up(key, x, y): 
    keys[key] = False

def handle_input():
    if keys.get(GLUT_KEY_DOWN): scroll_world(0, -HERO_SPEED)
    if keys.get(GLUT_KEY_UP): scroll_world(0, HERO_SPEED)
    if keys.get(GLUT_KEY_LEFT): scroll_world(-HERO_SPEED, 0)
    if keys.get(GLUT_KEY_RIGHT): scroll_world(HERO_SPEED, 0)
    # === PART 6: DISPLAY, ZONES, INIT, MAIN ===
import random, math, sys
from OpenGL.GL import *
from OpenGL.GLUT import *

zones = {}

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    handle_input()
    update_shots()
    update_enemies()
    update_enemy_shots()
    check_collisions()
    draw_stars()
    draw_hero()
    draw_shots()
    draw_enemies()
    draw_enemy_shots()
    glutSwapBuffers()

def timer(v):
    glutPostRedisplay()
    glutTimerFunc(16, timer, 1)

# --- генерація кам’яного кокону з дверними отворами ---
# --- генерація кам’яного кокону з дверними отворами + матері біля дверей ---

def spawn_stone_cocoon(zone_x, zone_y, size=24, block_size=32):
    cx = WIDTH//2 + zone_x*WIDTH
    cy = HEIGHT//2 + zone_y*HEIGHT

    door_top    = size//2
    door_bottom = size//2
    door_left   = size//2
    door_right  = size//2

    for i in range(size):
        for j in range(size):
            if i == 0 or j == 0 or i == size-1 or j == size-1:
                if (j == size-1 and i == door_top):
                    # верхній прохід → маточна клітина над дверима
                    spawn_mother(cx + i*block_size, cy + j*block_size + block_size)
                    continue
                if (j == 0 and i == door_bottom):
                    # нижній прохід → маточна клітина під дверима
                    spawn_mother(cx + i*block_size, cy + j*block_size - block_size)
                    continue
                if (i == 0 and j == door_left):
                    # лівий прохід → маточна клітина ліворуч
                    spawn_mother(cx + i*block_size - block_size, cy + j*block_size)
                    continue
                if (i == size-1 and j == door_right):
                    # правий прохід → маточна клітина праворуч
                    spawn_mother(cx + i*block_size + block_size, cy + j*block_size)
                    continue

                # решта блоків стін
                x = cx + i*block_size
                y = cy + j*block_size
                enemies.append({
                    "x": x, "y": y,
                    "size": block_size,
                    "color": (0.5,0.5,0.5),
                    "isMother": False,
                    "isBlock": True,
                    "active": True,
                    "hp": 9999
                })
                
def generate_zone(zone_x, zone_y):
    key = (zone_x, zone_y)
    if key in zones:
        return zones[key]

    new_enemies = []
    if random.random() < 0.7:
        spawn_stone_cocoon(zone_x, zone_y)
    else:
        for i in range(random.randint(2,4)):
            side = random.choice(["left","right","top","bottom"])
            if side == "left":
                x = -random.randint(50,200)
                y = random.randint(0, HEIGHT)
            elif side == "right":
                x = WIDTH + random.randint(50,200)
                y = random.randint(0, HEIGHT)
            elif side == "top":
                x = random.randint(0, WIDTH)
                y = HEIGHT + random.randint(50,200)
            else:
                x = random.randint(0, WIDTH)
                y = -random.randint(50,200)
            spawn_mother(x, y)

    new_stars = [{"x": random.randint(0, WIDTH),
                  "y": random.randint(0, HEIGHT),
                  "layer": random.randint(1,3)}
                 for _ in range(MAX_STARS//3)]

    zones[key] = {"enemies": new_enemies, "stars": new_stars}
    stars.extend(new_stars)
    return zones[key]

def check_zone_transition():
    zone_x = hero["world_x"] // WIDTH
    zone_y = hero["world_y"] // HEIGHT
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            generate_zone(zone_x + dx, zone_y + dy)

def init_stars():
    global stars
    stars = [{"x": random.randint(0, WIDTH),
              "y": random.randint(0, HEIGHT),
              "layer": random.randint(1,3)}
             for _ in range(MAX_STARS)]
    # --- колізії героя з блоками ---
def hero_collides_with_blocks(dx, dy):
    cx, cy = WIDTH//2, HEIGHT//2

    margin = 4
    gx1 = cx - HERO_SIZE//2 + dx + margin
    gy1 = cy - HERO_SIZE//2 + dy + margin
    gx2 = cx + HERO_SIZE//2 + dx - margin
    gy2 = cy + HERO_SIZE//2 + dy - margin

    for e in enemies:
        if e.get("isBlock") and e["active"]:
            bx1 = e["x"]
            by1 = e["y"]
            bx2 = e["x"] + e["size"]
            by2 = e["y"] + e["size"]

            if not (gx2 <= bx1 or gx1 >= bx2 or gy2 <= by1 or gy1 >= by2):
                return True
    return False

# --- колізії матері з блоками ---
def mother_collides_with_blocks(e, dx, dy):
    gx1 = e["x"] + dx
    gy1 = e["y"] + dy
    gx2 = gx1 + e["size"]
    gy2 = gy1 + e["size"]

    for b in enemies:
        if b.get("isBlock") and b["active"]:
            bx1 = b["x"]
            by1 = b["y"]
            bx2 = b["x"] + b["size"]
            by2 = b["y"] + b["size"]

            if not (gx2 <= bx1 or gx1 >= bx2 or gy2 <= by1 or gy1 >= by2):
                return True
    return False

# --- оновлений handle_input ---
def handle_input():
    dx, dy = 0, 0
    if keys.get(GLUT_KEY_DOWN):  dy -= HERO_SPEED
    if keys.get(GLUT_KEY_UP):    dy += HERO_SPEED
    if keys.get(GLUT_KEY_LEFT):  dx -= HERO_SPEED
    if keys.get(GLUT_KEY_RIGHT): dx += HERO_SPEED

    if dx != 0 or dy != 0:
        if not hero_collides_with_blocks(dx, dy):
            scroll_world(dx, dy)

# --- оновлений update_enemies ---
def update_enemies():
    cx, cy = WIDTH//2, HEIGHT//2
    for e in enemies:
        if not e["active"]:
            continue
        if e.get("isBlock"):
            continue
        if e["isMother"]:
            dx = cx - e["x"]
            dy = cy - e["y"]
            dist = math.hypot(dx, dy)

            move_x, move_y = 0, 0
            if dist > 30:  # наближається
                move_x = dx/dist * 2
                move_y = dy/dist * 2
            elif dist < 30:  # відступає
                move_x = -dx/dist * 2
                move_y = -dy/dist * 2

            if not mother_collides_with_blocks(e, move_x, move_y):
                e["x"] += move_x
                e["y"] += move_y

            # решта логіки (щит, меч)
            
            if e["attack_cooldown"] > 0:
                e["attack_cooldown"] -= 1
            elif dist < 200 and random.randint(0,100) < 10:
                fire_sword(e)
                e["attack_cooldown"] = 80
        else:
            if "parent" in e:
                update_child_shield(e)

def check_collisions():
    for s in shots:
        if s["active"]:
            for e in enemies:
                if e["active"] and not e["isMother"] and not e.get("isBlock"):
                    if (s["x"] > e["x"]-e["size"] and s["x"] < e["x"]+e["size"] and
                        s["y"] > e["y"]-e["size"] and s["y"] < e["y"]+e["size"]):
                        s["active"] = False
                        e["hp"] -= 1
                        if e["hp"] <= 0: e["active"] = False
                        break
            for e in enemies:
                if e["active"] and e["isMother"]:
                    if not any(
                        c["active"] and not c["isMother"] and c.get("parent") == e
                        for c in enemies
                    ):
                        if (s["x"] > e["x"] and s["x"] < e["x"]+e["size"] and
                            s["y"] > e["y"] and s["y"] < e["y"]+e["size"]):
                            s["active"] = False
                            e["hp"] -= 5
                            if e["hp"] <= 0:
                                e["active"] = False

def draw_enemies():
    for e in enemies:
        if e["active"]:
            if e["isMother"]:
                draw_square(e["x"], e["y"], e["size"], (1,0,1))
            elif e.get("isBlock"):
                draw_square(e["x"], e["y"], e["size"], (0.5,0.5,0.5))
            else:
                draw_square(e["x"], e["y"], e["size"], (0,0,1))

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"ZoneEscape Python/OpenGL - Stone Cocoons with Doors")

    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glPointSize(2)

    init_stars()
    generate_zone(0,0)

    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_keys)
    glutSpecialUpFunc(special_up)
    glutTimerFunc(16, timer, 1)
    glutMainLoop()

if __name__ == "__main__":
    main()
