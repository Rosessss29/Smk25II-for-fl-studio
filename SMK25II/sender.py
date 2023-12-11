import device

class Sender:
    @staticmethod
    def send_message(status, data1, data2):
        device.midiOutMsg(status | (data1 << 8) | (data2 << 16))