from smkconstant import *
import channels
import ui


def _init_channel_mode_actions(instance):
    for i, pad in enumerate(GRIDBIT_TOGGLE_PADS[:8]):
        if instance.mode == instance.MODE_CHANNEL:
            def create_channel_action(index=None, pad_value=None):
                def action():
                    adjusted_index = index + instance.track_offset
                    if adjusted_index >= channels.channelCount() or adjusted_index < 0:
                        return

                    channels.selectOneChannel(adjusted_index)
                    ui.crDisplayRect(0, instance.track_offset, 8, 8, 500, 32)

                    channels.midiNoteOn(adjusted_index, 60, 127)
                    channels.midiNoteOn(adjusted_index, 60, 0)

                return action

            instance.PAD_ACTIONS[(0x91, pad)] = create_channel_action(i, pad)
            instance.PAD_ACTIONS[PadUp] = lambda: instance.Sender.send_message(0x90, pad_to_light_map[0x2b],
                                                                                      0x7f)
            instance.PAD_ACTIONS[PadDown] = lambda: instance.Sender.send_message(0x90, pad_to_light_map[0x2d],
                                                                                        0x7f)
            instance.PAD_ACTIONS[PadUpRelease] = lambda: instance.Sender.send_message(0x90, pad_to_light_map[0x2b],
                                                                                      ChannelModeSwitchBacklit)
            instance.PAD_ACTIONS[PadDownRelease] = lambda: instance.Sender.send_message(0x90, pad_to_light_map[0x2d],
                                                                                        ChannelModeSwitchBacklit)


    def get_adjusted_index():
        adjusted_index = instance.currently_lit_pad + instance.track_offset
        if 0 <= adjusted_index < channels.channelCount():
            return adjusted_index
        return 0

    # def mute_selected_channel():
    #     adjusted_index = get_adjusted_index()
    #     instance.Sender.send_message(0x90, pad_to_light_map[0x24], 0x7F)
    #     channels.muteChannel(adjusted_index, not channels.isChannelMuted(adjusted_index))
    #
    # instance.PAD_ACTIONS[(0x91, 0x24)] = mute_selected_channel
    # instance.PAD_ACTIONS[(0x81, 0x24)] = lambda: instance.Sender.send_message(0x90, pad_to_light_map[0x24], ChannelModeBacklitSecond)

    def mute_selected_channel():
        adjusted_index = get_adjusted_index()
        channels.muteChannel(adjusted_index, not channels.isChannelMuted(adjusted_index))

    instance.PAD_ACTIONS[(0x91, 0x24)] = mute_selected_channel

    def solo_selected_channel():
        adjusted_index = get_adjusted_index()
        channels.soloChannel(adjusted_index, not channels.isChannelSolo(adjusted_index))

    instance.PAD_ACTIONS[(0x91, 0x2a)] = solo_selected_channel

    def quick_quantize_selected_channel():
        adjusted_index = get_adjusted_index()
        channels.quickQuantize(adjusted_index)
        instance.Sender.send_message(0x90, pad_to_light_map[0x36], 0x7F)

    instance.PAD_ACTIONS[(0x91, 0x36)] = quick_quantize_selected_channel
    instance.PAD_ACTIONS[(0x81, 0x36)] = lambda: instance.Sender.send_message(0x90, pad_to_light_map[0x36], ChannelModeBacklitSecond)

    def toggle_graph_editor_selected_channel():
        adjusted_index = get_adjusted_index()
        is_graph_editor_open = channels.isGraphEditorVisible()

        if is_graph_editor_open:
            channels.showGraphEditor(False, 0, 0, adjusted_index, 1)  # Attempt to hide the graph editor
        else:
            channels.showGraphEditor(True, 0, 0, adjusted_index, 1)  # Attempt to show the graph editor

        instance.Sender.send_message(0x90, pad_to_light_map[0x30], 0x7F)

    instance.PAD_ACTIONS[(0x91, 0x30)] = toggle_graph_editor_selected_channel
    instance.PAD_ACTIONS[(0x81, 0x30)] = lambda: instance.Sender.send_message(0x90, pad_to_light_map[0x30],
                                                                              ChannelModeBacklitSecond)

    def open_piano_roll_of_selected_channel():
        adjusted_index = get_adjusted_index()
        channels.showCSForm(adjusted_index, -1)  # Toggle the piano roll

        instance.Sender.send_message(0x90, pad_to_light_map[0x2f], 0x7F)

    instance.PAD_ACTIONS[(0x91, 0x2f)] = open_piano_roll_of_selected_channel
    instance.PAD_ACTIONS[(0x81, 0x2f)] = lambda: instance.Sender.send_message(0x90, pad_to_light_map[0x2f], ChannelModeBacklitSecond)

    def press_shift():
        instance.is_shift_active = True
        instance.Sender.send_message(0x90, pad_to_light_map[0x25], 0x7F)
        # instance.Sender.send_message(0x90, pad_to_light_map[0x25], 0x7F)

    instance.PAD_ACTIONS[(0x91, 0x25)] = press_shift

    def release_shift():
        instance.is_shift_active = False
        instance.Sender.send_message(0x90, pad_to_light_map[0x25], channelModeShiftBacklit)

    instance.PAD_ACTIONS[(0x81, 0x25)] = release_shift

    for i, (status_byte, knob_data_byte) in enumerate(KNOB_IDS):
        volume_change = 0.02
        pan_change = 0.02

        def create_knob_action(index=i):
            def action(value):
                adjusted_index = index + instance.track_offset

                if adjusted_index >= channels.channelCount() or adjusted_index < 0:
                    return

                if instance.is_shift_active:
                    current_pan = channels.getChannelPan(adjusted_index)
                    if value == LEFT_TURN:
                        new_pan = max(current_pan - pan_change, -1)
                    elif value == RIGHT_TURN:
                        new_pan = min(current_pan + pan_change, 1)
                    else:
                        return
                    channels.setChannelPan(adjusted_index, new_pan)
                    ui.crDisplayRect(0, instance.track_offset, 8, 8, 500, 8)
                else:
                    current_volume = channels.getChannelVolume(adjusted_index)
                    if value == LEFT_TURN:
                        new_volume = max(current_volume - volume_change, 0)
                    elif value == RIGHT_TURN:
                        new_volume = min(current_volume + volume_change, 1)
                    else:
                        return
                    channels.setChannelVolume(adjusted_index, new_volume)
                    ui.crDisplayRect(0, instance.track_offset, 8, 8, 500, 8)

            return action

        instance.KNOB_ACTIONS[(status_byte, knob_data_byte, LEFT_TURN)] = create_knob_action()
        instance.KNOB_ACTIONS[(status_byte, knob_data_byte, RIGHT_TURN)] = create_knob_action()