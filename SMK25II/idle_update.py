from smkconstant import *
import channels
import mixer
import transport
import time
import ui

def travelPadLight(instance):
    if instance.mode == instance.MODE_SEQUENCER:
        song_position = mixer.getSongStepPos() % 64
        instance.current_step = song_position - instance.gridbit_offset
        selected_chan = channels.selectedChannel()
        current_state = channels.getGridBit(selected_chan, instance.current_step + instance.gridbit_offset)

        if transport.isPlaying() and song_position >= instance.gridbit_offset and song_position < instance.gridbit_offset + 16:

            previous_step = instance.current_step - 1 if instance.current_step != 0 else 15
            instance.last_active_step = instance.current_step

            instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[instance.current_step], 0x7F)

            if instance.gridbit_states[previous_step]:
                instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[previous_step], SequencerGridBacklit)
            else:
                instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[previous_step], SequencerModeBacklit)

        elif not transport.isPlaying() and instance.last_active_step is not None:
            if instance.gridbit_states[instance.last_active_step]:
                instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[instance.last_active_step], SequencerGridBacklit)
            else:
                instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[instance.last_active_step], SequencerModeBacklit)
            instance.last_active_step = None

def update_instruments_light(instance):
    channel_name = instance.get_channel_name()

    if instance.mode == instance.MODE_INSTRUMENTS:
        if channel_name and channel_name.startswith("FPC"):
            for message in GRIDBIT_MESSAGES:
                if instance.gridbit_light_states[message] != InstrumentsModeFPCBacklit:
                    instance.Sender.send_message(0x90, message, InstrumentsModeFPCBacklit)
                    instance.gridbit_light_states[message] = InstrumentsModeFPCBacklit
                    time.sleep(0.05)
        else:
            for index, message in enumerate(GRIDBIT_MESSAGES):
                if index not in [0, 3, 7]:
                    if instance.gridbit_light_states[message] != InstrumentsModeBacklit:
                        instance.Sender.send_message(0x90, message, InstrumentsModeBacklit)
                        instance.gridbit_light_states[message] = InstrumentsModeBacklit
                        time.sleep(0.05)
                else:
                    if instance.gridbit_light_states[message] != 0x00:
                        instance.Sender.send_message(0x90, message, 0x00)
                        instance.gridbit_light_states[message] = 0x00
                        time.sleep(0.05)

def update_gridbit_light(instance):
    selected_chan = channels.selectedChannel()
    if instance.mode == instance.MODE_SEQUENCER:
        for step in range(16):
            current_state = channels.getGridBit(selected_chan, step + instance.gridbit_offset)

            if current_state != instance.gridbit_states[step]:
                light_status = SequencerGridBacklit if current_state else SequencerModeBacklit
                instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[step], light_status)
                instance.gridbit_states[step] = current_state

def update_channel_mode_light(instance):
    selected_chan = channels.selectedChannel()
    if instance.last_selected_channel == selected_chan:
        return

    instance.last_selected_channel = selected_chan
    instance.track_offset = (selected_chan // 8) * 8
    adjusted_channel = selected_chan % 8

    if instance.mode == instance.MODE_CHANNEL:
        if 0 <= adjusted_channel < 8:
            if instance.currently_lit_pad is not None and instance.currently_lit_pad != adjusted_channel:
                instance.Sender.send_message(0x90,
                                             GRIDBIT_MESSAGES[instance.currently_lit_pad - instance.gridbit_offset],
                                             ChannelModeBacklit)
                instance.channel_lit_pads.discard(instance.currently_lit_pad)

            instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[adjusted_channel], 0x7F)
            instance.channel_lit_pads.add(adjusted_channel)
            instance.currently_lit_pad = adjusted_channel

def update_channel_mute_solo_light(instance):
    selected_chan = channels.selectedChannel()
    current_mute_state = channels.isChannelMuted(selected_chan)

    if selected_chan != instance.last_selected_channel_states or \
       instance.previous_mute_states.get(selected_chan) != current_mute_state:
        instance.previous_mute_states[selected_chan] = current_mute_state
        mute_light_value = GolbeModeBacklitSecond if current_mute_state else ChannelModeBacklitSecond
        instance.Sender.send_message(0x90, pad_to_light_map[0x24], mute_light_value)

    current_solo_state = channels.isChannelSolo(selected_chan)

    if selected_chan != instance.last_selected_channel_states or \
       instance.previous_solo_states.get(selected_chan) != current_solo_state:
        instance.previous_solo_states[selected_chan] = current_solo_state
        solo_light_value = GolbeModeBacklitSecond if current_solo_state else ChannelModeBacklitSecond
        instance.Sender.send_message(0x90, pad_to_light_map[0x2a], solo_light_value)

    instance.last_selected_channel_states = selected_chan

def update_channel_count_light(instance):
    total_channels = channels.channelCount()

    if instance.prev_channel_count == total_channels:
        return

    instance.prev_channel_count = total_channels
    total_channels = min(total_channels, 8)
    selected_chan = channels.selectedChannel()
    adjusted_channel = selected_chan % 8

    for i in range(total_channels):
        if i == adjusted_channel:
            instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[i], 0x7F)
        else:
            instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[i], ChannelModeBacklit)
        instance.channel_lit_pads.add(i)

    for i in range(total_channels, 8):
        instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[i], 0x00)
        instance.channel_lit_pads.discard(i)

def update_mixermode_PadLights(instance):
    if instance.mode == instance.MODE_MIXER:
        for pad, (track_index, operation) in pad_to_action_map.items():
            if track_index == 0:
                track_index_adjusted = 0
            else:
                track_index_adjusted = track_index + instance.mixer_mode_track_offset

            light_id = pad_to_light_map[pad]
            new_light_state = instance.get_default_light_state(light_id)

            if operation == 'mute' and mixer.isTrackMuted(track_index_adjusted):
                new_light_state = 0x7F

            elif operation == 'solo' and mixer.isTrackSolo(track_index_adjusted):
                new_light_state = 0x7F

            if instance.mixer_pad_states.get(pad, None) != new_light_state:
                instance.Sender.send_message(0x90, light_id, new_light_state)
                instance.mixer_pad_states[pad] = new_light_state

