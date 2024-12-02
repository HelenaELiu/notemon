from noteseq2 import NoteSequencer2
from imslib.clock import kTicksPerQuarter, quantize_tick_up

class OppAudioController(object):
    def __init__(self, synth, sched, attack, index, callback):
        super(OppAudioController, self).__init__()
        self.synth = synth
        self.sched = sched
        self.metro_time = attack.metro_time

        self.index = index

        self.demo = NoteSequencer2(self.sched, self.synth, 0, (0,88), attack.notes, False, wait=0)
        self.solo = NoteSequencer2(self.sched, self.synth, 0, (0,88), attack.notes, False, wait=attack.metro_time)
        self.metro = NoteSequencer2(self.sched, self.synth, 1, (128, 0), attack.metro, True, wait=0)
        self.total_solo_time = attack.song_time

        # start ready
        self.playing_demo = False
        self.attacking = False
        self.song_start_tick = -10000 # so that we never see the nowbar move when we don't want it to

        self.callback = callback

    def play(self):
        print('hi')
        curr_tick = self.sched.get_tick()

        self.demo.start()
        self.playing_demo = True

        next_beat = quantize_tick_up(curr_tick, kTicksPerQuarter) # this is when the above noteseqs start

        self.playing_demo = True

        # start metro again so player knows beat
        attack_start = next_beat + self.total_solo_time + 480
        self.sched.post_at_tick(self.attack, attack_start)
        self.sched.post_at_tick(self.callback, attack_start, [self.index])

    def attack(self, tick):
        self.metro.start()
        self.solo.start()
        self.playing_demo = False
        self.attacking = True

        self.song_start_tick = quantize_tick_up(tick, kTicksPerQuarter) # this is when the above metro will start

        self.sched.post_at_tick(self.reset, self.song_start_tick + self.metro_time + self.total_solo_time) # afterwards, reset everything

    def reset(self, tick):
        self.metro.stop()
        self.playing_demo = False
        self.attacking = False
        self.song_start_tick = -10000 # so that we never see the nowbar move when we don't want it to

    def get_tick(self):
        return self.sched.get_tick() - self.song_start_tick

class PlayerAudioController(object):
    def __init__(self, synth, sched, attack, index, callback):
        super(PlayerAudioController, self).__init__()
        self.synth = synth
        self.sched = sched
        self.metro_time = attack.metro_time

        self.index = index

        self.solo = NoteSequencer2(self.sched, self.synth, 0, (0,88), attack.notes, False, wait=0)
        self.total_solo_time = attack.song_time

        self.callback = callback

    def play(self):
        self.solo.start()
        curr_tick = self.sched.get_tick()

        next_beat = quantize_tick_up(curr_tick, kTicksPerQuarter) # this is when the above noteseqs start
        defense_start = next_beat + self.total_solo_time
        self.sched.post_at_tick(self.callback, defense_start, [self.index])
