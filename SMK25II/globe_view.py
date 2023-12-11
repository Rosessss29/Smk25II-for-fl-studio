from smkconstant import *
from sender import Sender
import transport
import general
import midi
import ui


class GlobalView:
    def __init__(self):
        self.Sender = Sender
        self.play_button_state = False
        self.record_button_state = False
        self.metronome_button_state = False
        self.MIDI_ACTIONS = {
            ButtonTransportPlay: self.toggle_playback,
            ButtonTransportStop: self.stop_playback,
            ButtonTransportRecord: self.start_recording,
            ButtonFastFoward: self.fast_forward,
            ButtonRewind: self.rewind,
            ButtonMetronome: self.metronome,
            ButtonLoop: self.loop,
            ButtonUndo: self.undo,
            GlobeUp: self.up,
            GlobeDown: self.down,
            GlobeLeft: self.left,
            GlobeRight: self.right,
            ButtonTransportStopRelease: lambda: self.Sender.send_message(0x90, 0x60, GlobeTransportStopRecBacklit),
            ButtonFastFowardRelease: lambda: (self.Sender.send_message(0x90, 0x62, GolbeModeBacklitSecond),
                                              transport.globalTransport(13, 0, midi.PME_System, midi.GT_All))[1],
            ButtonRewindRelease: lambda: (self.Sender.send_message(0x90, 0x63, GolbeModeBacklitSecond),
                                          transport.globalTransport(14, 0, midi.PME_System, midi.GT_All))[1],
            ButtonLoopRelease: lambda: self.Sender.send_message(0x90, 0x65, GolbeModeBacklitSecond),
            ButtonUndoRelease: lambda: self.Sender.send_message(0x90, 0x66, GolbeModeBacklitSecond),
            GlobeUpRelease: lambda: self.Sender.send_message(0x90, 0x55, GlobeModeSwitchBacklit),
            GlobeDownRelease: lambda: self.Sender.send_message(0x90, 0x56, GlobeModeSwitchBacklit),
            GlobeLeftRelease: lambda: self.Sender.send_message(0x90, 0x57, GlobeModeSwitchBacklit),
            GlobeRightRelease: lambda: self.Sender.send_message(0x90, 0x58, GlobeModeSwitchBacklit),
        }

    def toggle_playback(self):
        transport.start()
        self.Sender.send_message(0x90, 0x5F, 0x7F)

    def update_playbutton_light(self):
        is_playing = transport.isPlaying()
        if is_playing != self.play_button_state:
            light_status = 0x0F if is_playing else GlobeTransportPlayBacklit
            self.Sender.send_message(0x90, 0x5F, light_status)
            self.play_button_state = is_playing

    def stop_playback(self):
        transport.stop()
        self.Sender.send_message(0x90, 0x60, 0x0F)

    def start_recording(self):
        transport.globalTransport(12, 1, midi.PME_System, midi.GT_Global)
        self.Sender.send_message(0x90, 0x61, 0x7F)

    def update_recordbutton_light(self):
        is_recording = transport.isRecording()
        if is_recording != self.record_button_state:
            light_status = 0x0F if is_recording else GlobeTransportStopRecBacklit
            self.Sender.send_message(0x90, 0x61, light_status)
            self.record_button_state = is_recording

    def fast_forward(self):
        transport.globalTransport(14, 2, midi.PME_System, midi.GT_All)
        self.Sender.send_message(0x90, 0x63, 0x0F)

    def rewind(self):
        transport.globalTransport(13, 2, midi.PME_System, midi.GT_All)
        self.Sender.send_message(0x90, 0x62, 0x0F)

    def metronome(self):
        transport.globalTransport(110, 1, midi.PME_System, midi.GT_Global)
        self.Sender.send_message(0x90, 0x64, 0x0F)

    def update_metronome_light(self):
        is_metronome_enabled = ui.isMetronomeEnabled()
        if is_metronome_enabled != self.metronome_button_state:
            light_status = 0x0F if is_metronome_enabled else GolbeModeBacklitSecond
            self.Sender.send_message(0x90, 0x64, light_status)
            self.metronome_button_state = is_metronome_enabled

    def loop(self):
        transport.globalTransport(15, 1, midi.PME_System, midi.GT_Global)
        self.Sender.send_message(0x90, 0x65, 0x0F)

    def update_loop_light(self):
        pass

    def undo(self):
        general.undo()
        self.Sender.send_message(0x90, 0x66, 0x0F)

    def up(self):
        ui.up()
        self.Sender.send_message(0x90, 0x55, 0x7F)

    def down(self):
        ui.down()
        self.Sender.send_message(0x90, 0x56, 0x7F)

    def left(self):
        ui.left()
        self.Sender.send_message(0x90, 0x58, 0x7F)

    def right(self):
        ui.right()
        self.Sender.send_message(0x90, 0x57, 0x7F)

