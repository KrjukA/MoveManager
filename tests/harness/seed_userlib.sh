mkdir -p "/tmp/fakeul/Samples/Bounces" "/tmp/fakeul/Samples/Drums" "/tmp/fakeul/Track Presets/Drums" "/tmp/fakeul/Sets/aaaaaaaa-0000-0000-0000-000000000001/Seed Proj"
python3 - <<'P'
import json, struct, wave
def tone(path, sec=0.3):
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100); w.writeframes(b"\x00\x10" * int(44100 * sec))
for f in ["Bounces/Set 93 Bounce 4 - 100 bpm.wav", "Bounces/Set 93 Bounce 5 - 100 bpm.wav", "Drums/kick.wav", "Drums/old unused.wav"]:
    tone("/tmp/fakeul/Samples/" + f)
uri = "ableton:/user-library/Samples/Bounces/Set%2093%20Bounce%204%20-%20100%20bpm.wav"
kick = "ableton:/user-library/Samples/Drums/kick.wav"
song = {"tracks": [{"kind": "midi", "devices": [{"kind": "drumRack", "chains": [
    {"devices": [{"kind": "drumCell", "deviceData": {"sampleUri": uri}}], "drumZoneSettings": {"receivingNote": 36}},
    {"devices": [{"kind": "drumCell", "deviceData": {"sampleUri": kick}}], "drumZoneSettings": {"receivingNote": 37}}]}]}]}
open("/tmp/fakeul/Sets/aaaaaaaa-0000-0000-0000-000000000001/Seed Proj/Song.abl", "w").write(json.dumps(song, indent=2))
open("/tmp/fakeul/Track Presets/Drums/Kit.ablpreset", "w").write(json.dumps({"kind": "drumCell", "deviceData": {"sampleUri": kick}}))
P
# «компьютер» для правой панели
rm -rf /root/mmpc && mkdir -p /root/mmpc/Kits/Sub
python3 - <<'P2'
import wave
def tone(path, sec=0.3):
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100); w.writeframes(b"\x00\x10" * int(44100 * sec))
tone("/root/mmpc/Kits/snare.wav"); tone("/root/mmpc/Kits/Sub/hat.wav")
open("/root/mmpc/lead.ablpreset", "w").write("{}")
open("/root/mmpc/Kits/readme.txt", "w").write("x")
P2
