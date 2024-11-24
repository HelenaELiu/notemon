from training_aud_ctrl import TrainingAudioController
from training_display_components import GemDisplay, ButtonDisplay
from training import GameDisplay, Player

class Defense(object):
    def __init__(self, attack, synth, sched, callback=None):
        super(Defense, self).__init__()
        self.attack = attack
        self.synth = synth
        self.sched = sched

        self.audio_ctrl = TrainingAudioController(synth, sched, attack)
        self.game_display = DefenseGameDisplay(attack, callback)
        self.add(self.game_display) # for this to work, make sure this object is added to your canvas
        # also remove this object after defense is over
        self.player = Player(attack, self.audio_ctrl, self.game_display, defense=True)

    def play(self):
        self.audio_ctrl.play()

    def on_update(self):
        now_tick = self.audio_ctrl.on_update()
        self.game_display.on_update(now_tick)
        self.player.on_update()

    def on_key_down(self, keycode, modifiers):
        # decide what buttons are "valid" to press; for now, any button is valid
        self.player.on_button_down(0)

    def on_key_up(self, keycode, modifiers):
        self.player.on_button_up(0)
        

class DefenseGameDisplay(GameDisplay):
    def __init__(self, attack, callback=None):
        super(DefenseGameDisplay).__init__(attack)
        self.callback = callback
        self.gems = [GemDisplay(lane, time, (1/8 * (lane),1,1), self.tick_to_xpos, attack) for time,lane in attack.gems]

        # button
        # self.buttons = [ButtonDisplay(i, (1/8 * i,0.9,0.5)) for i in range(8)]
        self.buttons = [ButtonDisplay(0, (1,0,0.5), num_lanes=1)]
        for button in self.buttons:
            self.add(button)


    # command player to play
    def play_command(self):
        self.remove(self.listen)
        self.add(self.play)
        for gem in self.gems:
            gem.color.hsv = (0,0,0)

    # reset command
    def remove_play_command(self):
        self.remove(self.play)
        self.callback(self.acc)
