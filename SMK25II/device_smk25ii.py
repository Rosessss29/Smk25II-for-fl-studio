# name=SMK25II For Fl
from foundation import SMK25IIHandler
from smkconstant import *
from globe_view import GlobalView
from sender import Sender
from idle_update import update_channel_mode_light, travelPadLight, update_gridbit_light,update_mixermode_PadLights, update_instruments_light, update_channel_count_light, update_channel_mute_solo_light

handler = SMK25IIHandler()
sender = Sender()
globalView = GlobalView()

def OnInit():
    handler.channel_mode_backlit_start_up()
    handler.globe_backlit()
    if handler.is_device_connected():
        handler.initialize_device()

def OnDeInit():
    sender.send_message(*OnClose)
    if handler.device_connected:
        handler.deinitialize_device()

def OnMidiIn(eventData):
    handler.action_generator(eventData)

def OnIdle():
    travelPadLight(handler)
    handler.restore_mode_backlit()
    globalView.update_playbutton_light()
    globalView.update_recordbutton_light()
    globalView.update_metronome_light()

    if handler.mode == handler.MODE_CHANNEL:
        update_channel_mode_light(handler)
        update_channel_count_light(handler)
        update_channel_mute_solo_light(handler)
    elif handler.mode == handler.MODE_SEQUENCER:
        update_gridbit_light(handler)
    elif handler.mode == handler.MODE_MIXER:
        update_mixermode_PadLights(handler)
    elif handler.mode == handler.MODE_INSTRUMENTS:
        update_instruments_light(handler)

def OnRefresh(flags):
    if handler.is_device_connected():
        if not handler.device_connected:
            handler.initialize_device()
    else:
        if handler.device_connected:
            handler.deinitialize_device()










