import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import Widget, run, lookup
from imslib.screen import Screen
# from imslib.audio import Audio
# from imslib.mixer import Mixer
# from imslib.wavegen import WaveGenerator
# from imslib.wavesrc import WaveBuffer, WaveFile
# from imslib.noteseq import NoteSequencer
from imslib.synth import Synth
from imslib.clock import SimpleTempoMap, AudioScheduler
from kivy.core.window import Window
from imslib.gfxutil import topleft_label, resize_topleft_label
from functools import reduce

from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy import metrics

from attack import Attack
from training_aud_ctrl import TrainingAudioController
from AttackDisplay import AttackDisplay, AttackBox
from training_display_components import btns, accuracy_window
from AttackDatabase import AttackDatabase

y_margin = 0.3 #distance from bottom of boxes to edge of screen
meloetta_dict = {0: 'meloetta_red', 1: 'meloetta_yellow', 2: 'meloetta_orange', 3: 'meloetta_green', 4: 'meloetta_blue', 5: 'meloetta_purple'}
font_sz = metrics.dp(15)
button_sz = (metrics.dp(400), metrics.dp(120))

class TrainingWidget(Screen):
    def __init__(self, name, audio, synth, sched):
        super(TrainingWidget, self).__init__(name)
        # audio
        self.audio = audio
        self.synth = synth
        # self.synth = Synth()# create TempoMap, AudioScheduler
        # self.tempo_map  = SimpleTempoMap(120)
        self.sched = sched
        # self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        # self.audio.set_generator(self.sched)
        # self.sched.set_generator(self.synth)

        # change this to make the attacks not all just winter haha
        self.game_display = None
        self.attack_box = None

        # Add the background image
        self.background = Image(
            source='training1.png',  # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch to fill the screen
            keep_ratio=False          # Fill the entire screen without maintaining aspect ratio
        )
        self.background.size = Window.size
        self.background.size_hint = (None, None)  # Disable size hinting
        self.background.pos = (0, 0)  # Position the image at the bottom-left corner
        self.add_widget(self.background)

        self.button1 = Button(text='Hi, I am Meloetta. \nHere you can train for battle.\nPress "=" to continue.', font_size=font_sz, size = (button_sz[0], button_sz[1]), pos = ((Window.width - button_sz[0])*.3, Window.height*0.9), color=(0, 0, 0, 1), background_color=(1, 0.647, 0, 0), font_name="Roboto-Bold.ttf")
        self.button1.bind(on_release= lambda x: self.switch_to('Notemon_orange'))
        self.add_widget(self.button1)

        self.notemon = Image()
        self.chatbox = Image()
        self.battle_unlocked = False
        # self.info = topleft_label()
        # self.add_widget(self.info)

    def on_enter(self):
        if self.globals.pokemon_counter[self.globals.pokemon_index] == 0:
                self.button1.text = "Hi, I am Meloetta. \nHere you can train for battle.\nPress '=' to continue."
        elif self.globals.pokemon_counter[self.globals.pokemon_index] == 1:
                self.button1.text = "Press '-' to pick a different color notemon. \nPress '=' to continue."
        elif self.globals.pokemon_counter[self.globals.pokemon_index] == 2:
            self.button1.text = "To train an attack, unlock at least \nhalf the gems AND have accuracy > 0. \nPress '=' to continue."
        elif self.globals.pokemon_counter[self.globals.pokemon_index] == 3:
            self.button1.text = "Press ENTER to select an attack. \nPress '=' to continue."
        else:
            self.button1.text = f"percent gems unlocked: {self.game_display[self.curr_attack_index].get_training_percent() * 100:.0f}%\naccuracy of run: {self.game_display[self.curr_attack_index].acc}\nnumber of attacks trained: {self.active_notemon.attacks_trained}\n" 

        self.active_notemon = self.globals.database[self.globals.pokemon_index]
        self.attacks = self.globals.database[self.globals.pokemon_index].attacks

        ### each ATTACK gets an AUDIO CONTROL, GAME DISPLAY, PLAYER, and ATTACK DISPLAY
        self.audio_ctrl = [TrainingAudioController(self.synth, self.sched, attack) for attack in self.attacks]
        self.game_display = [attack.game_display for attack in self.attacks]
        self.player = [Player(self.attacks[i], self.audio_ctrl[i], self.game_display[i]) for i in range(len(self.attacks))]
        self.attack_box = AttackBox(self.attacks, True, y_marg=y_margin)
        self.canvas.add(self.attack_box)
        
        self.curr_attack_index = 0  # attack that is currently selected
        self.attack_box.select(self.curr_attack_index) # display attack as selected in the selector
        self.canvas.add(self.game_display[self.curr_attack_index]) # display current attack
        self.training = False

        self.notemon = Image(
            source=f'{meloetta_dict[self.globals.pokemon_index]}.png',      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(150, 200)           # Set a specific size for the sprite image (adjust as needed)
        )
        
        self.notemon.pos = (Window.width*0.01, Window.height*0.8)
        self.add_widget(self.notemon)

        self.chatbox = Image(
            source='chatbox1.png',      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(800, 600)           # Set a specific size for the sprite image (adjust as needed)
        )
        
        self.chatbox.pos = (Window.width*0.1, Window.height*0.67)
        self.add_widget(self.chatbox)

        self.on_resize((Window.width, Window.height))

    def on_exit(self):
        self.canvas.remove(self.attack_box)
        self.canvas.remove(self.game_display[self.curr_attack_index])

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == '=':
            print(self.globals.pokemon_counter)

            # Update button text based on the press count
            
            self.globals.pokemon_counter[self.globals.pokemon_index] += 1  # Increment the counter

            if self.globals.pokemon_counter[self.globals.pokemon_index] == 1:
                self.button1.text = "Press '-' to pick a different color notemon from the ones available. \nPress '=' to continue."
            elif self.globals.pokemon_counter[self.globals.pokemon_index] == 2:
                self.button1.text = "To train an attack, unlock at least \nhalf the gems AND have accuracy > 0. \nPress '=' to continue."
            elif self.globals.pokemon_counter[self.globals.pokemon_index] == 3:
                self.button1.text = "Use the arrow keys to choose an attack. \nPress '=' to continue."
            else:
                self.button1.text = f"Press ENTER to select the attack{ '(this attack is trained)' if self.attacks[self.curr_attack_index].unlocked == True else ''}. \nPercent gems unlocked: {self.game_display[self.curr_attack_index].get_training_percent() * 100:.0f}%\nAccuracy of run: {self.game_display[self.curr_attack_index].acc}" 

