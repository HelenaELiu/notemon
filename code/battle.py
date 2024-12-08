import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import Widget, run, lookup
from imslib.screen import Screen
# from imslib.audio import Audio
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
from kivy.uix.image import Image

from battle_aud_ctrl import PlayerAudioController, OppAudioController
from AttackDisplay import AttackDisplay, AttackBox
from NotemonDisplay import NotemonDisplay
from AttackDatabase import AttackDatabase
from NotemonDatabase import NotemonDatabase
from attack import Attack
from rhythm_display import RhythmDisplay
from training_display_components import accuracy_window

attack_database = AttackDatabase()

x_margin = 1/10 #distance from sides of boxes to edge of screen
y_margin = 1/20 #distance from bottom of boxes to edge of screen
box_width = 7/20 #width of boxes
box_height = 1/6 #height of boxes
radius_margin = 1/16 #radius of notemon circles
defense_threshold = .9

TIME_BETWEEN_ATTACKS = 960

class MainWidget(Screen):
    def __init__(self, name, audio, synth, sched):
        super(MainWidget, self).__init__(name)

        # Add the background image
        self.background = Image(
            source='battle.jpg',  # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch to fill the screen
            keep_ratio=False          # Fill the entire screen without maintaining aspect ratio
        )
        self.background.size = Window.size
        self.background.size_hint = (None, None)  # Disable size hinting
        self.background.pos = (0, 0)  # Position the image at the bottom-left corner

        self.add_widget(self.background)

        # audio
        self.audio = audio
        self.synth = synth
        # self.tempo_map  = SimpleTempoMap(120)
        self.sched = sched

        # # connect scheduler into audio system
        # self.audio.set_generator(self.sched)
        # self.sched.set_generator(self.synth)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.opp_box_played = None
        # self.player_defending = False
        self.gem_idx = 0
        self.tick = None

        self.rhythm_display = None
        self.display = None

    def on_enter(self):
        self.active_notemon = self.globals.database[self.globals.pokemon_index]
        self.player_attacks = self.globals.database[self.globals.pokemon_index].attacks

        self.opp_index = random.randrange(6)
        self.opp = self.globals.database[self.opp_index]

        self.direction_enable = self.opp.direction_enable
        self.defendable_keys = set(['spacebar']) if not self.direction_enable else set(['up', 'down', 'spacebar'])

        self.op_attacks = self.globals.database[self.opp_index].attacks
        self.op_audio_ctrl = [OppAudioController(self.synth, self.sched, attack, index, self.player_defense_screen) for (index, attack) in enumerate(self.op_attacks)]
        self.rhythm_display = [RhythmDisplay(attack) for attack in self.op_attacks]


        self.display = GameDisplay(self.player_attacks, self.active_notemon, self.opp)
        self.canvas.add(self.display)

        self.player_audio_ctrl = [PlayerAudioController(self.synth, self.sched, attack, index, self.display.opponent_defense) for (index, attack) in enumerate(self.player_attacks)]
        self.player = Player(self.player_audio_ctrl, self.display, self.rhythm_display)

        self.on_resize((Window.width, Window.height))

    def on_exit(self):
        self.canvas.remove(self.display)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == '-':
            print('battleScreen prev')
            self.switch_to(self.globals.database[self.globals.pokemon_index].screen_name)

        if not self.display.invalid and self.display.check_complete():
            return

        if not self.display.invalid and keycode[1] in ["up", "down", "left", "right"]:
            self.display.move(keycode[1])
        elif not self.display.invalid and keycode[1] in ('1234') and len(keycode[1]) > 0:
            new_ind = int(keycode[1]) - 1
            if new_ind != self.display.current_box and self.display.box.attacks[new_ind].attack.unlocked:
                self.display.box.unselect(self.display.current_box)
                self.display.current_box = new_ind
                self.display.box.select(self.display.current_box)

        if not self.display.invalid and keycode[1] == 'enter':
            box_played = self.player.on_button_enter()

            if box_played is not None:
                # Schedule opponent attack
                self.can_hit = True
                self.rhythm_done = False
                next_beat = quantize_tick_up(self.sched.get_tick(), kTicksPerQuarter) # this is when the above noteseqs start
                self.sched.post_at_tick(self.attack_player, next_beat + self.player_attacks[box_played].song_time + TIME_BETWEEN_ATTACKS)

        if keycode[1] in self.defendable_keys and any([i.attacking for i in self.op_audio_ctrl]):
            self.rhythm_display[self.opp_box_played].on_button_down()
            target_time, _ = self.op_attacks[self.opp_box_played].gems[self.gem_idx]

            hit_condition = (target_time - self.tick <= accuracy_window) and self.can_hit
            if self.direction_enable:
                hit_condition = hit_condition and (keycode[1] == self.op_attacks[self.opp_box_played].gem_directions[self.gem_idx])

            if hit_condition:
                self.rhythm_display[self.opp_box_played].gem_hit(self.gem_idx)
                if self.gem_idx < len(self.op_attacks[self.opp_box_played].gems) - 1:
                    self.gem_idx += 1
                    self.can_hit = True
                else:
                    self.rhythm_done = True
            elif target_time - self.tick > accuracy_window: 
                # self.rhythm_display[self.opp_box_played].gem_pass(self.gem_idx)
                self.rhythm_display[self.opp_box_played].gem_pass(self.gem_idx)
                self.can_hit = False

    def on_key_up(self, keycode):

        if keycode[1] == "spacebar" and any([i.attacking for i in self.op_audio_ctrl]):
            self.rhythm_display[self.opp_box_played].on_button_up()

    def attack_player(self, tick):
        if self.display.notemon_opponent.fainted:
            return
        weapon_select = random.randrange(4)
        new_text = f"{self.display.opponent_name} is about to use {self.op_attacks[weapon_select].name} !\n"
        new_text += f"Listen carefully, and block as each note hits."
        self.display.update_label(new_text)

        self.op_audio_ctrl[weapon_select].play()

    def player_defense_screen(self, tick, index):
        self.display.update_label("")
        self.gem_idx = 0
        # self.player_defending = True

        self.opp_box_played = index
        self.display.remove(self.display.box)
        self.canvas.add(self.rhythm_display[index])

        next_beat = quantize_tick_up(self.sched.get_tick(), kTicksPerQuarter) # this is when the above noteseqs start
        self.sched.post_at_tick(self.player_attack_screen, next_beat + self.op_attacks[index].metro_time + self.op_attacks[index].song_time + TIME_BETWEEN_ATTACKS, [index])

    def player_attack_screen(self, tick, index):
        accuracy = self.rhythm_display[index].reset()
        if accuracy >= defense_threshold: # EDIT ACCURACY THRESHOLD LOGIC AS YOUD LIKE
            new_text = "Defended successfully!"
        else:
            new_text = self.display.take_damage(self.op_attacks[index].damage)
        self.display.update_label(new_text)

        self.canvas.remove(self.rhythm_display[index])
        self.display.add(self.display.box)
        self.player.our_turn = True
        self.opp_box_played = None
        self.tick = None

    def on_update(self):
        self.info.text = "Battle Screen\n"
        if self.direction_enable:
            self.info.text += "Defend by: \n"
            self.info.text += "Pressing up as the pitch goes up,\n"
            self.info.text += "down as the pitch goes down,\n"
            self.info.text += "and space otherwise!\n"
            self.info.text += "And do it all in time with their attack!\n"
        else:
            self.info.text += "Defend by pressing space in time with the attack!\n"
        self.info.text += "-: switch main\n"

        self.display.on_update()
        self.audio.on_update()
        if self.opp_box_played is not None:
            now = self.op_audio_ctrl[self.opp_box_played].get_tick()
            self.rhythm_display[self.opp_box_played].on_update(now)
            self.tick = now

        if any([i.attacking for i in self.op_audio_ctrl]):
            target_time, _ = self.op_attacks[self.opp_box_played].gems[self.gem_idx]
            if target_time + accuracy_window < self.tick and not self.rhythm_done:
                self.rhythm_display[self.opp_box_played].gem_pass(self.gem_idx)
                if self.gem_idx < len(self.op_attacks[self.opp_box_played].gems) - 1:
                    self.gem_idx += 1
                    self.can_hit = True
                else:
                    self.rhythm_done = True

    def on_resize(self, win_size):
        self.background.size = win_size
        if self.rhythm_display:
            for rd in self.rhythm_display:
                rd.on_resize(win_size)
        if self.display:
            self.display.on_resize(win_size)
        resize_topleft_label(self.info)

