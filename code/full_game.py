#####################################################################
#
# This software is to be used for MIT's class Interactive Music Systems only.
# Since this file may contain answers to homework problems, you MAY NOT release it publicly.
#
#####################################################################

import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run
from imslib.gfxutil import topleft_label, middle_label, resize_topleft_label, CEllipse, AnimGroup, count_canvas_items, resize_middle_label
from imslib.screen import ScreenManager, Screen
from imslib.audio import Audio

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.button import Button
from kivy import metrics
from kivy.uix.image import Image

from training import TrainingWidget
from battle import MainWidget
from attack import Attack
from NotemonSelection import NotemonSelectionBox
from NotemonDatabase import NotemonDatabase, Notemon

from imslib.clock import Clock, SimpleTempoMap, AudioScheduler, tick_str, kTicksPerQuarter, quantize_tick_up
from imslib.synth import Synth

from AttackDatabase import AttackDatabase

# metrics allows kivy to create screen-density-indeptrainingent sizes.
# Here, 20 dp will always be the same physical size on screen regardless of resolution or OS.
# Another option is to use metrics.pt or metrics.sp. See https://kivy.org/doc/stable/api-kivy.metrics.html
font_sz = metrics.dp(20)
button_sz = (metrics.dp(400), metrics.dp(120))
bigger_button_sz = (metrics.dp(800), metrics.dp(120))
# Window width: 1600, Window height: 1200

attacks = AttackDatabase().get_attack_roster(0)
audio = Audio(2)
synth = Synth()
tempo_map  = SimpleTempoMap(120)
sched = AudioScheduler(tempo_map)

# connect scheduler into audio system
audio.set_generator(sched)
sched.set_generator(synth)

# IntroScreen is just like a MainWidget, but it derives from Screen instead of BaseWidget.
# This allows it to work with the ScreenManager system.
class IntroScreen(Screen):
    def __init__(self, **kwargs):
        super(IntroScreen, self).__init__(always_update=False, **kwargs)

        # Add the background image
        self.background = Image(
            source='startscreen.jpg',  # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch to fill the screen
            keep_ratio=False          # Fill the entire screen without maintaining aspect ratio
        )
        self.background.size = Window.size
        self.background.size_hint = (None, None)  # Disable size hinting
        self.background.pos = (0, 0)  # Position the image at the bottom-left corner

        self.add_widget(self.background)
        
        self.button1 = Button(text='Start', font_size=font_sz, size = (button_sz[0], button_sz[1]), pos = ((Window.width - button_sz[0])*.5, Window.height*0.35), background_color=(0, 0.5, 1, 1), font_name="Roboto-Bold.ttf")
        self.button1.bind(on_release= lambda x: self.switch_to('Notemon_red'))
        self.add_widget(self.button1)

        self.button2 = Button(text='Welcome to Notemon', font_size=font_sz*4, size = (bigger_button_sz[0], bigger_button_sz[1]), pos = ((Window.width - bigger_button_sz[0])*.5, Window.height*0.6), background_color=(0, 0.5, 1, 1), font_name="Roboto-Bold.ttf")
        self.add_widget(self.button2)


    def on_key_down(self, keycode, modifiers):
        if keycode[1] == '=':
            # tell screen manager to switch from the current screen to some other screen, by name.
            print('IntroScreen next')
            self.switch_to(self.globals.database[self.globals.pokemon_index].screen_name)

    # this shows that on_update() gets called when this screen is active.
    # if you want on_update() called when a screen is NOT active, then pass in an extra argument:
    # always_update=True to the screen constructor.
    def on_update(self):
        pass

    # on_resize always gets called - even when a screen is not active.
    def on_resize(self, win_size):
        # resize_middle_label(self.info)
        # Update background size to match new window size
        self.background.size = win_size
        
        # Dynamically resize buttons based on the new window size
        bigger_button_width = win_size[0] * 0.5
        button_width = win_size[0] * 0.4  # 40% of window width
        button_height = win_size[1] * 0.1  # 10% of window height

        # Set button sizes and positions
        self.button1.size = (button_width, button_height)
        self.button1.font_size = 0.03*win_size[0]
        self.button1.pos = ((win_size[0] - button_width) * 0.5, win_size[1] * 0.35)

        self.button2.size = (bigger_button_width, button_height)
        self.button2.font_size = 0.05*win_size[0]
        self.button2.pos = ((win_size[0] - bigger_button_width) * 0.5, win_size[1] * 0.6)

