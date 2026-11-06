import pygame
import random
from src.constants import *
from src.door import Door
from src.enemies import Momia, Zombi, PescadoMutante, EsqueletoRumbero, CthulhuDJ

# Medidas del cuarto
RW       = 2000   # ancho
RH       = 800    # alto
WALL_T   = 40     # grosor de las paredes exteriores
DOOR_GAP = 160    # ancho del hueco de una puerta


def outer_walls(ox, oy, w, h,
                open_left=False, open_right=False,
                open_top=False,  open_bottom=False):
    """
    Generacion de las 4 paredes exteriores del cuarto, dejando un hueco centrado
    en los lados que tienen puerta. Las esquinas siempre quedan sólidas
    """
    walls = []
    gap = DOOR_GAP
    T   = WALL_T

    # esquinas
    walls.append(pygame.Rect(ox, oy, T, T))
    walls.append(pygame.Rect(ox + w - T, oy, T, T))
    walls.append(pygame.Rect(ox, oy + h - T, T, T))
    walls.append(pygame.Rect(ox + w - T, oy + h - T, T, T))

    # pared de arriba (con o sin hueco)
    if open_top:
        cx = ox + w // 2
        if cx - gap // 2 > ox + T:
            walls.append(pygame.Rect(ox + T, oy, (cx - gap // 2) - ox - T, T))
        if cx + gap // 2 < ox + w - T:
            walls.append(pygame.Rect(cx + gap // 2, oy, (ox + w - T) - (cx + gap // 2), T))
    else:
        walls.append(pygame.Rect(ox + T, oy, w - 2 * T, T))

    # pared de abajo
    if open_bottom:
        cx = ox + w // 2
        if cx - gap // 2 > ox + T:
            walls.append(pygame.Rect(ox + T, oy + h - T, (cx - gap // 2) - ox - T, T))
        if cx + gap // 2 < ox + w - T:
            walls.append(pygame.Rect(cx + gap // 2, oy + h - T, (ox + w - T) - (cx + gap // 2), T))
    else:
        walls.append(pygame.Rect(ox + T, oy + h - T, w - 2 * T, T))

    # pared izquierda
    if open_left:
        cy = oy + h // 2
        if cy - gap // 2 > oy + T:
            walls.append(pygame.Rect(ox, oy + T, T, (cy - gap // 2) - oy - T))
        if cy + gap // 2 < oy + h - T:
            walls.append(pygame.Rect(ox, cy + gap // 2, T, (oy + h - T) - (cy + gap // 2)))
    else:
        walls.append(pygame.Rect(ox, oy + T, T, h - 2 * T))

    # pared derecha
    if open_right:
        cy = oy + h // 2
        if cy - gap // 2 > oy + T:
            walls.append(pygame.Rect(ox + w - T, oy + T, T, (cy - gap // 2) - oy - T))
        if cy + gap // 2 < oy + h - T:
            walls.append(pygame.Rect(ox + w - T, cy + gap // 2, T, (oy + h - T) - (cy + gap // 2)))
    else:
        walls.append(pygame.Rect(ox + w - T, oy + T, T, h - 2 * T))

    return walls



# PLANTILLAS DE OBSTÁCULOS

# Cada plantilla devuelve (walls, slots):
#   walls = los bloques interiores
#   slots = posiciones donde pueden aparecer enemigos
# Interior jugable: x=[40..1960]  y=[40..760]
# ──────────────────────────────────────────────────────────────────────

def template_tres_islas(ox, oy):
    """Tres islas: las de los lados cuelgan del techo, la central sube del suelo."""
    walls = [
        pygame.Rect(ox + 240,  oy + WALL_T, 320, 440),
        pygame.Rect(ox + 760,  oy + 320,    480, 440),
        pygame.Rect(ox + 1440, oy + WALL_T, 320, 440),
    ]
    slots = [
        (ox + 140, oy + 200), (ox + 140, oy + 600),
        (ox + 640, oy + 200), (ox + 640, oy + 600),
        (ox + 1000, oy + 200), (ox + 1100, oy + 200),
        (ox + 1360, oy + 200), (ox + 1360, oy + 600),
        (ox + 1860, oy + 200), (ox + 1860, oy + 600),
        (ox + 900, oy + 600), (ox + 400, oy + 680),
    ]
    return walls, slots


def template_corredor_h(ox, oy):
    """Dos bloques grandes a los lados que hacen un corredor central."""
    walls = [
        pygame.Rect(ox + WALL_T, oy + WALL_T, 320, 320),
        pygame.Rect(ox + WALL_T, oy + 440,    320, 320),
        pygame.Rect(ox + 1640,   oy + WALL_T, 320, 320),
        pygame.Rect(ox + 1640,   oy + 440,    320, 320),
        pygame.Rect(ox + 760,    oy + WALL_T, 160, 320),   # pilar que baja del techo
        pygame.Rect(ox + 1080,   oy + 440,    160, 320),   # pilar que sube del suelo
    ]
    slots = [
        (ox + 500, oy + 200), (ox + 500, oy + 600),
        (ox + 700, oy + 600), (ox + 1000, oy + 200),
        (ox + 1300, oy + 200), (ox + 1300, oy + 600),
        (ox + 600, oy + 400), (ox + 1400, oy + 400),
        (ox + 200, oy + 400), (ox + 1800, oy + 400),
    ]
    return walls, slots


def template_u_invertida(ox, oy):
    """Una U al revés: dos brazos bajan del techo y dejan un canal en medio"""
    brazo_w, brazo_h = 280, 500
    walls = [
        pygame.Rect(ox + 240,  oy + WALL_T, brazo_w, brazo_h),
        pygame.Rect(ox + 1480, oy + WALL_T, brazo_w, brazo_h),
        pygame.Rect(ox + 760,  oy + 440,    200, 320),
        pygame.Rect(ox + 1040, oy + 440,    200, 320),
    ]
    slots = [
        (ox + 140, oy + 200), (ox + 140, oy + 600),
        (ox + 580, oy + 200), (ox + 580, oy + 600),
        (ox + 1000, oy + 200),
        (ox + 1420, oy + 200), (ox + 1420, oy + 600),
        (ox + 1860, oy + 200), (ox + 1860, oy + 600),
        (ox + 600, oy + 680), (ox + 1400, oy + 680),
    ]
    return walls, slots


def template_cuatro_bloques(ox, oy):
    """Cuatro bloques en las esquinas con un pasillo en cruz en el centro."""
    walls = [
        pygame.Rect(ox + WALL_T, oy + WALL_T, 860, 260),
        pygame.Rect(ox + 1100,   oy + WALL_T, 860, 260),
        pygame.Rect(ox + WALL_T, oy + 500,    860, 260),
        pygame.Rect(ox + 1100,   oy + 500,    860, 260),
    ]
    slots = [
        (ox + 500, oy + 200), (ox + 200, oy + 160),
        (ox + 1500, oy + 200), (ox + 1800, oy + 160),
        (ox + 500, oy + 600), (ox + 200, oy + 640),
        (ox + 1500, oy + 600), (ox + 1800, oy + 640),
        (ox + 1000, oy + 200), (ox + 1000, oy + 600),
        (ox + 400, oy + 400), (ox + 1600, oy + 400),
    ]
    return walls, slots


def template_arena(ox, oy):
    """Casi todo abierto: solo unos pilares cuadrados pequeños"""
    walls = [
        pygame.Rect(ox + 300,  oy + 160, 120, 120),
        pygame.Rect(ox + 880,  oy + 160, 120, 120),
        pygame.Rect(ox + 1460, oy + 160, 120, 120),
        pygame.Rect(ox + 300,  oy + 520, 120, 120),
        pygame.Rect(ox + 880,  oy + 520, 120, 120),
        pygame.Rect(ox + 1460, oy + 520, 120, 120),
        pygame.Rect(ox + 1780, oy + 340, 120, 120),
        pygame.Rect(ox + 100,  oy + 340, 120, 120),
    ]
    slots = [
        (ox + 200, oy + 100), (ox + 600, oy + 100), (ox + 1000, oy + 100), (ox + 1400, oy + 100), (ox + 1800, oy + 100),
        (ox + 200, oy + 400), (ox + 600, oy + 400), (ox + 1000, oy + 400), (ox + 1400, oy + 400), (ox + 1800, oy + 400),
        (ox + 200, oy + 700), (ox + 600, oy + 700), (ox + 1000, oy + 700), (ox + 1400, oy + 700), (ox + 1800, oy + 700),
    ]
    return walls, slots


ROOM_TEMPLATES = [
    template_tres_islas,
    template_corredor_h,
    template_u_invertida,
    template_cuatro_bloques,
    template_arena,
]


# Tema visual del Antro
THEME_ANTRO = {"name": "El Antro", "bg": (5, 0, 20), "grid": (30, 0, 60)}
FLOOR_KEYS_ANTRO = ["floor_antro_1", "floor_antro_2", "floor_antro_3"]

ROOM_STRIDE = RW + 300   # separación entre cuartos en el mundo 


def build_room_instance(tmpl_fn, world_ox, world_oy, connections,
                        theme, depth, is_start, is_boss):
    """
    paredes, función para spawnear enemigos, definición de puertas, spawn del jugador, etc.
    tmpl_fn es None para el inicio y el jefe (esos van vacíos por dentro).
    """
    ol = connections.get('left',   False)
    or_ = connections.get('right', False)
    ot = connections.get('top',    False)
    ob = connections.get('bottom', False)

    walls = outer_walls(world_ox, world_oy, RW, RH,
                        open_left=ol, open_right=or_,
                        open_top=ot,  open_bottom=ob)

    enemy_slots = []
    boss_x = world_ox + RW // 2
    boss_y = world_oy + RH // 2

    if tmpl_fn is not None:
        interior_walls, slots = tmpl_fn(world_ox, world_oy)

        # obstáculos para no tapar la entrada con un bloque por accidente
        safe_zones = []
        margin = DOOR_GAP // 2 + 20
        if ol:
            cy = world_oy + RH // 2
            safe_zones.append(pygame.Rect(world_ox, cy - margin, 200, margin * 2))
        if or_:
            cy = world_oy + RH // 2
            safe_zones.append(pygame.Rect(world_ox + RW - 200, cy - margin, 200, margin * 2))
        if ot:
            cx = world_ox + RW // 2
            safe_zones.append(pygame.Rect(cx - margin, world_oy, margin * 2, 200))
        if ob:
            cx = world_ox + RW // 2
            safe_zones.append(pygame.Rect(cx - margin, world_oy + RH - 200, margin * 2, 200))

        walls += [w for w in interior_walls
                  if not any(w.colliderect(sz) for sz in safe_zones)]
        enemy_slots = slots

    MAX_ENEMIES = 15   # maximo de enemigos por cuarto

    # se guardan estas variables en el closure para que make_enemies las recuerde
    _slots, _depth = enemy_slots, depth
    _is_start, _is_boss = is_start, is_boss
    _bx, _by = boss_x, boss_y

    def make_enemies(room):
        # la genero como funcion para poder re-spawnear al reiniciar la sala (tecla R)
        if _is_start:
            return []
        if _is_boss:
            return [CthulhuDJ(_bx, _by)]
        # se toman unos  slots al azar y a cada uno le asigno un enemigo
        # mientras más profundo el cuarto, spawnean enemigos como esqueletos/pescados
        chosen = []
        for _ in range(MAX_ENEMIES):
            sx, sy = random.choice(_slots)          # repite slots, ya no se acaban
            sx += random.randint(-60, 60)           # los corre un poco para que no caigan encima
            sy += random.randint(-60, 60)
            chosen.append((sx, sy))

        result = []
        for ex, ey in chosen:
            if _depth <= 2:
                cls = random.choices([Momia, Zombi, PescadoMutante],
                                     weights=[5, 3, 2])[0]
            elif _depth <= 4:
                cls = random.choices([Momia, Zombi, PescadoMutante, EsqueletoRumbero],
                                     weights=[3, 3, 2, 2])[0]
            else:
                cls = random.choices([Momia, Zombi, PescadoMutante, EsqueletoRumbero],
                                     weights=[2, 2, 3, 3])[0]
            result.append(cls(ex, ey))
        return result

    # defino dónde va cada puerta según los lados conectados
    door_defs = []
    if ol:  door_defs.append(('left',   world_ox,            world_oy + RH // 2))
    if or_: door_defs.append(('right',  world_ox + RW,       world_oy + RH // 2))
    if ot:  door_defs.append(('top',    world_ox + RW // 2,  world_oy))
    if ob:  door_defs.append(('bottom', world_ox + RW // 2,  world_oy + RH))

    floor_key = FLOOR_KEYS_ANTRO[depth % len(FLOOR_KEYS_ANTRO)]

    return {
        "walls":         walls,
        "floor_key":     floor_key,
        "spawn_enemies": make_enemies,
        "door_defs":     door_defs,
        "spawn_x":       world_ox + RW // 8,   # spawneo cerca del borde izquierdo
        "spawn_y":       world_oy + RH // 2,
        "name":          theme["name"] + (" – JEFE" if is_boss else (" – Inicio" if is_start else f" – Sala {depth}")),
        "bg_color":      theme["bg"],
        "is_boss":       is_boss,
        "is_start":      is_start,
        "world_ox":      world_ox,
        "world_oy":      world_oy,
    }


# LAYOUTS DEL ANTRO
# Cada layout es una lista de nodos (grid_x, grid_y, conexiones).
# El orden = el orden en que juegas los cuartos (depth = índice).
# grid_x/y se multiplican por ROOM_STRIDE para sacar la posición en el mundo

LAYOUTS_ANTRO = [
    # pasillo recto
    [(0, 0, {'right': True}), (1, 0, {'left': True, 'right': True}),
     (2, 0, {'left': True, 'right': True}), (3, 0, {'left': True, 'right': True}),
     (4, 0, {'left': True})],
    # se va recto y luego baja
    [(0, 0, {'right': True}), (1, 0, {'left': True, 'right': True}),
     (2, 0, {'left': True, 'right': True}), (3, 0, {'left': True, 'bottom': True}),
     (3, 1, {'top': True})],
    # zigzag bajando
    [(0, 0, {'right': True}), (1, 0, {'left': True, 'bottom': True}),
     (1, 1, {'top': True, 'right': True}), (2, 1, {'left': True, 'bottom': True}),
     (2, 2, {'top': True})],
    # cruz (un cuarto extra colgando arriba)
    [(0, 1, {'right': True}), (1, 1, {'left': True, 'right': True, 'top': True}),
     (2, 1, {'left': True, 'right': True}), (3, 1, {'left': True}),
     (1, 0, {'bottom': True})],
]


def _build_rooms(layout, theme):
    """Construye la lista de cuartos a partir de un layout y conecta sus puertas."""
    rooms, pos_to_idx = [], {}

    # primero creo cada cuarto
    for depth, (gx, gy, conn) in enumerate(layout):
        ox, oy = gx * ROOM_STRIDE, gy * ROOM_STRIDE
        is_start = depth == 0
        is_boss  = depth == len(layout) - 1
        tmpl_fn  = None if (is_start or is_boss) else random.choice(ROOM_TEMPLATES)
        room = build_room_instance(tmpl_fn, ox, oy, conn, theme, depth, is_start, is_boss)
        room["grid_pos"] = (gx, gy)
        rooms.append(room)
        pos_to_idx[(gx, gy)] = depth

    # luego conecto las puertas: para cada lado abierto, busco el cuarto vecino
    for room in rooms:
        gx, gy = room["grid_pos"]
        doors = []
        for (side, wx, wy) in room["door_defs"]:
            if side == 'right':    ngx, ngy = gx + 1, gy
            elif side == 'left':   ngx, ngy = gx - 1, gy
            elif side == 'bottom': ngx, ngy = gx, gy + 1
            else:                  ngx, ngy = gx, gy - 1
            target = pos_to_idx.get((ngx, ngy))
            if target is not None:
                doors.append(Door(wx, wy, side, target))
        room["doors"] = doors

    return rooms


def generate_map():
    """El Antro, con Cthulhu DJ de jefe al final"""
    return _build_rooms(random.choice(LAYOUTS_ANTRO), THEME_ANTRO)
