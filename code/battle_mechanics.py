#####################################################################
#
# This software is to be used for MIT's class Interactive Music Systems only.
# Since this file may contain answers to homework problems, you MAY NOT release it publicly.
#
#####################################################################

import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.audio import Audio
from imslib.synth import Synth
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile
from imslib.gfxutil import CEllipse, topleft_label, resize_topleft_label, KFAnim, CRectangle, CLabelRect
from imslib.clock import AudioScheduler, SimpleTempoMap, quantize_tick_up

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from imslib.kivyparticle import ParticleSystem

import random

class Attack:
    def __init__(self, notes):
        self.notes = notes

    def get_note(self, idx):
        return self.notes[idx]

    def last_note(self, idx):
        return idx == len(self.notes) - 1

MAJOR_KEY = [0, 2, 4, 5, 7, 9, 11, 12]
KEY_TO_IDX = { MAJOR_KEY[x] : x for x in range(len(MAJOR_KEY)) }

NUM_ATTACKS = 4
DAMAGE_MULTIPLIER = 6

PLAYER_NOTE_TIME = 1
OPP_NOTE_TIME = 8

INTERVAL = 2 # Third

attacks = [[random.choice(MAJOR_KEY) for _ in range(x + 2)] for x in range(NUM_ATTACKS)]

class Player():
    def __init__(self, attacks, sched, synth):
        self.key = 53 # F for funsies
        self.attacks = [Attack([n + self.key for n in attack]) for attack in attacks] # Shifting key of input

        self.sched = sched
        self.synth = synth

        self.next_note_cmd = None

        self.opponent = None

        self.defending = False

        self.damage = 0

    def set_opponent(self, opponent):
        self.opponent = opponent

    def note_off(self, tick, attack, note):
        self.synth.noteoff(0, self.attacks[attack].get_note(note))

    def next_note(self, tick, attack, note):
        self.synth.noteon(0, self.attacks[attack].get_note(note), 100)
        self.sched.post_at_tick(self.note_off, tick + 480*PLAYER_NOTE_TIME, [attack, note])

        if self.attacks[attack].last_note(note):
            self.next_note_cmd = None
            self.opponent.on_attack()
            return

        self.next_note_cmd = self.sched.post_at_tick(self.next_note, tick + 480*PLAYER_NOTE_TIME, [attack, note+1])
        self.opponent.on_attack()

    def launch_attack(self, attack):
        now = quantize_tick_up(self.sched.get_tick(), 480)

        self.next_note_cmd = self.sched.post_at_tick(self.next_note, now, [attack, 0])

    def on_opp_defense(self):
        print("Successful defense!")
        if self.next_note_cmd:
            self.sched.cancel(self.next_note_cmd)

    def on_defense(self, note):
        self.synth.noteon(1, note, 100)
        self.opponent.defense_note = note

        self.defending = False

    def incorrect_defense(self):
        self.defending = False
        self.take_damage()

    def take_damage(self):
        self.damage += DAMAGE_MULTIPLIER

### Defense
# Opponent sends a bunch of different attacks, but at a slower pace


class Opponent():
    def __init__(self, skill, sched, synth):
        self.key = 48 # Up the circle of 5ths

        attacks = [[0, 0, 7, 7, 9, 9, 7], [0, 2, 4, 0, 2, 4, 5, 2]]
        self.attacks = [Attack([n + self.key for n in attack]) for attack in attacks] # Shifting key of input

        self.skill = skill
        assert skill > 0 and skill < 1, "Skill must be 0 to 1 exclusive"

        self.sched = sched
        self.synth = synth

        self.attacking = False
        self.note = None

        self.damage = 0

        self.player = None

        self.defense_note = None

    def set_player(self, player):
        self.player = player

    def set_attack(self):
        self.attacking = True
        self.player.defending = True

    def player_timeout(self):
        if self.player.defending:
            self.player.take_damage()

    def unset_attack(self):
        self.attacking = False

        self.player_timeout()
        self.player.defending = False

    def note_off(self, tick, attack, note):
        if self.defense_note:
            self.synth.noteoff(1, self.defense_note)
            self.defense_note = None

        self.synth.noteoff(0, self.attacks[attack].get_note(note))
        self.player_timeout()

        if self.attacks[attack].last_note(note):
            self.unset_attack()

    def next_note(self, tick, attack, note):
        self.set_attack()

        self.note = self.attacks[attack].get_note(note)
        self.synth.noteon(0, self.note, 100)
        self.sched.post_at_tick(self.note_off, tick + 480*OPP_NOTE_TIME, [attack, note])

        if self.attacks[attack].last_note(note):
            return

        self.sched.post_at_tick(self.next_note, tick + 480*OPP_NOTE_TIME, [attack, note+1])

    def launch_attack(self):
        now = quantize_tick_up(self.sched.get_tick(), 480)

        attack = random.randrange(0, len(self.attacks)-1)

        self.sched.post_at_tick(self.next_note, now, [attack, 0])

    def on_attack(self):
        # Successful defense
        if random.random() < self.skill:
            self.player.on_opp_defense()
        else:
            self.damage += DAMAGE_MULTIPLIER


class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth()

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        self.player = Player(attacks, self.sched, self.synth)
        self.opponent = Opponent(0.3, self.sched, self.synth)

        self.player.set_opponent(self.opponent)
        self.opponent.set_player(self.player)

        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):
        # trigger attack
        attack_idx = lookup(keycode[1], '1234' , (0, 1, 2, 3))
        if attack_idx is not None:
            if attack_idx < len(self.player.attacks):
                self.player.launch_attack(attack_idx)
            else:
                print("That attack is too advanced")

        if keycode[1] == 'x':
            self.opponent.launch_attack()

        # Defense
        note = lookup(keycode[1], 'asdfjkl;' , (0, 1, 2, 3, 4, 5, 6, 7))
        if note is not None:
            if self.opponent.attacking and self.player.defending:
                # Note match!!
                if note == KEY_TO_IDX[(self.opponent.note - 48)] + INTERVAL:
                    self.player.on_defense(MAJOR_KEY[note]+48)
                else:
                    self.player.incorrect_defense()
            else:
                print("Opponent not attacking or we already tried!")

    def on_update(self):
        self.label.text = f'player damage: {self.player.damage}\n'
        self.label.text += f'opp damage: {self.opponent.damage}\n'
        self.label.text += f'defending: {self.player.defending}\n'

        self.audio.on_update()

if __name__ == "__main__":
    run(eval('MainWidget')())
