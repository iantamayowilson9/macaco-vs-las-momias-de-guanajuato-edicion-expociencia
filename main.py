import pygame
import sys
import os
import math
import random
from src.game import Game
from src.font import get_font

# Rutas base del proyecto
BASE = os.path.dirname(os.path.abspath(__file__))
ANCHO, ALTO = 1280, 720


#  AUDIO

def cambiar_musica(ruta, loops=-1):
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(ruta)
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(loops)
    except pygame.error as e:
        print(f"No se pudo reproducir {os.path.basename(ruta)}: {e}")

MUSICAS_MENU = [
    "menu_music.mp3",
    "menu_music2.mp3",
    "menu_music3.mp3",
    "menu_music4.mp3",
    "menu_music5.mp3",
    "menu_music6.mp3",
    "menu_music7.mp3",
    "menu_music8.mp3",
    "menu_music9.mp3",
    "menu_music10.mp3",
    "menu_music11.mp3",
    "menu_music12.mp3",
    "menu_music13.mp3",
    "menu_music14.mp3",
    "menu_music15.mp3",
    "menu_music16.mp3",
    "menu_music17.mp3",
    "menu_music18.mp3",
    "menu_music19.mp3",
    "menu_music20.mp3",
    "menu_music21.mp3"
]
_ultima_musica_menu = None


def musica_menu_aleatoria():
    """Pone una canción de menú al azar (sin repetir la anterior)."""
    global _ultima_musica_menu
    rutas = [os.path.join(BASE, "assets", n) for n in MUSICAS_MENU
             if os.path.isfile(os.path.join(BASE, "assets", n))]
    if not rutas:
        print("[Música] No hay canciones de menú en assets/")
        return
    opciones = [r for r in rutas if r != _ultima_musica_menu] or rutas
    elegida = random.choice(opciones)
    _ultima_musica_menu = elegida
    cambiar_musica(elegida, 0)

def musica_menu_cambiar(paso):
    """Cambia a otra canción al azar."""
    musica_menu_aleatoria()

def nombre_musica_menu():
    if not _ultima_musica_menu:
        return ""
    return os.path.splitext(os.path.basename(_ultima_musica_menu))[0]


#  CARGA DE ASSETS DEL MENU

def cargar_assets_menu():
    ruta_menu = os.path.join(BASE, "assets", "menu")   # <-- esta falta
    assets = {}

    def img(nombre):
        """Carga una imagen del menú"""
        ruta = os.path.join(ruta_menu, nombre)
        try:
            return pygame.image.load(ruta).convert_alpha()
        except Exception:
            print(f"[Assets] No encontrado: {nombre}")
            return None

    # Imagenes del menú
    assets["frame"]      = img("menu_frame.png")
    assets["bg_earth"]   = img("menu_bg_earth.png")

    raw_logo = img("menu_logo.png")
    if raw_logo:
        w = 560
        h = int(w * raw_logo.get_height() / raw_logo.get_width())
        assets["logo"] = pygame.transform.smoothscale(raw_logo, (w, h))
    else:
        assets["logo"] = None

    for key, fname in [("btn", "menu_button_texture.png"),
                       ("btn_hover", "menu_button_hover.png")]:
        raw = img(fname)
        assets[key] = pygame.transform.smoothscale(raw, (460, 48)) if raw else None

    # Fuente
    ruta_fuente = os.path.join(ruta_menu, "Earthbound.otf")
    try:
        assets["font_btn"]    = pygame.font.Font(ruta_fuente, 20)
        assets["font_splash"] = pygame.font.Font(ruta_fuente, 24)
        assets["font_hud"]    = pygame.font.Font(ruta_fuente, 28)
        print("[Fuente] Earthbound.otf cargada")
    except Exception:
        assets["font_btn"]    = pygame.font.SysFont("Arial", 22, bold=True)
        assets["font_splash"] = pygame.font.SysFont("Arial", 26, bold=True)
        assets["font_hud"]    = pygame.font.SysFont("Arial", 28, bold=True)

    return assets


#  CARGA DE FRAMES DE INTRO

def cargar_intro():
    ruta = os.path.join(BASE, "assets", "intro")
    frames = []
    if not os.path.exists(ruta):
        return frames
    archivos = sorted(f for f in os.listdir(ruta)
                      if f.lower().endswith(".png") and f.startswith("frame_"))
    for nombre in archivos:
        try:
            img = pygame.image.load(os.path.join(ruta, nombre)).convert_alpha()
            frames.append(pygame.transform.scale(img, (ANCHO, ALTO)))
        except Exception as e:
            print(f"[Intro] Error al cargar {nombre}: {e}")
    print(f"[Intro] {len(frames)} frames cargados")
    return frames


#  HELPERS DE DIBUJO DEL MENÚ

