import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.audio import Audio
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window
from imslib.gfxutil import topleft_label, resize_topleft_label, AnimGroup, KFAnim, CEllipse

x_margin = 1/10
y_margin = 1/32
radius_margin = 1/16


class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.display = GameDisplay()

        self.canvas.add(self.display)

        self.info = topleft_label()
        self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "up":
            self.display.up_key()
        elif keycode[1] == "down":
            self.display.down_key()
        elif keycode[1] == "left":
            self.display.left_key()
        elif keycode[1] == "right":
            self.display.right_key()
        elif keycode[1] == "enter":
            self.display.play()

    def on_resize(self, win_size):
        resize_topleft_label(self.info)
        self.display.on_resize(win_size)

    def on_update(self):
        self.display.on_update()

        self.info.text = 'Notemon!\n'
        self.info.text += f'our health: {self.display.get_our_health()}\n'
        self.info.text += f'opponent health: {self.display.get_opponent_health()}\n'


# Display for a single attack box
class AttackDisplay(InstructionGroup):
    def __init__(self, index, name, damage, wave_path):
        super(AttackDisplay, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.audio.set_generator(self.mixer)

        self.index = index
        self.name = name
        self.damage = damage
        self.wave_path = wave_path

        #graphics
        colors = [0.1, 0.5, 0.7, 0.85]
        self.color = Color(hsv=(colors[index], 1, 1))
        self.color.a = 0.7
        self.add(self.color)
        
        #TODO, recalculate w and h based on margins

        w = 600
        h = 200

        x1 = x_margin * Window.width
        y1 = 2 * y_margin * Window.width + h

        y2 = y_margin * Window.width
        x2 = (1 - x_margin) * Window.width - w

        if index == 0:
            self.box = Line(rectangle = (x1, y1, w, h), width = 3)
        elif index == 1:
            self.box = Line(rectangle = (x2, y1, w, h), width = 3)
        elif index == 2:
            self.box = Line(rectangle = (x1, y2, w, h), width = 3)
        elif index == 3:
            self.box = Line(rectangle = (x2, y2, w, h), width = 3)

        self.add(self.box)

    def select(self):
        self.color.a = 1
        self.box.width = 10

    def unselect(self):
        self.color.a = 0.7
        self.box.width = 3

    # play the song associated with this attack
    def play(self):
        print(self.wave_path)
        self.song = WaveGenerator(WaveFile(self.wave_path))
        self.mixer.add(self.song)
        self.song.play()
    
    def get_damage(self):
        return self.damage
    
    def on_update(self):
        self.audio.on_update()


# Display for a single notemon sprite
class NotemonDisplay(InstructionGroup):
    def __init__(self, health, opponent):
        super(NotemonDisplay, self).__init__()

        self.health = health
        self.fainted = False
        self.opponent = opponent

        #graphics
        #TODO: change the y1 and y2 calculations

        r = radius_margin * Window.width

        x1 = x_margin * Window.width
        y1 = (1 - 14 * y_margin) * Window.height

        x2 = (1 - x_margin) * Window.width
        y2 = (1 - 4 * y_margin) * Window.height

        if opponent:
            self.color = Color(1, 0, 0)
            self.notemon = Line(circle = (x1, y1, r), width = 3)
        else: #our pokemon
            self.color = Color(0, 1, 0)
            self.notemon = Line(circle = (x2, y2, r), width = 3)

        self.add(self.color)
        self.add(self.notemon)
    
    def take_damage(self, damage):
        if self.health - damage < 0:
            self.health = 0
            self.fainted = True
        else:
            self.health -= damage
        

# Displays all game elements: attack boxes, notemons
class GameDisplay(InstructionGroup):
    def __init__(self):
        super(GameDisplay, self).__init__()

        self.boxes = []

        #gems and downbeats
        self.box0 = AttackDisplay(0, "Vivaldi - Winter", 10, "./vivaldi_winter.wav")
        self.boxes.append(self.box0)
        self.add(self.box0)

        self.box1 = AttackDisplay(1, "Beethoven - 5th Symphony", 20, "./beethoven_5th_symphony.wav")
        self.boxes.append(self.box1)
        self.add(self.box1)

        self.box2 = AttackDisplay(2, "Box 2", 5, "./box2.wav")
        self.boxes.append(self.box2)
        self.add(self.box2)

        self.box3 = AttackDisplay(3, "Box 3", 30, "./box3.wav")
        self.boxes.append(self.box3)
        self.add(self.box3)

        self.current_box = 0

        self.boxes[self.current_box].select()

        self.notemon_us = NotemonDisplay(100, False)
        self.notemon_opponent = NotemonDisplay(100, True)

        self.add(self.notemon_us)
        self.add(self.notemon_opponent)
    
    def up_key(self):
        if self.current_box == 2 or self.current_box == 3:
            self.boxes[self.current_box].unselect()
            self.current_box -= 2
            self.boxes[self.current_box].select()
    
    def down_key(self):
        if self.current_box == 0 or self.current_box == 1:
            self.boxes[self.current_box].unselect()
            self.current_box += 2
            self.boxes[self.current_box].select()
    
    def left_key(self):
        if self.current_box == 1 or self.current_box == 3:
            self.boxes[self.current_box].unselect()
            self.current_box -= 1
            self.boxes[self.current_box].select()
    
    def right_key(self):
        if self.current_box == 0 or self.current_box == 2:
            self.boxes[self.current_box].unselect()
            self.current_box += 1
            self.boxes[self.current_box].select()
    
    def play(self):
        self.boxes[self.current_box].play()
        self.notemon_opponent.take_damage(self.boxes[self.current_box].get_damage())

        print(self.notemon_opponent.health)
        print(self.notemon_us.health)
    
    def get_our_health(self):
        return self.notemon_us.health

    def get_opponent_health(self):
        return self.notemon_opponent.health
    
    def on_resize(self, win_size):
        #TODO
        pass

    def on_update(self):
        self.boxes[self.current_box].on_update()


if __name__ == "__main__":
    run(MainWidget())
