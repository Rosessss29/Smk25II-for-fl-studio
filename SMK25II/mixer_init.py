from smkconstant import *
import mixer
import ui


def _init_mixer_mode_actions(instance):
    for i, (status_byte, data_byte) in enumerate(KNOB_IDS):
        if i == 7:
            def adjust_offset(value):
                if value == LEFT_TURN:
                    instance.mixer_mode_track_offset = max(instance.mixer_mode_track_offset - 6, 0)
                else:
                    instance.mixer_mode_track_offset = min(instance.mixer_mode_track_offset + 6, 125 - 6)

                ui.miDisplayRect(instance.mixer_mode_track_offset + 1, instance.mixer_mode_track_offset + 6, 1000)

            instance.KNOB_ACTIONS[(status_byte, data_byte, LEFT_TURN)] = adjust_offset
            instance.KNOB_ACTIONS[(status_byte, data_byte, RIGHT_TURN)] = adjust_offset
            continue

        def create_knob_action(status_byte=status_byte, data_byte=data_byte, index=i):
            def action(value):
                track_index = 0 if index == 0 else index + instance.mixer_mode_track_offset
                if instance.is_shift_active:
                    pan_change = 0.02
                    current_pan = mixer.getTrackPan(track_index)
                    if value == LEFT_TURN:
                        new_pan = max(current_pan - pan_change, -1)
                    else:
                        new_pan = min(current_pan + pan_change, 1)
                    mixer.setTrackPan(track_index, new_pan)
                    ui.miDisplayRect(instance.mixer_mode_track_offset + 1, instance.mixer_mode_track_offset + 6, 1000)
                else:
                    volume_change = 0.02
                    current_volume = mixer.getTrackVolume(track_index)
                    if value == LEFT_TURN:
                        new_volume = max(current_volume - volume_change, 0)
                    else:
                        new_volume = min(current_volume + volume_change, 1)
                    mixer.setTrackVolume(track_index, new_volume)
                    ui.miDisplayRect(instance.mixer_mode_track_offset + 1, instance.mixer_mode_track_offset + 6, 1000)

            return action

        instance.KNOB_ACTIONS[(status_byte, data_byte, LEFT_TURN)] = create_knob_action(status_byte, data_byte, i)
        instance.KNOB_ACTIONS[(status_byte, data_byte, RIGHT_TURN)] = create_knob_action(status_byte, data_byte, i)

        def mixer_pad_action_factory(track_index, operation):
            def action():
                if operation == 'shift':
                    instance.is_shift_active = not instance.is_shift_active
                    instance.Sender.send_message(0x90, 0x08, 0x7f)
                    return

                elif operation == 'shift_release':
                    instance.is_shift_active = False
                    instance.Sender.send_message(0x90, 0x08, MixerModeShiftBacklit)
                    return

                if operation == 'left':
                    adjust_offset(LEFT_TURN)
                    instance.Sender.send_message(0x90, 0x07, 0x7f)
                    return True

                if operation == 'right':
                    adjust_offset(RIGHT_TURN)
                    instance.Sender.send_message(0x90, 0x0F, 0x7f)
                    return True

                if track_index == 0:
                    if operation == 'mute':
                        mixer.muteTrack(0, not mixer.isTrackMuted(0))
                        ui.miDisplayRect(instance.mixer_mode_track_offset + 1, instance.mixer_mode_track_offset + 6,
                                         1000)
                else:
                    track_index_adjusted = track_index + instance.mixer_mode_track_offset
                    ui.miDisplayRect(instance.mixer_mode_track_offset + 1, instance.mixer_mode_track_offset + 6, 1000)
                    if operation == 'mute':
                        mixer.muteTrack(track_index_adjusted, not mixer.isTrackMuted(track_index_adjusted))
                    elif operation == 'solo':
                        mixer.soloTrack(track_index_adjusted, not mixer.isTrackSolo(track_index_adjusted))

                return True

            return action

        for pad, (track_index, action_type) in pad_to_action_map.items():
            if action_type == 'shift':
                instance.PAD_ACTIONS[(0x91, pad)] = mixer_pad_action_factory(track_index, 'shift')
                instance.PAD_ACTIONS[(0x81, pad)] = mixer_pad_action_factory(track_index, 'shift_release')
            elif action_type == 'left':
                instance.PAD_ACTIONS[(0x91, pad)] = mixer_pad_action_factory(track_index, 'left')
                instance.PAD_ACTIONS[(0x81, pad)] = lambda: instance.Sender.send_message(0x90, 0x07, MixerModeSwitchBacklit)
            elif action_type == 'right':
                instance.PAD_ACTIONS[(0x91, pad)] = mixer_pad_action_factory(track_index, 'right')
                instance.PAD_ACTIONS[(0x81, pad)] = lambda: instance.Sender.send_message(0x90, 0x0F, MixerModeSwitchBacklit)
            else:
                instance.PAD_ACTIONS[(0x91, pad)] = mixer_pad_action_factory(track_index, action_type)
