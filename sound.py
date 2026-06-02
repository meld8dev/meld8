import array
import math
import pygame

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.muted = False

    def generate_sequence(self, notes):
        sample_rate = 22050
        buf = array.array('h')
        for freq, duration_ms, volume in notes:
            num_samples = int(sample_rate * (duration_ms / 1000.0))
            for i in range(num_samples):
                if freq == 0:
                    buf.append(0)
                else:
                    t = float(i) / sample_rate
                    fade_in = 1.0 if i > 400 else i / 400.0
                    fade_out = 1.0 if (num_samples - i) > 400 else (num_samples - i) / 400.0
                    envelope = min(fade_in, fade_out)
                    sample = int(volume * 32767 * math.sin(2.0 * math.pi * freq * t) * envelope)
                    buf.append(sample)
        return pygame.mixer.Sound(buf)

    def init_sounds(self):
        seq_chi = [(659, 100, 0.3), (0, 100, 0), (784, 150, 0.3)]
        seq_pong = [(523, 100, 0.3), (0, 120, 0), (523, 100, 0.3), (0, 120, 0), (523, 100, 0.3)]
        seq_tsumo = [(784, 100, 0.3), (0, 100, 0), (1046, 200, 0.3)]
        seq_ron = [(1046, 100, 0.4), (0, 100, 0), (987, 100, 0.4), (0, 100, 0), (1046, 200, 0.4)]
        seq_fanfare = [(523, 100, 0.3), (0, 100, 0), (659, 100, 0.3), (0, 100, 0), (784, 100, 0.3), (0, 100, 0), (1046, 300, 0.3)]
        
        seq_tsumo_win = seq_tsumo + [(0, 150, 0)] + seq_fanfare
        seq_ron_win = seq_ron + [(0, 150, 0)] + seq_fanfare

        self.sounds['chi'] = self.generate_sequence(seq_chi)
        self.sounds['pong'] = self.generate_sequence(seq_pong)
        self.sounds['tsumo'] = self.generate_sequence(seq_tsumo)
        self.sounds['ron'] = self.generate_sequence(seq_ron)
        self.sounds['win_fanfare'] = self.generate_sequence(seq_fanfare)
        self.sounds['tsumo_win_fanfare'] = self.generate_sequence(seq_tsumo_win)
        self.sounds['ron_win_fanfare'] = self.generate_sequence(seq_ron_win)
        self.sounds['my_turn'] = self.generate_sequence([(440, 150, 0.2)])
        self.sounds['com_win'] = self.generate_sequence([(330, 400, 0.3)])
        self.sounds['draw'] = self.generate_sequence([(440, 300, 0.2)])
        self.sounds['action'] = self.generate_sequence([(660, 150, 0.2)])
        self.sounds['deal'] = self.generate_sequence([(1500, 20, 0.05)])

    def play(self, name):
        if not self.muted and name in self.sounds:
            self.sounds[name].play()

    def toggle_mute(self):
        self.muted = not self.muted

sm = SoundManager()

def play_chi_sound(): sm.play('chi')
def play_pong_sound(): sm.play('pong')
def play_tsumo_sound(): sm.play('tsumo')
def play_ron_sound(): sm.play('ron')