# Number of attacks trained: {self.active_notemon.attacks_trained}\n

        if keycode[1] == '-':
            print('trainingScreen prev')
            self.switch_to(self.globals.database[self.globals.pokemon_index].screen_name)

        # only change selected attack if not actively training
        elif not self.training and keycode[1] in ('right', 'left', 'up', 'down'):
            new_ind = self.attack_box.move(keycode[1], self.curr_attack_index)
            if new_ind != self.curr_attack_index:
                self.canvas.remove(self.game_display[self.curr_attack_index])
                self.curr_attack_index = new_ind
                self.canvas.add(self.game_display[self.curr_attack_index])

        elif not self.training and keycode[1] in ('1234'):
            new_ind = int(keycode[1]) - 1
            if new_ind != self.curr_attack_index:
                self.attack_box.attacks[self.curr_attack_index].unselect()
                self.canvas.remove(self.game_display[self.curr_attack_index])
                self.curr_attack_index = new_ind
                self.canvas.add(self.game_display[self.curr_attack_index])
                self.attack_box.attacks[self.curr_attack_index].select()

        # train the selected attack
        elif keycode[1] == "enter" and not self.training:
            self.audio_ctrl[self.curr_attack_index].play()
            self.player[self.curr_attack_index].done = False

        # play a note 
        button_idx = lookup(keycode[1], btns, (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('down', button_idx)
            self.player[self.curr_attack_index].on_button_down(button_idx)
        

    def on_key_up(self, keycode):
        # button up
        button_idx = lookup(keycode[1], btns, (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('up', button_idx)
            self.player[self.curr_attack_index].on_button_up(button_idx)

    def scoring(self):
        # Get the training accuracy percentage
        training_percent = self.game_display[self.curr_attack_index].get_training_percent()
        curr_acc = self.game_display[self.curr_attack_index].acc

        # Check if the training is mastered
        if training_percent > 0.5 and curr_acc > 0 and not self.attacks[self.curr_attack_index].unlocked:
            self.active_notemon.attacks_trained += 1
            self.attacks[self.curr_attack_index].unlocked = True
            self.button2 = Button(text='Click to go to Battle', font_size=font_sz, size = (button_sz[1], button_sz[1]), pos = (Window.width * .8, Window.height*.8))
            self.button2.bind(on_release= lambda x: self.switch_to('battle'))
            self.add_widget(self.button2)
            self.battle_unlocked = True
            return

    # handle changing displayed elements when window size changes
    # This function should call GameDisplay.on_resize
    def on_resize(self, win_size):
        self.background.size = win_size
        self.notemon.pos = (win_size[0]*0.01, win_size[1]*0.8)
        self.notemon.size = (win_size[0]*0.1, win_size[1]*0.17)
        
        self.chatbox.pos = (win_size[0]*0.1, win_size[1]*0.67)
        self.chatbox.size = (win_size[0]*0.5, win_size[1]*0.5)

        if self.game_display:
            for gd in self.game_display:
                gd.on_resize(win_size)
        if self.attack_box:
            self.attack_box.on_resize(win_size)
        # resize_topleft_label(self.info)

        button_width = win_size[0] * 0.05  # 40% of window width
        button_height = win_size[1] * 0.05 # 10% of window height
        self.button1.size = (button_width, button_height)
        self.button1.font_size = 0.02*win_size[0]
        self.button1.pos = ((win_size[0] - button_width) * 0.3, win_size[1] * 0.9)

        if self.battle_unlocked == True:
            self.button2.size = (button_width, button_height)
            self.button2.font_size = 0.02*win_size[0]
            self.button2.pos = ((win_size[0] - button_width) * 0.8, win_size[1] * 0.8)

    def on_update(self):
        self.audio.on_update() # used to be # self.audio_ctrl.on_update()
        # everyone uses audio's time now, which is in ticks instead of seconds
        now = self.audio_ctrl[self.curr_attack_index].get_tick()
        self.game_display[self.curr_attack_index].on_update(now)
        self.player[self.curr_attack_index].on_update(now)
        
        self.scoring()

        self.training = reduce(lambda tot,aud_ctrl: tot or aud_ctrl.training, self.audio_ctrl, False)

        if self.globals.pokemon_counter[self.globals.pokemon_index] > 3:
            self.button1.text = f"Press ENTER to select the attack.{ ' (This attack is trained.)' if self.attacks[self.curr_attack_index].unlocked == True else ''} \nPercent gems unlocked: {self.game_display[self.curr_attack_index].get_training_percent() * 100:.0f}%\nAccuracy of run: {self.game_display[self.curr_attack_index].acc}" 

        # self.info.text = "Training Screen; '-' switches to main. ENTER to select attack.\n"
        # self.info.text += "To train an attack, unlock at least half the gems AND have accuracy > 0\n"
        # self.info.text += f'percent gems unlocked: {self.game_display[self.curr_attack_index].get_training_percent() * 100:.0f}%\n'
        # self.info.text += f'accuracy of run: {self.game_display[self.curr_attack_index].acc}\n'
        # self.info.text += f'number of attacks trained: {self.active_notemon.attacks_trained}\n'
        
        # self.info.text = 'p: pause/unpause song\n'
        # self.info.text += f'song time: {now:.2f}\n'
        # self.info.text += f'index {self.curr_attack_index}\n'
        # self.info.text += f'num objects: {self.game_display[self.curr_attack_index].get_num_object()}\n'

class Player(object):
    def __init__(self, attack, audio_ctrl, display, defense=False):
        super(Player, self).__init__()

        self.gems = attack.gems
        self.attack = attack
        self.idx = 0
        self.defense = defense

        self.display = display
        self.audio_ctrl = audio_ctrl
        self.tick = 0
        self.done = False

        self.acc = 0

        self.listening = False
        self.playing = False

    # called by MainWidget
    def on_button_down(self, lane):
        # self.lanes.add(lane)
        self.display.on_button_down(lane)
        self.audio_ctrl.synth.noteon(2, self.attack.lanes[lane], 100)
        if self.done or not self.audio_ctrl.player:
            return
        

        target_time = self.gems[self.idx][0]
        target_lane = self.gems[self.idx][1]
        # print(lane, target_lane)
        # print(self.tick, target_time)
        if target_time - accuracy_window < self.tick:
            if self.defense or lane == target_lane:
                self.display.gem_hit(self.idx)
                self.acc += 1
                self.display.set_acc(self.acc)
                # only do this if gem hits. 
                if self.idx < len(self.gems) - 1:
                    self.idx += 1
                else:
                    self.done = True
                    self.idx = 0

                return
        
        # if you hit an unneccesary note:
            self.acc -= 1
            self.display.set_acc(self.acc)

    # called by MainWidget
    def on_button_up(self, lane):
        # self.lanes.remove(lane)
        self.display.on_button_up(lane)
        self.audio_ctrl.synth.noteoff(2, self.attack.lanes[lane])

    # needed to check for pass gems (ie, went past the slop window)
    def on_update(self, tick):
        if not self.listening and not self.playing and self.audio_ctrl.training:
            self.acc = 0
            self.display.set_acc(self.acc)
            self.listening = True
            self.display.listen_command()

        if not self.playing and self.audio_ctrl.player:
            self.playing = True
            self.listening = False
            self.display.play_command()

        if self.playing and not self.audio_ctrl.training:
            self.playing = False
            self.display.remove_play_command()

        self.tick = tick
        if self.done or not self.audio_ctrl.player:
            return

        if self.gems[self.idx][0] + accuracy_window < tick:
            self.display.gem_pass(self.idx)
            self.acc -= 1
            self.display.set_acc(self.acc)
            
            if self.idx < len(self.gems) - 1:
                self.idx += 1
            else:
                self.done = True
                self.idx = 0

if __name__ == "__main__":
    attacks = AttackDatabase().get_attack_roster(0)
    run(TrainingWidget(attacks))