def draw_tiled_bg(surface, tile):
    """Fondo de mosaico"""
    if not tile:
        surface.fill((20, 10, 30))
        return
    tw, th = tile.get_size()
    offset = (pygame.time.get_ticks() // 40) % tw
    for y in range(0, ALTO, th):
        for x in range(-tw, ANCHO + tw, tw):
            surface.blit(tile, (x - offset, y))


def draw_splash(surface, text, font, logo_x, logo_y, logo_w, logo_h):
    """Texto minecraft en la esquina del logo."""
    scale = 1.3 + 0.08 * math.sin(pygame.time.get_ticks() * 0.006)
    base   = font.render(text, True, (255, 255, 0))
    shadow = font.render(text, True, (0, 0, 0))
    w, h   = base.get_size()
    nw, nh = int(w * scale), int(h * scale)
    base   = pygame.transform.rotate(pygame.transform.scale(base,   (nw, nh)), 15)
    shadow = pygame.transform.rotate(pygame.transform.scale(shadow, (nw, nh)), 15)
    px = logo_x + logo_w - 180
    py = logo_y + logo_h - 70
    surface.blit(shadow, (px + 3, py + 3))
    surface.blit(base,   (px, py))


def draw_outlined(surface, text, font, pos, color, border=(0,0,0), thickness=2):
    """Texto con borde negro"""
    x, y = pos
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx or dy:
                surface.blit(font.render(text, True, border), (x+dx, y+dy))
    surface.blit(font.render(text, True, color), (x, y))


#  PANTALLA DE CONTROLES

def draw_controles(surface, font, font_title):
    """Pantalla de controles, vuelve con ESC o ENTER."""
    surface.fill((10, 0, 20))
    titulo = font_title.render("CONTROLES", True, (255, 200, 0))
    surface.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 80))

    lineas = [
        ("MOUSE",  "Mover a Macaco + apuntar el Escudo"),
        ("ESCUDO", "Refleja las balas enemigas de vuelta"),
        ("PUERTA", "Cruza la puerta para avanzar al siguiente cuarto"),
        ("ESC",    "Pausa el juego"),
        ("R",      "Reiniciar sala actual"),
    ]
    y = 200
    for key, desc in lineas:
        k = font.render(f"[ {key} ]", True, (0, 230, 255))
        d = font.render(desc,         True, (200, 200, 200))
        surface.blit(k, (200, y))
        surface.blit(d, (420, y))
        y += 44

    volver = font.render("Presiona ESC o ENTER para volver", True, (120, 120, 160))
    surface.blit(volver, (ANCHO//2 - volver.get_width()//2, ALTO - 60))


#  BUCLE PRINCIPAL

def main():
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()

        # Sonido del botón Jugar
    sfx_start = None
    ruta_start = os.path.join(BASE, "assets", "audio", "sfx", "start.mp3")
    try:
        sfx_start = pygame.mixer.Sound(ruta_start)
        sfx_start.set_volume(0.7)
    except Exception as e:
        print(f"[SFX] no pude cargar start.mp3: {e}")

    screen = pygame.display.set_mode((ANCHO, ALTO), pygame.SCALED | pygame.FULLSCREEN)
    pygame.display.set_caption("Macaco vs. Las Momias de Guanajuato")
    clock  = pygame.time.Clock()

    # Cargar assets
    assets        = cargar_assets_menu()
    intro_frames  = cargar_intro()
    splash_text   = random.choice([
        "¡Mi papá es fox!",
        "¡SIXSEVENSIXSEVEN!",
        "¡UN SALUDO PARA EL BETO!",
        "PATROCINADO POR LITTLE CAESARS"
    ])
    opciones      = ["Jugar", "Controles", "Salir"]
    seleccion     = 0
    rects_botones = []
    radio_espera  = 0
    rect_prev = pygame.Rect(0, 0, 0, 0)
    rect_next = pygame.Rect(0, 0, 0, 0)  

    # Scanlines
    scanlines = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for y in range(0, ALTO, 4):
        pygame.draw.line(scanlines, (0, 0, 0, 40), (0, y), (ANCHO, y))

    estado         = "INTRO" if intro_frames else "MENU"
    frame_idx      = 0
    frame_timer    = 0
    FPS_INTRO      = 4
    TOTAL_FRAMES   = len(intro_frames) if intro_frames else 215

    # Música de intro
    ruta_intro_music = os.path.join(BASE, "assets", "intro_music.mp3")
    cambiar_musica(ruta_intro_music)

    # Referencia al objeto Game
    game = None

    corriendo = True
    while corriendo:
        clock.tick(60)

                # Radio del menú: al terminar una canción, pone otra al azar
        if estado in ("MENU", "CONTROLES") and not pygame.mixer.music.get_busy():
            radio_espera = locals().get("radio_espera", 0) + 1
            if radio_espera >= 30:           # revisa cada medio segundo
                radio_espera = 0
                musica_menu_aleatoria()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                corriendo = False

                    # ── Mouse ──
            if estado == "INTRO" and event.type == pygame.MOUSEBUTTONDOWN:
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

            elif estado == "MENU":
                if event.type == pygame.MOUSEMOTION:
                    for i, r in enumerate(rects_botones):
                        if r.collidepoint(event.pos):
                            seleccion = i            # hover = seleccionar
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, r in enumerate(rects_botones):
                        if r.collidepoint(event.pos):
                            seleccion = i
                            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

            elif estado == "CONTROLES" and event.type == pygame.MOUSEBUTTONDOWN:
                estado = "MENU"

            if event.type == pygame.KEYDOWN:

                if estado == "INTRO":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        musica_menu_aleatoria()
                        estado = "MENU"

                elif estado == "MENU":
                    if event.key == pygame.K_DOWN:
                        seleccion = (seleccion + 1) % len(opciones)
                    elif event.key == pygame.K_UP:
                        seleccion = (seleccion - 1) % len(opciones)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if seleccion == 0:
                            if sfx_start:
                                sfx_start.play()           # Jugar
                            pygame.mixer.music.stop()
                            pygame.time.delay(100)
                            game = Game()
                            game.start_game()
                            estado = "GAMEPLAY"
                        elif seleccion == 1:        # Controles
                            estado = "CONTROLES"
                        elif seleccion == 2:        # Salir
                            corriendo = False
                        elif event.key == pygame.K_RIGHT:
                            musica_menu_cambiar(+1)
                    elif event.key == pygame.K_LEFT:
                        musica_menu_cambiar(-1)
                    elif event.key == pygame.K_ESCAPE:
                        corriendo = False

                elif estado == "CONTROLES":
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        estado = "MENU"

                elif estado == "GAMEPLAY":
                    game._handle_event(event)


        if estado == "INTRO":
            screen.fill((0, 0, 0))
            if intro_frames:
                screen.blit(intro_frames[frame_idx], (0, 0))
                frame_timer += 1
                if frame_timer >= FPS_INTRO:
                    frame_timer = 0
                    frame_idx  += 1
                    if frame_idx >= TOTAL_FRAMES:
                        musica_menu_aleatoria()
                        estado = "MENU"
            else:
                txt = assets["font_hud"].render("Presiona ENTER para continuar", True, (255,255,255))
                screen.blit(txt, (ANCHO//2 - txt.get_width()//2, ALTO//2))
                frame_idx += 1
                if frame_idx >= TOTAL_FRAMES:
                    musica_menu_aleatoria()
                    estado = "MENU"

        elif estado == "MENU":
            draw_tiled_bg(screen, assets["bg_earth"])

            logo = assets["logo"]
            if logo:
                lx = ANCHO//2 - logo.get_width()//2
                ly = 50
                screen.blit(logo, (lx, ly))
                draw_splash(screen, splash_text, assets["font_splash"],
                            lx, ly, logo.get_width(), logo.get_height())

            # Botones
            by = 420
            gap = 8
            rects_botones = []
            for i, opcion in enumerate(opciones):
                tex = assets["btn_hover"] if i == seleccion else assets["btn"]
                col = (255, 255, 0) if i == seleccion else (255, 255, 255)
                if tex:
                    bw, bh = tex.get_size()
                    bx = ANCHO//2 - bw//2
                    rects_botones.append(pygame.Rect(bx, by, bw, bh)) # <-- 2) dentro del for
                    screen.blit(tex, (bx, by))
                    tx = bx + bw//2 - assets["font_btn"].size(opcion)[0]//2
                    ty = by + bh//2 - assets["font_btn"].get_height()//2 - 3
                    draw_outlined(screen, opcion, assets["font_btn"], (tx, ty), col)
                else:
                    rects_botones.append(pygame.Rect(ANCHO//2 - 150, by, 300, 48))
                by += (tex.get_height() if tex else 48) + gap

            copy = assets["font_btn"].render("© 2026 Macaco Games", True, (140, 140, 140))
            screen.blit(copy, (ANCHO//2 - copy.get_width()//2, ALTO - 45))
            screen.blit(scanlines, (0, 0))
            if assets["frame"]:
                screen.blit(assets["frame"], (0, 0))

        elif estado == "CONTROLES":
            draw_controles(screen, assets["font_btn"], assets["font_hud"])
            screen.blit(scanlines, (0, 0))

        elif estado == "GAMEPLAY":
            result = game._tick_external(screen)
            # Si el juego termina (GAMEOVER / VICTORY / vuelve al menú)
            if result in ("MENU", "QUIT"):
                if result == "QUIT":
                    corriendo = False
                else:
                    musica_menu_aleatoria()
                    game  = None
                    estado = "MENU"

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
