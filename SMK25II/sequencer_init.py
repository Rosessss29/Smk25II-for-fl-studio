from smkconstant import *
import channels
import ui


def _init_sequencer_mode_actions(instance):
    for i, pad in enumerate(GRIDBIT_TOGGLE_PADS):
        index_with_offset = i + instance.gridbit_offset

        def create_gridbit_action(index):
            def action():
                is_bit_set = channels.getGridBit(channels.selectedChannel(), index)
                channels.setGridBit(channels.selectedChannel(), index, not is_bit_set)

                if is_bit_set:
                    instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[index - instance.gridbit_offset], SequencerModeBacklit)
                else:
                    instance.Sender.send_message(0x90, GRIDBIT_MESSAGES[index - instance.gridbit_offset], SequencerGridBacklit)

            return action

        instance.PAD_ACTIONS[(0x91, pad)] = create_gridbit_action(index_with_offset)
