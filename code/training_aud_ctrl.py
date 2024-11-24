from noteseq2 import NoteSequencer2
from imslib.clock import kTicksPerQuarter, quantize_tick_up

class TrainingAudioController(object):
    def __init__(self, synth, sched, attack):
        super(TrainingAudioController, self).__init__()
        self.synth = synth
        self.sched = sched
        self.metro_time = attack.metro_time

        self.solo = NoteSequencer2(self.sched, self.synth, 0, (0,88), attack.notes, False, wait=attack.metro_time)
        self.metro = NoteSequencer2(self.sched, self.synth, 1, (128, 0), attack.metro, True, wait=0)
        self.total_solo_time = attack.song_time

        # start ready
        self.training = False
        self.player = False
        self.song_start_tick = -10000 # so that we never see the nowbar move when we don't want it to

    # start / stop the song
    def play(self):
        print('hi')
        curr_tick = self.sched.get_tick()

        self.metro.start()
        self.solo.start()
        next_beat = quantize_tick_up(curr_tick, kTicksPerQuarter) # this is when the above noteseqs start
        # self.sched.post_at_tick(self._play_song, next_beat)
        self.song_start_tick = next_beat
        self.training = True

        # pause metronome for a little bit before starting player's turn
        self.sched.post_at_tick(self._stop_metro, next_beat + self.metro_time + self.total_solo_time)

        # start metro again so player knows beat
        player_start = next_beat + self.metro_time + self.total_solo_time + 480
        self.sched.post_at_tick(self._player_turn, player_start)

    # def _play_song(self, tick):
    #     print('playing', tick)
    #     self.metro.start()
    #     self.solo.start()
    #     self.song_start_tick = tick

    def _stop_metro(self, tick):
        self.metro.stop()

    def _player_turn(self, tick):
        self.metro.start()
        self.player = True # now the player will playing
        self.song_start_tick = quantize_tick_up(tick, kTicksPerQuarter) # this is when the above metro will start
        self.sched.post_at_tick(self._set_to_normal, self.song_start_tick + self.metro_time + self.total_solo_time) # afterwards, reset everything

    def _set_to_normal(self, tick):
        self.metro.stop()
        self.training = False
        self.player = False
        self.song_start_tick = -10000 # so that we never see the nowbar move when we don't want it to

    # return current time (in ticks) of song
    def get_tick(self):
        return self.sched.get_tick() - self.song_start_tick