# Displays all game elements: attack boxes, notemon sprites
class GameDisplay(InstructionGroup):
    def __init__(self, attacks, active_notemon, opp):
        super(GameDisplay, self).__init__()
        self.invalid = False
        self.opp = opp

        #attack boxes
        self.box = AttackBox(attacks, y_marg=y_margin)
        self.add(self.box)

        #battle log
        self.color = Color(1, 1, 1)
        self.add(self.color)

        self.label_x = Window.width // 2
        self.label_y = (1 - 9 * y_margin) * Window.height
        self.text = ""
        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = self.text)
        self.add(self.label)

        unlocked = [ind for ind, attack in enumerate(attacks) if attack.unlocked]
        if len(unlocked) == 0:
            self.invalid = True
            self.update_label("You must train first! Go back to main screen.")
            return
        self.current_box = min(unlocked)
        self.box.select(self.current_box)

        #notemon sprites
        self.us_img = active_notemon.img_src
        self.opponent_img = opp.img_src
        self.notemon_us = NotemonDisplay(100, False, self.us_img)
        self.notemon_opponent = NotemonDisplay(100, True, self.opponent_img)
        self.opponent_name = opp.name
        self.opponent_skill = opp.skill

        self.update_label("You encountered " + self.opponent_name + "!")

        self.add(self.notemon_us)
        self.add(self.notemon_opponent)
        
    
    def move(self, dir):
        new_ind = self.box.move(dir, self.current_box)
        if new_ind != self.current_box and self.box.attacks[new_ind].attack.unlocked:
            self.current_box = new_ind

    def update_label(self, new_text):
        self.remove(self.label)

        self.text = new_text
        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = self.text)
        self.add(Color(1, 1, 1))
        self.add(self.label)
    
    def attack_opponent(self):
        new_text = f"You used {self.box.get_name(self.current_box)} !\n"
        self.update_label(new_text)

    def opponent_defense(self, tick, box):
        if random.random() >= self.opponent_skill:
            damage = self.box.get_damage(box)
            new_text = f"It dealt {damage} damage!\n"
            self.notemon_opponent.take_damage(damage)

            if self.notemon_opponent.fainted:
                new_text += "Opponent notemon fainted! You win :)"
                if not self.opp.unlocked:
                    new_text += f"\nYou gain {self.opp.name}!"
                    self.opp.unlocked = True
        else:
            new_text = "Opponent successfully defended :("

        self.update_label(new_text)

    def take_damage(self, damage):
        new_text = f"It dealt {damage} damage!\n"
        self.notemon_us.take_damage(damage)

        if self.notemon_us.fainted:
            new_text += "We fainted :( Opponent notemon wins!"
        return new_text
    
    def check_complete(self):
        return (self.notemon_opponent.fainted or self.notemon_us.fainted)

    def on_resize(self, win_size):
        if not self.invalid:
            self.notemon_opponent.on_resize(win_size)
            self.notemon_us.on_resize(win_size)
            self.box.on_resize(win_size)

            self.label_x = Window.width // 2
            self.label_y = (1 - 9 * y_margin) * Window.height
            self.label.cpos = (self.label_x, self.label_y)
    
    def on_update(self):
        if not self.invalid:
            self.notemon_opponent.on_update()
            self.notemon_us.on_update()

# Handles game logic.
# Controls the GameDisplay and AudioCtrl based on what happens
class Player(object):
    def __init__(self, audio_ctrl, display, rhythm_display):
        super(Player, self).__init__()

        self.audio_ctrl = audio_ctrl
        self.display = display
        self.rhythm_display = rhythm_display

        self.our_turn = True
        self.complete = False

    def on_button_enter(self):
        if not self.complete: 
            if self.our_turn:
                self.audio_ctrl[self.display.current_box].play()
                self.display.attack_opponent()
                self.our_turn = False
                return self.display.current_box

if __name__ == "__main__":
    attacks = AttackDatabase().get_attack_roster(0)
    run(MainWidget(attacks))
