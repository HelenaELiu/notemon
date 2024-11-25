#####################################################################
#
# This software is to be used for MIT's class Interactive Music Systems only.
# Since this file may contain answers to homework problems, you MAY NOT release it publicly.
#
#####################################################################

import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run
from imslib.gfxutil import topleft_label, resize_topleft_label, CEllipse, AnimGroup, count_canvas_items
from imslib.screen import ScreenManager, Screen

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.button import Button
from kivy import metrics

from training import TrainingWidget
from battle import MainWidget

# metrics allows kivy to create screen-density-indeptrainingent sizes.
# Here, 20 dp will always be the same physical size on screen regardless of resolution or OS.
# Another option is to use metrics.pt or metrics.sp. See https://kivy.org/doc/stable/api-kivy.metrics.html
font_sz = metrics.dp(20)
button_sz = metrics.dp(100)

# IntroScreen is just like a MainWidget, but it derives from Screen instead of BaseWidget.
# This allows it to work with the ScreenManager system.
class IntroScreen(Screen):
    def __init__(self, **kwargs):
        super(IntroScreen, self).__init__(always_update=False, **kwargs)

        self.info = topleft_label()
        self.info.text = "Welcome to Notemon"
        self.info.text += "→: switch to main\n"
        self.add_widget(self.info)

        self.counter = 0

        # A button is a widget. It must be added with add_widget()
        # button.bind allows you to set up a reaction to when the button is pressed (or released).
        # It takes a function as argument. You can define one, or just use lambda as an inline function.
        # In this case, the button will cause a screen switch
        self.button = Button(text='Notemon', font_size=font_sz, size = (button_sz, button_sz), pos = (Window.width/2, Window.height/2))
        self.button.bind(on_release= lambda x: self.switch_to('main'))
        self.add_widget(self.button)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == '=':
            # tell screen manager to switch from the current screen to some other screen, by name.
            print('IntroScreen next')
            self.switch_to('main')

    # this shows that on_update() gets called when this screen is active.
    # if you want on_update() called when a screen is NOT active, then pass in an extra argument:
    # always_update=True to the screen constructor.
    def on_update(self):
        self.info.text = "Welcome to Notemon\n"
        self.info.text += "=: switch to main\n"
        # self.info.text += f'fps:{kivyClock.get_fps():.1f}\n'
        # self.info.text += f'counter:{self.counter}\n'
        # self.counter += 1

    # on_resize always gets called - even when a screen is not active.
    def on_resize(self, win_size):
        self.button.pos = (Window.width/2, Window.height/2)
        resize_topleft_label(self.info)


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        self.info = topleft_label()
        self.add_widget(self.info)

        # more buttons - one to switch back to the intro screen, and one to switch to the training screen.
        self.button1 = Button(text='Select \n Notemon', font_size=font_sz, size = (button_sz, button_sz), pos = (Window.width * .25, Window.height/2))
        self.button1.bind(on_release= lambda x: self.switch_to('intro'))
        self.add_widget(self.button1)

        self.button2 = Button(text='Training', font_size=font_sz, size = (button_sz, button_sz), pos = (Window.width * .45, Window.height/2))
        self.button2.bind(on_release= lambda x: self.switch_to('training'))
        self.add_widget(self.button2)

        self.button3 = Button(text='Battle', font_size=font_sz, size = (button_sz, button_sz), pos = (Window.width * .65, Window.height/2))
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

class trainingScreen(Screen):
    def __init__(self, **kwargs):
        super(trainingScreen, self).__init__(**kwargs)
        
        # Create an instance of TrainingWidget
        self.training_widget = TrainingWidget()
        
        # Add the TrainingWidget to the screen
        self.add_widget(self.training_widget)
        
        # self.info = topleft_label()
        # self.info.text = "Training Screen\n"
        # self.info.text += "←: switch main\n"
        # self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == '-':
            print('trainingScreen prev')
            self.switch_to('main')

    def on_update(self):
        # self.info.text = "Training Screen\n"
        # self.info.text += "←: switch main\n"
        # self.info.text += f"total score:{self.globals.total_score}"
        
        # Update the TrainingWidget if it has an update method
        if hasattr(self.training_widget, 'on_update'):
            self.training_widget.on_update()

class battleScreen(Screen):
    def __init__(self, **kwargs):
        super(battleScreen, self).__init__(**kwargs)

        # Create an instance of MainWidget (battle)
        self.battle_widget = MainWidget()

        # Add the MainWidget (battle) to the screen
        self.add_widget(self.battle_widget)

        # self.info = topleft_label()
        # self.info.text = "Battle Screen\n"
        # self.info.text += "←: switch main\n"
        # self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == '-':
            print('battleScreen prev')
            self.switch_to('main')

    def on_update(self):
        # self.info.text = "Battle Screen\n"
        # self.info.text += "←: switch main\n"
        # self.info.text += f"total score:{self.globals.total_score}"

        # Update the MainWidget (battle) if it has an update method
        if hasattr(self.battle_widget, 'on_update'):
            self.battle_widget.on_update()
                
        

# optional globals object for data to be shared amongst all screens
class Globals():
    def __init__(self):
        # example of total score
        self.total_score = 0

        # could also create self.audio = Audio(2) here if needed
        # (there should only ever be one Audio instance)


# create the screen manager (this is the replacement for "MainWidget")
sm = ScreenManager(globals=Globals())

# add all screens to the manager. By default, the first screen added is the current screen.
# each screen must have a name argument (so that switch_to() will work).
# If screens need to share data between themselves, feel free to pass in additional arguments
# like a shared data class or they can even know directly about each other as needed.
sm.add_screen(IntroScreen(name='intro'))
sm.add_screen(MainScreen(name='main'))
sm.add_screen(trainingScreen(name='training'))
sm.add_screen(battleScreen(name='battle'))

run(sm)
