from smkconstant import *


def _init_instruments_mode_actions(instance):

    for i, pad in enumerate(GRIDBIT_TOGGLE_PADS):
        remapped_note = NOTE_REMAPPING.get(pad, pad)

        def create_light_up_action(pad):

            def action_on():
                instance.Sender.send_message(0x90, pad, 0x7F)
                return False

            def action_off():
                instance.Sender.send_message(0x90, pad, InstrumentsModeBacklit)
                return False

            return action_on, action_off

        action_on, action_off = create_light_up_action(i)

        instance.PAD_ACTIONS[(0x91, remapped_note)] = action_on
        instance.PAD_ACTIONS[(0x81, remapped_note)] = action_off











