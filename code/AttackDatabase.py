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


class AttackDatabase(object):
    def __init__(self):
        self.metro_time = 480 * 4
        
        self.names = ["winter", "fifth symphony", "fur elise", "magic flute", "hello", "espresso", "rolling in the deep", "dynamite"]

        self.keys = {
            'winter': (60, 'minor'),
            'fifth symphony' : (60, 'minor'),
            'fur elise': (64, 'minor'),
            'magic flute': (65, 'major'),
            'hello': (65, 'minor'),
            'espresso': (60, 'major'),
            'rolling in the deep': (60, 'minor'),
            'dynamite': (64, 'major'),
            }

        self.lanes = {
            'winter': (60, 62, 63, 65, 67, 69, 71, 72),
            'fifth symphony': (62, 63, 65, 67),
            'fur elise': (69, 71, 72, 74, 75, 76, 77, 79),
            'magic flute': (60, 62, 63, 65, 67, 69, 70, 72),
            'hello': (65, 68, 70),
            'espresso': (55, 57, 59, 60, 62),
            'rolling in the deep': (67, 70, 72),
            'dynamite': (64, 66, 68, 69, 71, 73),
            }

        self.notes = {
            'winter': ((240, 60), (240, 72), (240, 67), (240, 63), 
                (240, 60), (240, 72), (240, 67), (240, 63), (240, 60),),
            'fifth symphony': ((240, 67), (240, 67), (240, 67), (240 * 5, 63), 
                (240, 65), (240, 65), (240, 65), (240 * 5, 62),),
            'fur elise': ((240, 76), (240, 75), (240, 76), (240, 75), 
                (240, 76), (240, 71), (240, 74), (240, 72), (240 * 2, 69),), 
            'magic flute': ((120, 69), (120, 67), (120, 69), (120, 70), 
                (240, 72), (240, 72), (240, 72), (240, 72), 
                (240, 72), (240, 72), (240, 72), (240, 72), (240 * 4, 65),),
            'hello': ((240, 65), (240, 65), (240, 68), (240, 68), (240, 70), (240, 70), (240 * 2, 70),),
            'espresso': ((240, 55), (240, 55), (240, 59), (240, 62), (240, 60), (240, 59), (240, 57),),
            'rolling in the deep': ((240, 67), (240, 70), (240, 67), (240, 70), (240, 67), (240, 70), 
                                    (240 * 2, 72),),
            'dynamite': ((480, 73), (480, 71), (480, 69), (360, 68), (240, 66), (120, 64), (240, 64),),
            }