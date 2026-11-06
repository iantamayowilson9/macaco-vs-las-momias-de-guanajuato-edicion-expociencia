import pygame
import os
import random

class MusicPlayer:

    # Nombres base: acepta .ogg o .mp3 automáticamente
    TRACK_BASES = [
        "01_antro", "02_antro", "03_antro",
        "04_antro", "05_antro", "06_antro",
        "07_antro", "08_antro", "09_antro", "10_antro"
    ]

    def __init__(self):
        self._base   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._folder = os.path.join(self._base, "assets", "audio")
        self.volume  = 0.7   # volumen del juego (0.0 a 1.0)
        self._warmup = 0
        self._active = False
        self.index   = 0
        self.tracks  = []
        self._order  = []    # orden aleatorio actual (índices de self.tracks)
        self._pos    = 0
        self._scan()

    def _scan(self):
        self.tracks = []
        for base in self.TRACK_BASES:
            for ext in (".ogg", ".mp3"):
                path = os.path.join(self._folder, base + ext)
                if os.path.isfile(path):
                    self.tracks.append(path)
                    print(f"[Música] OK → {base}{ext}")
                    break
            else:
                print(f"[Música] ✗  → {base} (no encontrado)")
        if not self.tracks:
            for f in sorted(os.listdir(self._folder)) if os.path.isdir(self._folder) else []:
                if f.lower().endswith((".ogg", ".mp3")):
                    self.tracks.append(os.path.join(self._folder, f))
                    print(f"[Música] Fallback → {f}")

    def _barajar(self, evitar=None):
        """Crea un nuevo orden aleatorio; evita que arranque con la canción 'evitar'."""
        self._order = list(range(len(self.tracks)))
        random.shuffle(self._order)
        if evitar is not None and len(self._order) > 1 and self._order[0] == evitar:
            self._order[0], self._order[1] = self._order[1], self._order[0]
        self._pos = 0

    def play(self, index=0):
        if not self.tracks:
            print("[Música] Sin canciones en assets/audio/")
            return
        self._barajar()
        self.index   = self._order[0]
        self._active = True
        self._play_current()

    def _play_current(self):
        path = self.tracks[self.index]
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(0)   # sin loop: update() avanza a la siguiente
            self._warmup = 90
            print(f"[Musica] ▶ {os.path.basename(path)}")
        except Exception as e:
            print(f"[Musica] ERROR: {e}")
            self._active = False

    def update(self):
        if not self._active or not self.tracks:
            return
        if self._warmup > 0:
            self._warmup -= 1
            return
        if not pygame.mixer.music.get_busy():
            self._pos += 1
            if self._pos >= len(self._order):
                self._barajar(evitar=self.index)   # ya sonaron todas: re-barajar
            self.index = self._order[self._pos]
            self._play_current()

    def siguiente(self):
        if not self.tracks:
            return
        if not self._order:
            self._barajar()
        self._pos += 1
        if self._pos >= len(self._order):
            self._barajar(evitar=self.index)
        self.index   = self._order[self._pos]
        self._active = True
        self._play_current()

    def anterior(self):
        if not self.tracks:
            return
        if not self._order:
            self._barajar()
        self._pos    = (self._pos - 1) % len(self._order)
        self.index   = self._order[self._pos]
        self._active = True
        self._play_current()

    def pause(self):
        if self._active:
            pygame.mixer.music.pause()

    def unpause(self):
        if self._active:
            pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()
        self._active = False

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        pygame.mixer.music.set_volume(self.volume)

    @property
    def current_name(self):
        if not self.tracks:
            return "Sin música"
        return os.path.basename(self.tracks[self.index])