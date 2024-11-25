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

from AttackDisplay import AttackDisplay
from attack import Attack

x_margin = 1/10 #distance from sides of boxes to edge of screen
y_margin = 1/20 #distance from bottom of boxes to edge of screen
box_width = 7/20 #width of boxes
box_height = 1/6 #height of boxes
radius_margin = 1/16 #radius of notemon circles

MAJOR_KEY = [0, 2, 4, 5, 7, 9, 11, 12]
MINOR_KEY = [0, 2, 3, 5, 7, 8, 10, 12]
MAJOR_KEY_TO_IDX = { MAJOR_KEY[x] : x for x in range(len(MAJOR_KEY)) }
MINOR_KEY_TO_IDX = { MINOR_KEY[x] : x for x in range(len(MINOR_KEY)) }
CHORDS = [
    [0, 2, 4, 7], 
    [0, 2, 5, 7], 
    [0, 3, 5, 7], 
    [1, 3, 5],
    [1, 4, 6],
    [1, 3, 7],
    [2, 4, 6]
]
INTERVALS = {x : [] for x in range(8)}
for c in CHORDS:
    for i in range(len(c)):
        INTERVALS[c[i]].append(set(c[0:i]+c[i+1:]))
print(INTERVALS)

NUM_ATTACKS = 4
DAMAGE_MULTIPLIER = 6

PLAYER_NOTE_TIME = 1
OPP_NOTE_TIME = 8

INTERVAL = 2 # Third

class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.display = GameDisplay()
        self.canvas.add(self.display)

        self.audio_ctrl = AudioController()
        self.player = Player(self.audio_ctrl, self.display, 58)
        self.opp = Opponent(.3, self.audio_ctrl)
        self.player.set_opponent(self.opp)
        self.opp.set_player(self.player)

        self.info = topleft_label()
        self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "up":
            self.player.on_button_up()
        elif keycode[1] == "down":
            self.player.on_button_down()
        elif keycode[1] == "left":
            self.player.on_button_left()
        elif keycode[1] == "right":
            self.player.on_button_right()
        elif keycode[1] == "enter":
            self.player.on_button_enter()

        if keycode[1] == 'x':
            self.opp.launch_attack(1)

        # Defense
        note = lookup(keycode[1], 'asdfjkl;' , (0, 1, 2, 3, 4, 5, 6, 7))
        if note is not None:
            if self.opp.attacking and self.player.defending:
                # Note match!!
                root, key_type = key['fifth_symphony']
                note_to_match = MINOR_KEY_TO_IDX[self.opp.note - root] if key_type == 'minor' else MAJOR_KEY_TO_IDX[self.opp_note - root]
                intervals = [i for i in INTERVALS[note_to_match] if note in i]

                if intervals != []:
                    note = MINOR_KEY[note] + root if key_type == 'minor' else MAJOR_KEY[note] + root
                    self.player.on_defense(note)
                else:
                    self.player.incorrect_defense()
            else:
                print("Opponent not attacking or we already tried!")

    def on_update(self):
        self.info.text = f'player damage: {self.player.damage}\n'
        self.info.text += f'opp damage: {self.opp.damage}\n'

        self.player.on_update()

        #self.info.text = 'Let\'s Battle!\n'

# Display for a single notemon sprite
class NotemonDisplay(InstructionGroup):
    def __init__(self, health, opponent):
        super(NotemonDisplay, self).__init__()

        self.health = health
        self.opponent = opponent
        self.fainted = False

        #graphics
        r = radius_margin * Window.width
        
        if opponent:
            self.color = Color(1, 0, 0)
            self.x = (1 - 2 * x_margin) * Window.width
            self.y = (1 - 3 * y_margin) * Window.height
        else:
            self.color = Color(0, 1, 0)
            self.x = 2 * x_margin * Window.width
            self.y = (1 - 6 * y_margin) * Window.height
        
        self.notemon = Line(circle = (self.x, self.y, r), width = 3)
        self.label = CLabelRect(cpos = (self.x, self.y), text = str(self.health))

        self.add(self.color)
        self.add(self.notemon)
        self.add(self.label)
    
    def take_damage(self, damage):
        if self.health - damage < 0:
            self.health = 0
            self.fainted = True
        else:
            self.health -= damage
    
    def on_update(self):
        self.remove(self.label)
        self.label = CLabelRect(cpos = (self.x, self.y), text = str(self.health))
        self.add(self.label)

key = {'fifth_symphony' : (60, 'minor')}

winter = ((240, 60), (240, 72), (240, 67), (240, 63), 
          (240, 60), (240, 72), (240, 67), (240, 63), (240, 60),)
fifth_symphony = ((240, 67), (240, 67), (240, 67), (240 * 5, 63), 
                  (240, 65), (240, 65), (240, 65), (240 * 5, 62),)
