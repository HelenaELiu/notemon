import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.audio import Audio
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile
from imslib.noteseq import NoteSequencer

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window
from imslib.gfxutil import topleft_label, resize_topleft_label, AnimGroup, KFAnim, CEllipse, CLabelRect
from imslib.clock import Clock, SimpleTempoMap, AudioScheduler, tick_str, kTicksPerQuarter, quantize_tick_up
from imslib.synth import Synth
import random

from attack import Attack

class AttackDatabase(object):
    def __init__(self):
        self.metro_time = 480 * 4
        
        self.names = ["winter", "fifth symphony", "fur elise", "magic flute", "hello", "espresso", "rolling in the deep", "dynamite", "just the way you are", "uptown funk", "shape of you", 
        "the feels"]

        self.keys = {
            'winter': (60, 'minor'),
            'fifth symphony' : (60, 'minor'),
            'fur elise': (64, 'minor'),
            'magic flute': (65, 'major'),
            'hello': (65, 'minor'),
            'espresso': (60, 'major'),
            'rolling in the deep': (60, 'minor'),
            'dynamite': (64, 'major'),
            'just the way you are': (65, 'major'),
            'uptown funk': (65, 'major'),
            'shape of you': (61, 'minor'),
            'the feels': (70, 'minor'),
            }

        self.lanes = {
            'winter': (60, 62, 63, 65, 67, 69, 71, 72),
            'fifth symphony': (60, 62, 63, 65, 67, 69, 71, 72),
            'fur elise': (69, 71, 72, 74, 75, 76, 77, 79),
            'magic flute': (60, 62, 63, 65, 67, 69, 70, 72),
            'hello': (58, 60, 61, 63, 65, 66, 68, 70),
            'espresso': (55, 57, 59, 60, 62, 64, 66, 67), # TODO THESE NEED TO HAVE 8
            'rolling in the deep': (67, 69, 70, 72, 74, 75, 77, 79),
            'dynamite': (64, 66, 68, 69, 71, 73, 74, 76),
            'just the way you are': (65, 67, 69, 70, 72, 74, 76, 77),
            'uptown funk': (60, 62, 64, 65, 67, 69, 70, 72),
            'shape of you': (61, 64, 66, 68, 69, 71, 73, 76),
            'the feels': (67, 69, 71, 72, 74, 76, 78, 79),
            }

        self.notes = {
            'winter': ((240, 60), (240, 72), (240, 67), (240, 63), 
                (240, 60), (240, 72), (240, 67), (240, 63), (240, 60),),
            'fifth symphony': ((240, 67), (240, 67), (240, 67), (240 * 5, 63), 
                (240, 65), (240, 65), (240, 65), (240 * 5, 62),),
            'fur elise': ((240, 76), (240, 75), (240, 76), (240, 75), 
                (240, 76), (240, 71), (240, 74), (240, 72), (480, 69),), 
            'magic flute': ((120, 69), (120, 67), (120, 69), (120, 70), 
                (240, 72), (240, 72), (240, 72), (240, 72), 
                (240, 72), (240, 72), (240, 72), (240, 72), (240 * 4, 65),),
            'hello': ((240, 65), (240, 65), (240, 68), (240, 68), (240, 70), (240, 70), (480, 70),),
            'espresso': ((240, 55), (240, 55), (240, 59), (240, 62), (240, 60), (240, 59), (240, 57),),
            'rolling in the deep': ((240, 67), (240, 70), (240, 67), (240, 70), (240, 67), (240, 70), 
                                    (480, 72),),
            'dynamite': ((480, 73), (480, 71), (480, 69), (360, 68), (240, 66), (120, 64), (240, 64),),
            'just the way you are': ((480, 70), (480, 69), (480, 65), (480, 67), (480, 65), ),
            'uptown funk': ((360, 65), (360, 65), (240, 60), (360, 62), (360, 62), (240, 60), 
                            (360, 62), (360, 62), (240, 60), (360, 62), (360, 62),),
            'shape of you': ((240, 64), (240, 66), (480, 68), (240, 66), (240, 64), (480, 64), 
                             (480, 66), (480, 61), ),
            'the feels': ((480, 74), (480, 71), (240, 71), (120, 69), (360, 71), (480, 74),
                          (240, 71), (480, 71),),
            }

        self.damages = {
            'winter': 10,
            'fifth symphony': 40,
            'fur elise': 20,
            'magic flute': 30,
            'hello': 10,
            'espresso': 40,
            'rolling in the deep': 20,
            'dynamite': 30,
            'just the way you are': 30,
            'uptown funk': 20,
            'shape of you': 30,
            'the feels': 20
            }

    def index(self, index):
        name = self.names[index]
        return {"name": name, "lanes": self.lanes[name], "notes": self.notes[name], "damage": self.damages[name], "key": self.keys[name]}

    def get_attack(self, index, unlocked):
        return Attack(self.index(index), self.metro_time, unlocked=unlocked)
    
    def get_attack_from_name(self, name, unlocked):
        index = self.names.index(name)
        return self.get_attack(index, unlocked)

    def get_attack_roster(self, starting_index, is_op=False):
        return [self.get_attack(i+starting_index, i==0 or is_op) for i in range(4)]
