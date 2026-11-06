import pygame
import os
import random


class SoundSystem:
    def __init__(self):
        self._base    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._folder  = os.path.join(self._base, "assets", "audio", "sfx")
        self._sounds  = {}
        self._enabled = True
        self.volume   = 0.6

        # combos:a los 15 hits suena combo.wav
        self._combo_count   = 0
        self._combo_timer   = 0
        self._COMBO_WINDOW  = 180   # 3 seg para mantener el combo
        self._COMBO_TRIGGER = 10

        self._load_all()

    def _load(self, key, filename):
        path = os.path.join(self._folder, filename)
        if not os.path.isfile(path):
            return
        try:
            snd = pygame.mixer.Sound(path)
            snd.set_volume(0.7)
            self._sounds[key] = snd
            print(f"[SFX] cargado: {filename}")
        except Exception as e:
            print(f"[SFX] no pude cargar {filename}: {e}")

    def _load_all(self):
        if not os.path.isdir(self._folder):
            print(f"[SFX] no encontre la carpeta: {self._folder}")
            print(f"[SFX] assets/audio/sfx/")
            return

        # voy rotando al azar hit_1, hit_2, ...
        hit_variants = []
        for i in range(1, 6):
            for ext in (".wav", ".ogg"):
                path = os.path.join(self._folder, f"hit_{i}{ext}")
                if os.path.isfile(path):
                    try:
                        snd = pygame.mixer.Sound(path)
                        snd.set_volume(0.65)
                        hit_variants.append(snd)
                        print(f"[SFX] cargado: hit_{i}{ext}")
                    except Exception:
                        pass
        self._sounds["hit_variants"] = hit_variants

        # el resto de sonidos sueltos
        for key, fname in [
            ("hit_kill",       "hit_kill.wav"),
            ("combo",          "combo.wav"),
            ("shield_reflect", "shield_reflect.wav"),
            ("player_hurt",    "player_hurt.wav"),
            ("door_open",      "door_open.wav"),
            ("levelup",        "levelup.wav"),
            ("victoria",       "victoria.wav"),
            ("muerte",         "muerte.wav"),
        ]:
            if os.path.isfile(os.path.join(self._folder, fname)):
                self._load(key, fname)
            else:
                ogg = fname.replace(".wav", ".ogg")
                if os.path.isfile(os.path.join(self._folder, ogg)):
                    self._load(key, ogg)

    def play(self, key):
        """Suena un efecto por su clave"""
        if not self._enabled:
            return
        snd = self._sounds.get(key)
        if snd:
            snd.play()

    def play_hit(self):
        """Suena un golpe aleatorio de entre los hit_N que haya."""
        if not self._enabled:
            return
        variants = self._sounds.get("hit_variants", [])
        if variants:
            random.choice(variants).play()

    def register_hit(self, killed=False):
        """
        La llamo cada vez que una bala reflejada le pega a un enemigo.
        """
        self._combo_count += 1
        self._combo_timer  = self._COMBO_WINDOW

        self.play_hit()
        if killed:
            self.play("hit_kill")

        if self._combo_count == self._COMBO_TRIGGER:
            self.play("combo")

    def update(self):
        """si dejas de pegar mucho tiempo, se reinicia el combo."""
        if self._combo_timer > 0:
            self._combo_timer -= 1
            if self._combo_timer == 0:
                self._combo_count = 0

    @property
    def combo(self):
        return self._combo_count

    def set_volume(self, vol):
        """Volumen global de 0.0 a 1.0."""
        self.volume = max(0.0, min(1.0, vol))
        for key, snd in self._sounds.items():
            if key == "hit_variants":
                for s in snd:
                    s.set_volume(vol * 0.65)
            elif hasattr(snd, "set_volume"):
                snd.set_volume(vol)