fur_elise = ((240, 76), (240, 75), (240, 76), (240, 75), 
             (240, 76), (240, 71), (240, 74), (240, 72), (240 * 2, 69),)
magic_flute = ((120, 69), (120, 67), (120, 69), (120, 70), 
               (240, 72), (240, 72), (240, 72), (240, 72), 
               (240, 72), (240, 72), (240, 72), (240, 72), (240 * 4, 65),)

# song data for winter, will eventually come from the song database
metro_time = 480 * 4
lanes = (60, 62, 63, 65, 67, 69, 71, 72) # can change; should change for every song?
fur_elise_lanes = (69, 71, 72, 74, 75, 76, 77, 79)
magic_flute_lanes = (60, 62, 63, 65, 67, 69, 70, 72)

class AudioController(object):
    def __init__(self):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
        self.synth = Synth()

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        #create song
        self.seqs = []

        self.attacks = [Attack(winter, metro_time, lanes), Attack(fifth_symphony, metro_time, lanes), Attack(fur_elise, metro_time, fur_elise_lanes), Attack(magic_flute, metro_time, magic_flute_lanes)]

        self.next_note_cmd = None
        self.defense_note = None
    
    def play(self, index):
        self.seqs[index].start()

    # needed to update audio
    def on_update(self):
        self.audio.on_update()

    # Called by opponent
    def on_opp_defense(self):
        print("Successful defense!")
        if self.next_note_cmd:
            self.sched.cancel(self.next_note_cmd)


# Displays all game elements: attack boxes, notemon sprites
class GameDisplay(InstructionGroup):
    def __init__(self):
        super(GameDisplay, self).__init__()

        #attack boxes
        self.boxes = []

        self.box0 = AttackDisplay(0, "Winter", 10, True)
        self.boxes.append(self.box0)
        self.add(self.box0)

        self.box1 = AttackDisplay(1, "5th Symphony", 40, True)
        self.boxes.append(self.box1)
        self.add(self.box1)

        self.box2 = AttackDisplay(2, "Fur Elise", 20, True)
        self.boxes.append(self.box2)
        self.add(self.box2)

        self.box3 = AttackDisplay(3, "Magic Flute", 30, True)
        self.boxes.append(self.box3)
        self.add(self.box3)

        self.current_box = 0
        self.boxes[self.current_box].select()

        #notemon sprites
        self.notemon_us = NotemonDisplay(100, False)
        self.notemon_opponent = NotemonDisplay(100, True)

        self.add(self.notemon_us)
        self.add(self.notemon_opponent)

        #battle log
        self.color = Color(1, 1, 1)
        self.add(self.color)

        self.label_x = Window.width // 2
        self.label_y = (1 - 9 * y_margin) * Window.height
        self.text = "You encountered red circle!"
        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = self.text)
        
        self.add(self.label)
    
    def on_button_up(self):
        if self.current_box == 2 or self.current_box == 3:
            self.boxes[self.current_box].unselect()
            self.current_box -= 2
            self.boxes[self.current_box].select()
    
    def on_button_down(self):
        if self.current_box == 0 or self.current_box == 1:
            self.boxes[self.current_box].unselect()
            self.current_box += 2
            self.boxes[self.current_box].select()
    
    def on_button_left(self):
        if self.current_box == 1 or self.current_box == 3:
            self.boxes[self.current_box].unselect()
            self.current_box -= 1
            self.boxes[self.current_box].select()
    
    def on_button_right(self):
        if self.current_box == 0 or self.current_box == 2:
            self.boxes[self.current_box].unselect()
            self.current_box += 1
            self.boxes[self.current_box].select()
    
    def attack_opponent(self, index):
        damage = self.boxes[index].damage
        self.notemon_opponent.take_damage(damage)

        self.remove(self.label)
        self.text = "You used " + self.boxes[index].name + "!\n"
        self.text += "It dealt " + str(damage) + " damage!\n"

        if self.notemon_opponent.fainted:
            self.text += "Opponent notemon fainted! You win :)"

        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = self.text)
        self.add(self.label)
    
    def lose_health(self, index):
        damage = self.boxes[index].damage
        self.notemon_us.take_damage(damage)

        self.remove(self.label)
        self.text = "The opponent used " + self.boxes[index].name + "!\n"
        self.text += "It dealt " + str(damage) + " damage!\n"

        if self.notemon_us.fainted:
            self.text += "Your notemon fainted! You lose :("

        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = self.text)
        self.add(self.label)
    
    def check_complete(self):
        return (self.notemon_opponent.fainted or self.notemon_us.fainted)
    
    def on_update(self):
        self.notemon_opponent.on_update()
        self.notemon_us.on_update()

