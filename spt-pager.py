# Loosely-derived from the pjsua sample code on the wiki
# Otherwise, copyright 2020 Nathan Whitehorn and placed
# in the public domain.
#
# Will use text-to-speech to play a message to a given SIP
# URI on a loop until either the recipient acknowledges the
# message or a timer expires. The return code is zero if
# the alarm was acknowledged and non-zero if the call failed
# or the alarm played to a voicemail box.

import sys
import pjsua as pj
import time
import tempfile
import os

# Logging callback
def log_cb(level, str, len):
    #print(str, end=' ')
    pass

acknowledged = False

# Audio file
wavfile = tempfile.mkstemp(suffix='.wav')[1]
print(wavfile)
os.popen('espeak -w %s' % wavfile, 'w').write(sys.argv[2] + '. Press any key to acknowledge this alarm.')

# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):
    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)
        self.wav_player_id = None

    # Notification when call's media state has changed.
    def on_media_state(self):
        global lib
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Connect the call to sound device
            if self.wav_player_id is None:
                self.wav_player_id=pj.Lib.instance().create_player(wavfile,loop=True)
            call_slot = self.call.info().conf_slot
            lib.conf_connect(pj.Lib.instance().player_get_slot(self.wav_player_id), call_slot)
            print("Call connected")

    def on_dtmf_digit(self, digits):
        global acknowledged
        print('Got acknowledgment')
        acknowledged = True
        self.call.hangup()

# Check command line argument
if len(sys.argv) != 3:
    print("Usage: alert.py <dst-URI> <message>")
    print("dst-URI is of the form sip:user@domain")
    os.unlink(wavfile)
    sys.exit(1)

try:
    # Create library instance
    lib = pj.Lib()

    # Init library with default config
    lib.init(log_cfg = pj.LogConfig(level=3, callback=log_cb))

    # Create UDP transport which listens to any available port
    transport = lib.create_transport(pj.TransportType.TCP)
    
    # Start the library
    lib.start()
    lib.set_null_snd_dev()

    # Create local/user-less account
    acc = lib.create_account_for_transport(transport)

    # Make call
    call = acc.make_call(sys.argv[1], MyCallCallback())

    # Wait for call to end one way or the other
    start_time = time.time()
    while call.is_valid():
        time.sleep(1)
        if time.time() - start_time > 20:
            # Give up if this has run more than 20 seconds with ack.
            # Probably got voicemail.
            break

    # We're done, shutdown the library
    lib.destroy()
    lib = None
    os.unlink(wavfile)

    if acknowledged:
        print("Alert acknowledged")
        sys.exit(0)
    else:
        print("Alert not acknowledged")
        sys.exit(0)

except pj.Error as e:
    print("Exception: " + str(e))
    lib.destroy()
    lib = None
    os.unlink(wavfile)
    sys.exit(1)