class NotemonScreen(Screen):
    def __init__(self, **kwargs):
        super(NotemonScreen, self).__init__(**kwargs)

        # Add the background image
        self.background = Image(
            source='selection.png',  # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch to fill the screen
            keep_ratio=False          # Fill the entire screen without maintaining aspect ratio
        )
        self.background.size = Window.size
        self.background.size_hint = (None, None)  # Disable size hinting
        self.background.pos = (0, 0)  # Position the image at the bottom-left corner

        self.add_widget(self.background)

        self.button1 = Button(text='->', font_size=font_sz, size = (button_sz[0], button_sz[1]), pos = ((Window.width - button_sz[0])*.75, Window.height*0.34), color=(0, 0, 0, 1), background_color=(1, 0.647, 0, 0), font_name="Roboto-Bold.ttf")
        self.button1.bind(on_release= lambda x: self.switch_to(self.switch_fwd))
        self.add_widget(self.button1)

        self.button2 = Button(text='<-', font_size=font_sz, size = (button_sz[0], button_sz[1]), pos = ((Window.width - button_sz[0])*.68, Window.height*0.34), color=(0, 0, 0, 1), background_color=(1, 0.647, 0, 0), font_name="Roboto-Bold.ttf")
        self.button2.bind(on_release= lambda x: self.switch_to(self.switch_back))
        self.add_widget(self.button2)

        self.button3 = Button(text='Select a Notemon:', font_size=font_sz*1.5, size = (button_sz[0], button_sz[1]), pos = ((Window.width - button_sz[0])*.5, Window.height*0.85), background_color=(1, 0.8, 0, 0.8), font_name="Roboto-Bold.ttf")
        self.add_widget(self.button3)

        self.button4 = Button(text='Select', font_size=font_sz*1.5, size = (button_sz[0], button_sz[1]), pos = ((Window.width - button_sz[0])*.8, Window.height*0.425), color=(0, 0, 0, 1), background_color=(1, 0.8, 0, 0), font_name="Roboto-Bold.ttf")
        self.button4.bind(on_release= lambda x: self.switch_to_training())
        self.add_widget(self.button4)

        self.beginning = True

    def on_enter(self):
        self.globals.pokemon_index = self.index
        if self.beginning:
            available_notemon = [g.screen_name for g in self.globals.database]
        else:
            available_notemon = [g.screen_name for g in self.globals.database if g.unlocked or g.screen_name == self.name]

        curr_idx = available_notemon.index(self.name)
        fwd_idx = 0 if curr_idx == len(available_notemon)-1 else curr_idx + 1
        back_idx = curr_idx - 1
        self.switch_fwd = available_notemon[fwd_idx]
        self.switch_back = available_notemon[back_idx]

        self.button1.bind(on_release = lambda x: self.switch_to(self.switch_fwd))
        self.button2.bind(on_release = lambda x: self.switch_to(self.switch_back))

    def on_key_down(self, keycode, modifiers):
        print(keycode)
        if keycode[1] == 'right':
            print('MainScreen next')
            self.switch_to(self.switch_fwd)

        if keycode[1] == 'left':
            print('MainScreen prev')
            self.switch_to(self.switch_back)

    def on_resize(self, win_size):
        self.background.size = win_size
        self.notemon.pos = (win_size[0]*0.45, win_size[1]//2)
        self.notemon.size = (win_size[0]*0.1, win_size[1]*0.17)

        button_width = win_size[0] * 0.05  # 40% of window width
        button_height = win_size[1] * 0.05 # 10% of window height
        self.button1.size = (button_width, button_height)
        self.button1.font_size = 0.03*win_size[0]
        self.button1.pos = ((win_size[0] - button_width) * 0.75, win_size[1] * 0.34)

        self.button2.size = (button_width, button_height)
        self.button2.font_size = 0.03*win_size[0]
        self.button2.pos = ((win_size[0] - button_width) * 0.68, win_size[1] * 0.34)

        self.button3.size = (win_size[0]*0.3, win_size[1]*0.06)
        self.button3.font_size = 0.03*win_size[0]
        self.button3.pos = ((win_size[0] - win_size[0]*0.3) * 0.5, win_size[1] * 0.85)

        self.button4.size = (win_size[0]*0.3, win_size[1]*0.06)
        self.button4.font_size = 0.03*win_size[0]
        self.button4.pos = ((win_size[0] - win_size[0]*0.3) * 0.8, win_size[1] * 0.425)

    def switch_to_training(self):
        self.globals.database[self.index].unlocked = True
        for s in self.globals.notemon_screens:
            s.beginning = False
        self.switch_to('training')

class Notemon_red(NotemonScreen):
    def __init__(self, **kwargs):
        super(Notemon_red, self).__init__(**kwargs)
        self.notemon = Image(
            source='meloetta_red.png',      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(150, 200)           # Set a specific size for the sprite image (adjust as needed)
        )
        self.notemon.pos = (Window.width*0.45, Window.height//2)
        self.add_widget(self.notemon)

        self.index = 0
        self.switch_fwd = 'Notemon_yellow'
        self.switch_back = 'Notemon_purple'

class Notemon_yellow(NotemonScreen):
    def __init__(self, **kwargs):
        super(Notemon_yellow, self).__init__(**kwargs)
        self.notemon = Image(
            source='meloetta_yellow.png',      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(150, 200)           # Set a specific size for the sprite image (adjust as needed)
        )
        self.notemon.pos = (Window.width*0.45, Window.height//2)
        self.add_widget(self.notemon)

        self.index = 1
        self.switch_fwd = 'Notemon_orange'
        self.switch_back = 'Notemon_red'

class Notemon_orange(NotemonScreen):
    def __init__(self, **kwargs):
        super(Notemon_orange, self).__init__(**kwargs)
        self.notemon = Image(
            source='meloetta_orange.png',      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(150, 200)           # Set a specific size for the sprite image (adjust as needed)
        )
        self.notemon.pos = (Window.width*0.45, Window.height//2)
        self.add_widget(self.notemon)

        self.index = 2
        self.switch_fwd = 'Notemon_green'
        self.switch_back = 'Notemon_yellow'

class Notemon_green(NotemonScreen):
    def __init__(self, **kwargs):
        super(Notemon_green, self).__init__(**kwargs)
        self.notemon = Image(
            source='meloetta_green.png',      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(150, 200)           # Set a specific size for the sprite image (adjust as needed)
        )
        self.notemon.pos = (Window.width*0.45, Window.height//2)
        self.add_widget(self.notemon)

        self.index = 3
        self.switch_fwd = 'Notemon_blue'
        self.switch_back = 'Notemon_orange'

class Notemon_blue(NotemonScreen):
    def __init__(self, **kwargs):
        super(Notemon_blue, self).__init__(**kwargs)
        self.notemon = Image(
            source='meloetta_blue.png',      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(150, 200)           # Set a specific size for the sprite image (adjust as needed)
        )
        self.notemon.pos = (Window.width*0.45, Window.height//2)
        self.add_widget(self.notemon)

        self.index = 4
        self.switch_fwd = 'Notemon_purple'
        self.switch_back = 'Notemon_green'

class Notemon_purple(NotemonScreen):
    def __init__(self, **kwargs):
        super(Notemon_purple, self).__init__(**kwargs)
        self.notemon = Image(
            source='meloetta_purple.png',      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(150, 200)           # Set a specific size for the sprite image (adjust as needed)
        )
        self.notemon.pos = (Window.width*0.45, Window.height//2)
        self.add_widget(self.notemon)

        self.index = 5
        self.switch_fwd = 'Notemon_red'
        self.switch_back = 'Notemon_blue'

class BattleTutorial(Screen):
    def __init__(self, **kwargs):
        super(BattleTutorial, self).__init__(**kwargs)

        # Add the background image
        self.background = Image(
            source='battle1.png',  # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch to fill the screen
            keep_ratio=False          # Fill the entire screen without maintaining aspect ratio
        )
        self.background.size = Window.size
        self.background.size_hint = (None, None)  # Disable size hinting
        self.background.pos = (0, 0)  # Position the image at the bottom-left corner

        self.add_widget(self.background)
        self.counter = 0
        self.button1 = Button(text="Welcome to Battle! \nPress '=' to continue", font_size=font_sz, size = (button_sz[0], button_sz[1]), pos = ((Window.width - button_sz[0])*.5, Window.height*0.85), background_color=(0, 0.5, 1, 0), font_name="Roboto-Bold.ttf")
        self.add_widget(self.button1)

        self.notemon = Image()

    def on_enter(self):
        path = f'{self.globals.meloetta_dict[self.globals.pokemon_index]}.png'
        self.notemon = Image(
            source=path,      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(150, 200)           # Set a specific size for the sprite image (adjust as needed)
        )
        self.notemon.pos = (Window.width*0.45, Window.height//2)
        self.add_widget(self.notemon)

        self.on_resize((Window.width, Window.height))

    def on_resize(self, win_size):
        self.background.size = win_size
        self.notemon.pos = (win_size[0]*0.01, win_size[1]*0.8)
        self.notemon.size = (win_size[0]*0.1, win_size[1]*0.17)
        button_width = win_size[0] * 0.4  # 40% of window width
        button_height = win_size[1] * 0.1  # 10% of window height

        # Set button sizes and positions
        self.button1.size = (button_width, button_height)
        self.button1.font_size = 0.03*win_size[0]
        self.button1.pos = ((win_size[0] - button_width) * 0.5, win_size[1] * 0.85)
    
    def on_key_down(self, keycode, modifiers):
        if keycode[1] == '=':
            print(self.globals.pokemon_index)
            self.counter +=1
            if self.counter == 1 and self.globals.pokemon_index < 3: # 0, 1, 2
                self.button1.text = "Defend by pressing space in time with the attack.\nReady? Press '=' to start"
            elif self.counter == 1 and self.globals.pokemon_index > 2: # 3, 4, 5
                self.button1.text = "Defend by pressing up as the pitch goes up, \ndown as the pitch goes down, and space otherwise.\nReady? Press '=' to start"
            else:
                self.switch_to("battle")

class Win(Screen):
    def __init__(self, **kwargs):
        super(Win, self).__init__(**kwargs)

        # Add the background image
        self.background = Image(
            source='battle1.png',  # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch to fill the screen
            keep_ratio=False          # Fill the entire screen without maintaining aspect ratio
        )
        self.background.size = Window.size
        self.background.size_hint = (None, None)  # Disable size hinting
        self.background.pos = (0, 0)  # Position the image at the bottom-left corner

        self.add_widget(self.background)
        self.counter = 0
        self.button1 = Button()

    def on_enter(self):
        self.button1 = Button(text=f"YOU WON! \nYou have now acquired {self.globals.database[self.globals.opp_index].name}. \nPress '=' to return to selection screen to train {self.globals.database[self.globals.opp_index].name}.", font_size=font_sz, size = (button_sz[0], button_sz[1]), pos = ((Window.width - button_sz[0])*.5, Window.height*0.6), background_color=(0, 0.5, 1, 0), font_name="Roboto-Bold.ttf")
        self.button1.bind(on_release= lambda x: self.switch_to(f'{self.globals.pokemon_dict[self.globals.opp_index]}'))
        self.add_widget(self.button1)
        self.on_resize((Window.width, Window.height))
    
    def on_resize(self, win_size):
        self.background.size = win_size
        button_width = win_size[0] * 0.4  # 40% of window width
        button_height = win_size[1] * 0.1  # 10% of window height

        # Set button sizes and positions
        self.button1.size = (button_width, button_height)
        self.button1.font_size = 0.03*win_size[0]
        self.button1.pos = ((win_size[0] - button_width) * 0.5, win_size[1] * 0.6)

class Lose(Screen):
    def __init__(self, **kwargs):
        super(Lose, self).__init__(**kwargs)

        # Add the background image
        self.background = Image(
            source='battle1.png',  # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch to fill the screen
            keep_ratio=False          # Fill the entire screen without maintaining aspect ratio
        )
        self.background.size = Window.size
        self.background.size_hint = (None, None)  # Disable size hinting
        self.background.pos = (0, 0)  # Position the image at the bottom-left corner

        self.add_widget(self.background)
        self.counter = 0
        self.button1 = Button()
        self.notemon = Image()

    def on_enter(self):
        self.button1 = Button(text=f"We fainted :( \nPress '=' to return to selection screen to train.", font_size=font_sz, size = (button_sz[0], button_sz[1]), pos = ((Window.width - button_sz[0])*.5, Window.height*0.6), background_color=(0, 0.5, 1, 0), font_name="Roboto-Bold.ttf")
        self.button1.bind(on_release= lambda x: self.switch_to(f'{self.globals.database[self.pokemon_index]}'))
        self.add_widget(self.button1)
        
        path = f'{self.globals.meloetta_dict[self.globals.pokemon_index]}_fainted.png'
        self.notemon = Image(
            source=path,      # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch
            keep_ratio=True,         # Do not maintain aspect ratio (optional)
            size_hint=(None, None),   # Disable size hinting to allow manual resizing
            size=(150, 200)           # Set a specific size for the sprite image (adjust as needed)
        )
        self.notemon.pos = (Window.width*0.05, Window.height*0.55)
        self.add_widget(self.notemon)
        self.on_resize((Window.width, Window.height))
    
    def on_resize(self, win_size):
        self.background.size = win_size
        self.notemon.pos = (win_size[0]*0.05, win_size[1]*0.55)
        self.notemon.size = (win_size[0]*0.1, win_size[1]*0.17)
        
        button_width = win_size[0] * 0.4  # 40% of window width
        button_height = win_size[1] * 0.1  # 10% of window height

        # Set button sizes and positions
        self.button1.size = (button_width, button_height)
        self.button1.font_size = 0.03*win_size[0]
        self.button1.pos = ((win_size[0] - button_width) * 0.5, win_size[1] * 0.6)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        # Add the background image
        self.background = Image(
            source='background.jpg',  # Replace with the path to your image
            allow_stretch=True,       # Allow the image to stretch to fill the screen
            keep_ratio=False          # Fill the entire screen without maintaining aspect ratio
        )
        self.background.size = Window.size
        self.background.size_hint = (None, None)  # Disable size hinting
        self.background.pos = (0, 0)  # Position the image at the bottom-left corner

        self.add_widget(self.background)

        self.info = topleft_label()
        self.add_widget(self.info)

        # more buttons - one to switch back to the intro screen, and one to switch to the training screen.
        self.button1 = Button(text='Select \n Notemon', font_size=font_sz, size = (button_sz[1], button_sz[1]), pos = (Window.width * .25, Window.height/2))
        self.button1.bind(on_release= lambda x: self.switch_to('intro'))
        self.add_widget(self.button1)

        self.button2 = Button(text='Training', font_size=font_sz, size = (button_sz[1], button_sz[1]), pos = (Window.width * .45, Window.height/2))
        self.button2.bind(on_release= lambda x: self.switch_to('training'))
        self.add_widget(self.button2)

        self.button3 = Button(text='Battle', font_size=font_sz, size = (button_sz[1], button_sz[1]), pos = (Window.width * .65, Window.height/2))
        self.button3.bind(on_release= lambda x: self.switch_to('battle'))
        self.add_widget(self.button3)

        self.objects = AnimGroup()
        self.canvas.add(self.objects)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == '=':
            print('MainScreen next')
            self.switch_to('training')

        if keycode[1] == '-':
            print('MainScreen prev')
            self.switch_to('battle')

    def on_update(self):
        self.info.text = "MainScreen\n"
        self.info.text += "=: switch to training\n"
        self.info.text += "-: switch to battle\n"

    def on_resize(self, win_size):
        resize_topleft_label(self.info)
        self.background.size = win_size
        self.button1.pos = (Window.width * .25, Window.height/2)
        self.button2.pos = (Window.width * .45, Window.height/2)
        self.button3.pos = (Window.width * .65, Window.height/2)

# optional globals object for data to be shared amongst all screens
class Globals():
    def __init__(self):
        # example of total score
        self.total_score = 0
        self.pokemon_index = 0
        self.database = NotemonDatabase().make_notemon_array()
        self.pokemon_dict = {0: 'Notemon_red', 1: 'Notemon_orange', 2: 'Notemon_yellow', 3: 'Notemon_green', 4: 'Notemon_blue', 5: 'Notemon_purple'}
        self.pokemon_counter = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.meloetta_dict = {0: 'meloetta_red', 1: 'meloetta_orange', 2: 'meloetta_yellow', 3: 'meloetta_green', 4: 'meloetta_blue', 5: 'meloetta_purple'}
        self.notemon_screens = None
        self.opp_index = 0
        # could also create self.audio = Audio(2) here if needed
        # self.audio = Audio(2)
        # (there should only ever be one Audio instance)

    def add_notemon_screens(self, screens):
        self.notemon_screens = [s for s in screens if 'Notemon_' in s.name ]

# create the screen manager (this is the replacement for "MainWidget")
sm = ScreenManager(globals=Globals())

# add all screens to the manager. By default, the first screen added is the current screen.
# each screen must have a name argument (so that switch_to() will work).
# If screens need to share data between themselves, feel free to pass in additional arguments
# like a shared data class or they can even know directly about each other as needed.
# sm.add_screen(NotemonSelectionBox(name='intro'))
sm.add_screen(IntroScreen(name='intro'))
sm.add_screen(Notemon_red(name='Notemon_red'))
sm.add_screen(Notemon_orange(name='Notemon_orange'))
sm.add_screen(Notemon_yellow(name='Notemon_yellow'))
sm.add_screen(Notemon_green(name='Notemon_green'))
sm.add_screen(Notemon_blue(name='Notemon_blue'))
sm.add_screen(Notemon_purple(name='Notemon_purple'))
sm.add_screen(TrainingWidget('training', audio, synth, sched))
sm.add_screen(MainWidget('battle', audio, synth, sched))
sm.add_screen(BattleTutorial(name='battletutorial'))
sm.add_screen(Win(name='Win'))
sm.add_screen(Lose(name='Lose'))
sm.globals.add_notemon_screens(sm.screens)
run(sm)
