from globe_view import GlobalView
from sender import Sender
from channel_init import _init_channel_mode_actions
from sequencer_init import _init_sequencer_mode_actions
from mixer_init import _init_mixer_mode_actions
from instrument_init import _init_instruments_mode_actions
from smkconstant import *
import time
import channels
import mixer
import ui

class SMK25IIHandler:

    MODE_CHANNEL = 'Channel'
    MODE_SEQUENCER = 'Sequencer'
    MODE_MIXER = 'Mixer'
    MODE_INSTRUMENTS = 'Instruments'

    def __init__(self):
        self.Sender = Sender
        self.mode = self.MODE_CHANNEL
        self.device_connected = False
        self.last_active_gridbit = -1
        self.knob_turn_counter = 0
        self.gridbit_offset = 0
        self.track_offset = 0
        self.mixer_mode_track_offset = 0
        self.currently_lit_pad = None
        self.last_active_step = None
        self.gridbit_light_states = {message: None for message in GRIDBIT_MESSAGES}
        self.previous_channel_FPC = False
        self.last_selected_channel = None
        self.initialization_complete = False
        self.prev_channel_count = -1
        self.previous_mode = None
        self.channel_lit_pads = set()
        self.sequencer_lit_pads = set()
        self.mixer_lit_pads = set()
        self.instrument_lit_pads = set()
        self.mixer_pad_states = {}
        self.last_selected_channel_states = 0
        self.previous_mute_states = {}
        self.previous_solo_states = {}
        self.current_step = 0
        self.tick_counter = 0
        self.gridbit_states = [False] * 16
        self.is_shift_active = False
        self.PAD_ACTIONS = {}
        self.KNOB_ACTIONS = {}
        self.last_travel_light_step = None
        self.global_view = GlobalView()
        self._init_mode_dependent_actions()
        self._init_mode_independent_actions()

    def is_device_connected(self):
        pass

    def initialize_device(self):
        self.device_connected = True

    def deinitialize_device(self):
        self.Sender.send_message(*OnClose)
        self.device_connected = False

    def shut_down_light_show(self):
        for pad in GRIDBIT_MESSAGES + BANK_A_PAD_LED:
            self.Sender.send_message(0x90, pad, 0x00)
            time.sleep(0.05)

    def _init_mode_independent_actions(self):
        self.global_view.MIDI_ACTIONS.update({
            ChannelModeButton: self.set_channel_mode,
            SequencerModeButton: self.set_sequencer_mode,
            MixerModeButton: self.set_mixer_mode,
            InstrumentsModeButton: self.set_instruments_mode,
        })

    def _init_mode_dependent_actions(self):
        self.PAD_ACTIONS.clear()
        if self.mode == self.MODE_CHANNEL:
            _init_channel_mode_actions(self)
        elif self.mode == self.MODE_SEQUENCER:
            _init_sequencer_mode_actions(self)
        elif self.mode == self.MODE_MIXER:
            _init_mixer_mode_actions(self)
        elif self.mode == self.MODE_INSTRUMENTS:
            _init_instruments_mode_actions(self)

    def globe_backlit(self):
        for idx, item in enumerate(BANK_A_PAD_LED):
            if 0 <= idx < 4:
                self.Sender.send_message(0x90, item, GolbeModeBacklit)
            elif 4 <= idx < 8:
                self.Sender.send_message(0x90, item, GlobeModeSwitchBacklit)
            elif idx == 8:
                self.Sender.send_message(0x90, item, GlobeTransportPlayBacklit)
            elif 9 <= idx < 11:
                self.Sender.send_message(0x90, item, GlobeTransportStopRecBacklit)
            else:
                self.Sender.send_message(0x90, item, GolbeModeBacklitSecond)
            time.sleep(0.05)

    def channel_mode_backlit(self):
        for idx, item in enumerate(GRIDBIT_MESSAGES):
            if idx == 8:
                self.Sender.send_message(0x90, item, channelModeShiftBacklit)
            elif 14 <= idx < 16:
                self.Sender.send_message(0x90, item, ChannelModeSwitchBacklit)
            else:
                self.Sender.send_message(0x90, item, ChannelModeBacklitSecond)

    def channel_mode_backlit_start_up(self):
        for idx, item in enumerate(GRIDBIT_MESSAGES):
            if 0 <= idx < 8:
                self.Sender.send_message(0x90, item, ChannelModeBacklit)
            if idx == 8:
                self.Sender.send_message(0x90, item, channelModeShiftBacklit)
            elif 14 <= idx < 16:
                self.Sender.send_message(0x90, item, ChannelModeSwitchBacklit)
            else:
                self.Sender.send_message(0x90, item, ChannelModeBacklitSecond)
            time.sleep(0.05)

    def sequencer_mode_backlit(self):
        for i in GRIDBIT_MESSAGES:
            self.Sender.send_message(0x90, i, SequencerModeBacklit)

    def mixer_mode_backlit(self):
        self.update_channel_count_backlit()
        for idx, item in enumerate(GRIDBIT_MESSAGES):
            if idx == 0:
                self.Sender.send_message(0x90, item, MixerModeMasterMuteBacklit)
            elif 1 <= idx < 7:
                self.Sender.send_message(0x90, item, MixerModeMuteBacklit)
            elif idx in [7, 15]:
                self.Sender.send_message(0x90, item, MixerModeSwitchBacklit)
            elif idx == 8:
                self.Sender.send_message(0x90, item, MixerModeShiftBacklit)
            elif 9 <= idx < 15:
                self.Sender.send_message(0x90, item, MixerModeSoloBacklit)

    def get_default_light_state(self, idx):
        if idx == 0:
            return MixerModeMasterMuteBacklit
        elif 1 <= idx < 7:
            return MixerModeMuteBacklit
        elif idx in [7, 15]:
            return MixerModeSwitchBacklit
        elif idx == 8:
            return MixerModeShiftBacklit
        elif 9 <= idx < 15:
            return MixerModeSoloBacklit

    def instrument_mode_backlit(self):
        channel_name = self.get_channel_name()
        if self.mode == self.MODE_INSTRUMENTS:
            if channel_name and channel_name.startswith("FPC"):
                for message in GRIDBIT_MESSAGES:
                    self.Sender.send_message(0x90, message, InstrumentsModeFPCBacklit)
                    self.gridbit_light_states[message] = InstrumentsModeFPCBacklit
            else:
                for index, message in enumerate(GRIDBIT_MESSAGES):
                    if index not in [0, 3, 7]:
                        self.Sender.send_message(0x90, message, InstrumentsModeBacklit)
                        self.gridbit_light_states[message] = InstrumentsModeBacklit
                    else:
                        self.Sender.send_message(0x90, message, 0x00)
                        self.gridbit_light_states[message] = 0x00

    def update_channel_count_backlit(self):
        channel_count = channels.channelCount()
        for i in range(8):
            if i < channel_count:
                self.Sender.send_message(0x90, GRIDBIT_MESSAGES[i], ChannelModeBacklit)
            else:
                self.Sender.send_message(0x90, GRIDBIT_MESSAGES[i], 0x00)

    def restore_mode_backlit(self):
        if self.previous_mode == self.mode:
            return
        self.Sender.send_message(0x90, 0x5A, GolbeModeBacklit)
        self.Sender.send_message(0x90, 0x5B, GolbeModeBacklit)
        self.Sender.send_message(0x90, 0x5C, GolbeModeBacklit)
        self.Sender.send_message(0x90, 0x5D, GolbeModeBacklit)

        if self.mode == self.MODE_CHANNEL:
            self.Sender.send_message(0x90, 0x5A, 0x7F)
        elif self.mode == self.MODE_SEQUENCER:
            self.Sender.send_message(0x90, 0x5B, 0x7F)
        elif self.mode == self.MODE_MIXER:
            self.Sender.send_message(0x90, 0x5C, 0x7F)
        elif self.mode == self.MODE_INSTRUMENTS:
            self.Sender.send_message(0x90, 0x5D, 0x7F)

        self.previous_mode = self.mode

    def restore_channel_mode_backlit(self):
        selected_chan = channels.selectedChannel()
        adjusted_channel = selected_chan - self.track_offset
        current_mute_state = channels.isChannelMuted(selected_chan)
        current_solo_state = channels.isChannelSolo(selected_chan)
        self.update_channel_count_backlit()

        if self.mode == self.MODE_CHANNEL:
            if 0 <= adjusted_channel < 8:
                target_pad = GRIDBIT_TOGGLE_PADS[adjusted_channel]
                self.Sender.send_message(0x90, GRIDBIT_MESSAGES[adjusted_channel - self.gridbit_offset], 0x7F)

                mute_light_value = GolbeModeBacklitSecond if current_mute_state else ChannelModeBacklitSecond
                self.Sender.send_message(0x90, pad_to_light_map[0x24], mute_light_value)

                solo_light_value = GolbeModeBacklitSecond if current_solo_state else ChannelModeBacklitSecond
                self.Sender.send_message(0x90, pad_to_light_map[0x2a], solo_light_value)

    def restore_sequencer_mode_backlit(self):
        selected_chan = channels.selectedChannel()
        if self.mode == self.MODE_SEQUENCER:
            for step in range(16):
                current_state = channels.getGridBit(selected_chan, step + self.gridbit_offset)
                light_status = SequencerGridBacklit if current_state else SequencerModeBacklit
                self.Sender.send_message(0x90, GRIDBIT_MESSAGES[step], light_status)
                self.gridbit_states[step] = current_state

    def restore_mixer_mode_backlit(self):
        if self.mode == self.MODE_MIXER:
            for pad, (track_index, operation) in pad_to_action_map.items():
                if track_index == 0:
                    track_index_adjusted = 0
                else:
                    track_index_adjusted = track_index + self.mixer_mode_track_offset
                light_id = pad_to_light_map[pad]

                new_light_state = self.get_default_light_state(light_id)

                if operation == 'mute' and mixer.isTrackMuted(track_index_adjusted):
                    new_light_state = 0x7F

                elif operation == 'solo' and mixer.isTrackSolo(track_index_adjusted):
                    new_light_state = 0x7F

                self.Sender.send_message(0x90, light_id, new_light_state)

    def set_channel_mode(self):
        self.mode = self.MODE_CHANNEL
        self.channel_mode_backlit()
        self.restore_channel_mode_backlit()
        self._init_mode_dependent_actions()

    def set_sequencer_mode(self):
        self.mode = self.MODE_SEQUENCER
        self.sequencer_mode_backlit()
        self.restore_sequencer_mode_backlit()
        self._init_mode_dependent_actions()

    def set_mixer_mode(self):
        self.mode = self.MODE_MIXER
        self.mixer_mode_backlit()
        self.restore_mixer_mode_backlit()
        self._init_mode_dependent_actions()

    def set_instruments_mode(self):
        self.mode = self.MODE_INSTRUMENTS
        self.turn_off_all_pad_lights()
        self.instrument_mode_backlit()
        self._init_mode_dependent_actions()

    def turn_off_all_pad_lights(self):
        for pad_msg in GRIDBIT_MESSAGES:
            self.Sender.send_message(0x90, pad_msg, 0x00)

    def get_channel_name(self):
        current_channel = channels.selectedChannel()
        if current_channel is not None:
            channel_name = channels.getChannelName(current_channel)
            return channel_name

    def switch_channel_up(self):
        current_channel = channels.selectedChannel()
        next_channel = (current_channel + 1) % channels.channelCount()
        channels.selectOneChannel(next_channel)
        self._init_mode_dependent_actions()
        ui.crDisplayRect(self.gridbit_offset, channels.selectedChannel(), 16, 1, 500)

    def switch_channel_down(self):
        current_channel = channels.selectedChannel()
        prev_channel = (current_channel - 1) % channels.channelCount()
        channels.selectOneChannel(prev_channel)
        self._init_mode_dependent_actions()
        ui.crDisplayRect(self.gridbit_offset, channels.selectedChannel(), 16, 1, 500)

    def move_grid_left(self):
        self.gridbit_offset = max(0, self.gridbit_offset - 16)
        self._init_mode_dependent_actions()
        ui.crDisplayRect(self.gridbit_offset, channels.selectedChannel(), 16, 1, 500)

    def move_grid_right(self):
        self.gridbit_offset = min(48, self.gridbit_offset + 16)
        self._init_mode_dependent_actions()
        ui.crDisplayRect(self.gridbit_offset, channels.selectedChannel(), 16, 1, 500)

    def switch_channel_mode_up(self):
        selected_chan = channels.selectedChannel()
        if self.currently_lit_pad is not None:
            self.Sender.send_message(0x90, GRIDBIT_MESSAGES[self.currently_lit_pad - self.gridbit_offset], ChannelModeBacklit)
            self.channel_lit_pads.remove(self.currently_lit_pad)

        self.track_offset = selected_chan + 1
        if self.track_offset >= channels.channelCount():
            self.track_offset = 0

        channels.selectOneChannel(self.track_offset)

        self.channel_lit_pads.add(0)
        self.currently_lit_pad = 0

        ui.crDisplayRect(0, (self.track_offset // 8) * 8, 8, 8, 500, 32)
        self._init_mode_dependent_actions()

    def switch_channel_mode_down(self):
        selected_chan = channels.selectedChannel()
        if self.currently_lit_pad is not None:
            self.Sender.send_message(0x90, GRIDBIT_MESSAGES[self.currently_lit_pad - self.gridbit_offset], ChannelModeBacklit)
            self.channel_lit_pads.remove(self.currently_lit_pad)

        self.track_offset = selected_chan - 1
        if self.track_offset < 0:
            self.track_offset = channels.channelCount() - 1

        channels.selectOneChannel(self.track_offset)

        self.channel_lit_pads.add(0)
        self.currently_lit_pad = 0

        ui.crDisplayRect(0, (self.track_offset // 8) * 8, 8, 8, 500, 32)
        self._init_mode_dependent_actions()

    def action_generator(self, eventData):
        action = self.global_view.MIDI_ACTIONS.get((eventData.status, eventData.data1, eventData.data2))
        if not action:
            action = self.global_view.MIDI_ACTIONS.get((eventData.status, eventData.data1))
        if not action:
            action = self.PAD_ACTIONS.get((eventData.status, eventData.data1, eventData.data2))
        if not action:
            action = self.PAD_ACTIONS.get((eventData.status, eventData.data1))

        if action:
            should_handle = action()
            if should_handle is not False:
                eventData.handled = True

        if self.mode == self.MODE_SEQUENCER:
            if (eventData.status, eventData.data1, eventData.data2) in [ButtonUp, ButtonDown, ButtonLeft, ButtonRight]:
                self.knob_turn_counter += 1
                if self.knob_turn_counter >= 15:
                    if (eventData.status, eventData.data1, eventData.data2) == ButtonUp:
                        self.switch_channel_up()
                    elif (eventData.status, eventData.data1, eventData.data2) == ButtonDown:
                        self.switch_channel_down()
                    elif (eventData.status, eventData.data1, eventData.data2) == ButtonLeft:
                        self.move_grid_left()
                    elif (eventData.status, eventData.data1, eventData.data2) == ButtonRight:
                        self.move_grid_right()
                    self.knob_turn_counter = 0
                eventData.handled = True
                return

        if self.mode == self.MODE_CHANNEL:
            if (eventData.status, eventData.data1) == PadUp:
                self.switch_channel_mode_up()
                eventData.handled = True
            elif (eventData.status, eventData.data1) == PadDown:
                self.switch_channel_mode_down()
                eventData.handled = True
            elif (eventData.status, eventData.data1) in KNOB_IDS:
                knob_action = self.KNOB_ACTIONS.get((eventData.status, eventData.data1, eventData.data2))
                if knob_action:
                    knob_action(eventData.data2)
                    eventData.handled = True
                    return

        if self.mode == self.MODE_MIXER:
            knob_action = self.KNOB_ACTIONS.get((eventData.status, eventData.data1, eventData.data2))
            if knob_action:
                knob_action(eventData.data2)
                eventData.handled = True
                return True

        if self.mode == self.MODE_INSTRUMENTS:

            channel_name = self.get_channel_name()

            if channel_name.startswith("FPC"):
                for message in GRIDBIT_MESSAGES:
                    self.Sender.send_message(0x90, message, InstrumentsModeFPCBacklit)
                if eventData.status == 0x91:
                    self.Sender.send_message(0x90, pad_to_light_map[eventData.data1], 0x7f)
                elif eventData.status == 0x81:
                    self.Sender.send_message(0x90, pad_to_light_map[eventData.data1], InstrumentsModeFPCBacklit)
                return

            elif eventData.data1 in [0x28, 0x2c, 0x35]:
                eventData.status = 0x90
                eventData.handled = True
                # return

            eventData.data1 = NOTE_REMAPPING.get(eventData.data1, eventData.data1)
            action = self.PAD_ACTIONS.get((eventData.status, eventData.data1))

            if action:
                should_handle = action()
                if should_handle is not False:
                    eventData.handled = True













