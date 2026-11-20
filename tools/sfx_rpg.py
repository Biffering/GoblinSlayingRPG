"""Sound effects for Six Hearths, synthesized."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import sfxlib as L
from sfxlib import (adsr, at, bp, crush, env, hp, lp, mix, noise, note, saw, sine, square, sweep, sweep_lp, t_of, tri,
                    s_coins, s_click, s_explosion, s_hit, s_enemy_die, s_super_spawn, s_super_pickup, s_tally_row, s_new_best)

SR = 44100


def blip(f, d=0.04, duty=0.25):
    return square(f, d, duty) * env(d, decay_pow=2)


def chime(notes, step=0.07, d=0.4):
    return mix(*[at(sine(note(n), d) * env(d, attack=0, decay_pow=3), i * step) for i, n in enumerate(notes)])


SFX = {
    "text": lambda: blip(900, 0.02),
    "cursor": lambda: blip(1250, 0.035),
    "confirm": lambda: mix(blip(990, 0.05), at(blip(1480, 0.07), 0.04)),
    "cancel": lambda: mix(blip(700, 0.05), at(blip(500, 0.07), 0.04)),
    "buzzer": lambda: square(140, 0.18, 0.5) * env(0.18, decay_pow=0.6) * 0.7,
    "menu_open": lambda: mix(blip(660, 0.05), at(blip(990, 0.05), 0.04), at(blip(1320, 0.08), 0.08)),
    "chest": lambda: mix(lp(noise(0.08), 1500) * env(0.08, attack=0, decay_pow=2), at(chime(["C6", "E6", "G6", "C7"], 0.06), 0.06)),
    "coins": s_coins,
    "quest": lambda: chime(["G5", "C6", "E6"], 0.09, 0.5),
    "quest_done": lambda: chime(["C6", "E6", "G6", "C7", "E7"], 0.08, 0.7),
    "recruit": lambda: chime(["D5", "F#5", "A5", "D6"], 0.1, 0.7),
    "key": lambda: mix(hp(noise(0.03), 3000) * env(0.03, attack=0), at(chime(["A6", "E7"], 0.1, 0.6), 0.03)),
    "door": lambda: lp(noise(0.25), 900) * env(0.25, attack=0.02, decay_pow=1.5),
    "portal": lambda: mix(sine(sweep(300, 1400, 0.5), 0.5) * env(0.5, attack=0.05) * 0.5,
                          bp(noise(0.5), 800, 5000) * np.sin(np.linspace(0, np.pi, int(SR * 0.5))) ** 2 * 0.4),
    "stairs": lambda: mix(*[at(lp(noise(0.05), 1200) * env(0.05, attack=0), i * 0.09) for i in range(3)]),
    "rest": lambda: chime(["C5", "E5", "G5", "B5", "D6", "G6"], 0.18, 1.2),
    "dig": lambda: mix(*[at(bp(noise(0.08), 300, 1500) * env(0.08, attack=0, decay_pow=2), i * 0.16) for i in range(3)]),
    "treasure": lambda: chime(["E6", "G6", "B6", "E7", "G7"], 0.06, 0.6),
    "summon_get": lambda: mix(s_super_spawn(), at(chime(["C5", "G5", "C6"], 0.15, 1.0), 0.1)),
    "door_open": lambda: mix(lp(noise(0.8), 500) * env(0.8, attack=0.1, decay_pow=1.2), sine(sweep(80, 50, 0.8), 0.8) * env(0.8) * 0.6),
    "encounter": lambda: mix(square(sweep(200, 1600, 0.35), 0.35, 0.5) * env(0.35, attack=0, decay_pow=0.7) * 0.4,
                             at(bp(noise(0.3), 1000, 6000) * env(0.3, attack=0, decay_pow=2) * 0.5, 0.05)),
    "atb": lambda: blip(1760, 0.03, 0.5) * 0.6,
    "defend": lambda: mix(sine(220, 0.2) * env(0.2, attack=0, decay_pow=2), at(blip(880, 0.05), 0.02)),
    "hit": s_hit,
    "weak": lambda: mix(blip(1400, 0.05, 0.5), at(blip(1870, 0.08, 0.5), 0.05)),
    "ko": lambda: mix(saw(sweep(300, 60, 0.4), 0.4) * env(0.4, decay_pow=1.4) * 0.5, lp(noise(0.2), 800) * env(0.2, attack=0) * 0.5),
    "enemy_die": s_enemy_die,
    "miss": lambda: bp(noise(0.15), 2000, 6000) * np.sin(np.linspace(0, np.pi, int(SR * 0.15))) * 0.5,
    "swing": lambda: bp(noise(0.12), 1500, 7000) * env(0.12, attack=0.02, decay_pow=1.5) * 0.7,
    "bow": lambda: mix(tri(sweep(600, 300, 0.08), 0.08) * env(0.08, attack=0), at(hp(noise(0.1), 3000) * env(0.1, attack=0) * 0.5, 0.02)),
    "enemy_attack": lambda: mix(lp(noise(0.15), 2500) * env(0.15, attack=0, decay_pow=2), sine(sweep(200, 80, 0.12), 0.12) * env(0.12) * 0.7),
    "heal": lambda: chime(["C6", "E6", "G6", "C7"], 0.05, 0.5),
    "revive": lambda: mix(chime(["G5", "D6", "G6", "B6", "D7"], 0.09, 0.9), sine(sweep(400, 1200, 0.6), 0.6) * env(0.6) * 0.2),
    "buff": lambda: mix(square(sweep(400, 1600, 0.35), 0.35, 0.25) * env(0.35) * 0.4, at(blip(1600, 0.08), 0.3)),
    "boost": lambda: mix(s_super_pickup()[: int(SR * 0.9)] * 0.7),
    "cast": lambda: mix(sine(sweep(500, 1500, 0.35), 0.35) * env(0.35, attack=0.05) * 0.4,
                        bp(noise(0.35), 2000, 8000) * env(0.35, attack=0.1) * 0.25),
    "summon": lambda: mix(s_super_pickup(), at(lp(noise(1.2), 2000) * env(1.2, attack=0.3) * 0.4, 0.3)),
    "limit": lambda: mix(square(sweep(200, 2000, 0.5), 0.5, 0.3) * env(0.5, decay_pow=0.5) * 0.4, at(s_explosion() * 0.6, 0.3)),
    "flee": lambda: mix(*[at(lp(noise(0.04), 2000) * env(0.04, attack=0), i * 0.07) for i in range(5)]),
    "dispel": lambda: mix(sine(sweep(1200, 200, 0.5), 0.5) * env(0.5) * 0.5, bp(noise(0.5), 300, 3000) * env(0.5) * 0.3),
    "stun": lambda: mix(*[at(blip(1500 + i * 300, 0.04, 0.5), i * 0.05) for i in range(4)]),
    "silence": lambda: sine(sweep(800, 100, 0.5), 0.5) * env(0.5, decay_pow=0.8) * 0.5,
    "summon_minion": lambda: mix(sine(sweep(150, 400, 0.4), 0.4) * env(0.4) * 0.5, lp(noise(0.4), 1200) * env(0.4, attack=0.1) * 0.4),
    "shift": lambda: mix(saw(sweep(200, 800, 0.4), 0.4) * env(0.4) * 0.3, saw(sweep(800, 200, 0.4), 0.4) * env(0.4) * 0.3),
    "fade": lambda: bp(noise(0.6), 200, 3000) * env(0.6, attack=0.2) * 0.4,
    "phase": lambda: mix(sine(55, 1.0) * env(1.0, attack=0.05, decay_pow=1.2), lp(noise(1.0), 400) * env(1.0, attack=0.2) * 0.5),
    "levelup": lambda: mix(*[at(square(note(n), 0.12, 0.25) * env(0.12, decay_pow=1) * 0.6, i * 0.08)
                             for i, n in enumerate(["C5", "E5", "G5", "C6", "E6", "G6", "C7"])]),
    "learn": lambda: chime(["A5", "C#6", "E6", "A6"], 0.07, 0.6),
    "equip": lambda: mix(hp(noise(0.04), 2500) * env(0.04, attack=0) * 0.6, at(blip(1100, 0.05), 0.03)),
    "save": lambda: chime(["E6", "B6", "E7"], 0.1, 0.7),
}
EL_HIT = {
    "fire": lambda: mix(s_hit(), bp(noise(0.2), 600, 4000) * env(0.2, attack=0.01) * 0.6),
    "water": lambda: mix(s_hit(), bp(noise(0.25), 400, 2500) * env(0.25, attack=0) * 0.5, sine(sweep(900, 300, 0.15), 0.15) * env(0.15) * 0.4),
    "wind": lambda: mix(s_hit(), bp(noise(0.25), 1500, 8000) * np.sin(np.linspace(0, np.pi, int(SR * 0.25))) * 0.5),
    "stone": lambda: mix(s_hit(), lp(noise(0.2), 900) * env(0.2, attack=0) * 0.8, sine(sweep(120, 60, 0.15), 0.15) * env(0.15) * 0.6),
    "spirit": lambda: mix(s_hit(), chime(["E7", "B7"], 0.03, 0.3) * 0.6),
    "void": lambda: mix(s_hit(), sine(sweep(400, 60, 0.3), 0.3) * env(0.3) * 0.6),
}
EL_SPELL = {
    "fire": lambda: mix(sweep_lp(noise(0.7), 6000, 400) * env(0.7, attack=0.05, decay_pow=1.3),
                        sine(sweep(100, 60, 0.5), 0.5) * env(0.5) * 0.6),
    "water": lambda: mix(bp(noise(0.8), 300, 3000) * np.sin(np.linspace(0, np.pi, int(SR * 0.8))) ** 1.5 * 0.8,
                         *[at(sine(sweep(1400 + i * 200, 500, 0.1), 0.1) * env(0.1) * 0.4, 0.1 + i * 0.08) for i in range(5)]),
    "wind": lambda: bp(noise(0.9), 600, 7000) * np.sin(np.linspace(0, np.pi, int(SR * 0.9))) ** 2
                    * (1 + 0.5 * np.sin(np.linspace(0, 30, int(SR * 0.9)))),
    "stone": lambda: mix(lp(noise(0.8), 600) * env(0.8, attack=0, decay_pow=1.2),
                         *[at(lp(noise(0.08), 1500) * env(0.08, attack=0) * 0.7, i * 0.11) for i in range(5)],
                         sine(sweep(80, 40, 0.6), 0.6) * env(0.6) * 0.7),
    "spirit": lambda: mix(chime(["C6", "G6", "C7", "E7", "G7", "C8"], 0.05, 0.8), hp(noise(0.8), 5000) * env(0.8, attack=0.1) * 0.25),
    "void": lambda: mix(sine(sweep(600, 40, 0.8), 0.8) * env(0.8, decay_pow=0.8) * 0.6,
                        bp(noise(0.8), 100, 1200) * env(0.8, attack=0.2) * 0.5, crush(saw(sweep(80, 30, 0.6), 0.6), 4) * env(0.6) * 0.3),
}
for el, fn in EL_HIT.items():
    SFX["hit_" + el] = fn
for el, fn in EL_SPELL.items():
    SFX["spell_" + el] = fn

if __name__ == "__main__":
    L.OUT = sys.argv[1]
    os.makedirs(L.OUT, exist_ok=True)
    for name, fn in SFX.items():
        L.save(name, fn())
    print(len(SFX), "sounds")