# Handles game logic.
# Controls the GameDisplay and AudioCtrl based on what happens
class Player(object):
    def __init__(self, audio_ctrl, display, key):
        super(Player, self).__init__()

        self.key = key

        self.audio_ctrl = audio_ctrl
        self.display = display

        self.our_turn = True
        self.complete = False

        self.defending = False
        self.opponent = None
        self.damage = 0

    def set_opponent(self, opponent):
        self.opponent = opponent

    # called by MainWidget
    def on_button_down(self):
        self.display.on_button_down()
        
    # called by MainWidget
    def on_button_up(self):
        self.display.on_button_up()
    
    # called by MainWidget
    def on_button_left(self):
        self.display.on_button_left()
    
    # called by MainWidget
    def on_button_right(self):
        self.display.on_button_right()

    # called by MainWidget
    def on_button_enter(self):
        if not self.complete: 
            #make sure battle is not over
            if self.our_turn:
                current_box = self.display.current_box
                self.launch_attack(current_box)
                self.display.attack_opponent(current_box)
                self.our_turn = False
            else:
                opponent_box = random.randint(0, 3)
                self.opponent.launch_attack(opponent_box)
                self.display.lose_health(opponent_box)
                self.our_turn = True
            
            self.complete = self.display.check_complete()

    # Scheduled during attack
    def note_off(self, tick, attack, note):
        _, pitch = self.audio_ctrl.attacks[attack].get_note(note)
        self.audio_ctrl.synth.noteoff(0, pitch)

    # Scheduled during attack
    def next_note(self, tick, attack, note):
        length, pitch = self.audio_ctrl.attacks[attack].get_note(note)
        self.audio_ctrl.synth.noteon(0, pitch, 100)
        self.audio_ctrl.sched.post_at_tick(self.note_off, tick + length*.95, [attack, note])

        if self.audio_ctrl.attacks[attack].last_note(note):
            self.audio_ctrl.next_note_cmd = None
            self.opponent.on_attack()
            return

        self.audio_ctrl.next_note_cmd = self.audio_ctrl.sched.post_at_tick(self.next_note, tick + length, [attack, note+1])
        self.opponent.on_attack()

    # Called by MainWidget
    def launch_attack(self, attack):
        now = quantize_tick_up(self.audio_ctrl.sched.get_tick(), 480)

        self.audio_ctrl.next_note_cmd = self.audio_ctrl.sched.post_at_tick(self.next_note, now, [attack, 0])

    # REACTIONS TO GAME EVENTS

    # called by MainWidget
    def on_defense(self, note):
        self.audio_ctrl.synth.noteon(1, note, 100)
        self.audio_ctrl.defense_note = note

        self.defending = False

    # called by MainWidget
    def incorrect_defense(self):
        self.defending = False
        self.take_damage()

    # called by MainWidget
    def take_damage(self):
        self.damage += DAMAGE_MULTIPLIER

    def on_update(self):
        self.audio_ctrl.on_update()
        self.display.on_update()

class Opponent():
    def __init__(self, skill, audio_ctrl):
        self.skill = skill
        assert skill > 0 and skill < 1, "Skill must be 0 to 1 exclusive"

        self.audio_ctrl = audio_ctrl

        self.attacking = False

        self.damage = 0

        self.player = None

        self.note = None

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

    # Scheduled during attack
    def note_off(self, tick, attack, note):
        if self.audio_ctrl.defense_note:
            self.audio_ctrl.synth.noteoff(1, self.audio_ctrl.defense_note)
            self.audio_ctrl.defense_note = None

        length, pitch = self.audio_ctrl.attacks[attack].get_note(note)
        self.audio_ctrl.synth.noteoff(0, pitch)
        self.note = None
        self.player_timeout()

        if self.audio_ctrl.attacks[attack].last_note(note):
            self.unset_attack()

    # Scheduled during attack
    def next_note(self, tick, attack, note):
        self.set_attack()

        length, pitch = self.audio_ctrl.attacks[attack].get_note(note)
        self.audio_ctrl.synth.noteon(0, pitch, 100)
        self.note = pitch
        self.audio_ctrl.sched.post_at_tick(self.note_off, tick + 4*length*.95, [attack, note])

        if self.audio_ctrl.attacks[attack].last_note(note):
            return

        self.audio_ctrl.sched.post_at_tick(self.next_note, tick + 4*length, [attack, note+1])

    # Called by MainWidget
    def launch_attack(self, attack):
        now = quantize_tick_up(self.audio_ctrl.sched.get_tick(), 480)

        self.audio_ctrl.sched.post_at_tick(self.next_note, now, [attack, 0])

    def on_attack(self):
        # Successful defense
        if random.random() < self.skill:
            self.audio_ctrl.on_opp_defense()
        else:
            self.damage += DAMAGE_MULTIPLIER


if __name__ == "__main__":
    run(MainWidget())
