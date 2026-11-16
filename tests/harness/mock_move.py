import json, io, zipfile, uuid, time, threading, struct, wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
def song(root, scale, tempo, presets):
    def tr(p, kind):
        inner = {"kind": kind, "name": "", "parameters": {}, "presetUri": None, "deviceData": {}}
        if kind == "drumRack": inner["chains"] = [{"devices":[{"kind":"drumCell","deviceData":{"sampleUri":"Samples/Kick%201.wav"},"presetUri":None}]}]
        return {"kind":"midi","name":"","color":3,"clipSlots":[{"hasStop":True,"clip":{"isPlaying":False,"name":"","color":3,"isEnabled":True,"timeSignature":{"upper":4,"lower":4},"region":{"start":0.0,"end":4.0,"loop":{"start":0.0,"end":4.0,"isEnabled":True}},"grooveId":1,"stepEditorScrollPosition":0.0,"notes":[{"noteNumber":36,"startTime":float(b),"duration":0.25,"velocity":100.0,"offVelocity":0.0} for b in range(4)],"envelopes":[]}}]+[{"hasStop":True,"clip":None} for _ in range(7)],
                "devices":[{"kind":"instrumentRack","name":"X","presetUri":p,"chains":[{"devices":[inner,{"kind":"reverb"}]}]}]}
    return {"tempo":tempo,"rootNote":root,"scale":scale,"timeSignature":{"upper":4,"lower":4},"scenes":[{}]*8,
            "tracks":[tr(p,k) for p,k in presets]}
def bundle(s):
    b = io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("Samples/Kick 1.wav", b"RIFF0000")
        z.writestr("Song.abl", json.dumps(s))
        z.writestr("BundleInfo.json", "{}")
    return b.getvalue()
P = [("ableton:/packs/abl-core-library/Track%20Presets/Templates/Drum%20Kit.json","drumRack"),
     ("ableton:/user-library/Track%20Presets/Ableton%20Stock%20Drift%20Presets/Bass/Skanker%20Bass.ablpreset","drift"),
     ("ableton:/user-library/Track%20Presets/Melodic%20Movement/Arp%20-%20Fading2%20%28Move%20Preset%29.ablpreset","drift"),
     ("ableton:/packs/abl-core-library/Track%20Presets/Templates/Sampler.json","melodicSampler")]
SETS = {}
import os, pathlib
ROOT = pathlib.Path("/tmp/fakesets"); 
def add(name, data):
    oid = str(uuid.uuid4()); SETS[oid] = {"name":name,"data":data,"mod":"2026-11-12T23:17:14Z"}
    d = ROOT/oid/name; d.mkdir(parents=True)
    (d/"Song.abl").write_bytes(zipfile.ZipFile(io.BytesIO(data)).read("Song.abl"))
    used = {int((x/".xattr_user.song-index").read_text()) for x in ROOT.iterdir() if (x/".xattr_user.song-index").exists()}
    free = next(i for i in range(32) if i not in used)
    (ROOT/oid/".xattr_user.song-index").write_text(str(free)); (ROOT/oid/".xattr_user.song-color").write_text(str(free*3%25+1))
    return oid
for n,(r,sc,t) in {"BGDN LV Set 78":(9,"Minor Pentatonic",140),"Set 90":(0,"Major",120),"House":(4,"Minor",124),"Set 99":(2,"Dorian",98),"Set 101":(7,"Major",128),"Set 104":(6,"Whole Tone",90)}.items():
    add(n, bundle(song(r,sc,t,P)))
AUTHED = set(); RENDERS = {}; STUCK = set(); DELETED = []
def wav():
    b = io.BytesIO(); w = wave.open(b,"wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(b"\0\0"*8000); w.close(); return b.getvalue()
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def j(self, o, c=200, hd=None):
        b = json.dumps(o).encode(); self.send_response(c); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b)))
        for k,v in (hd or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(b)
    def authed(self): return "tok=secret" in (self.headers.get("Cookie") or "")
    def any(self):
        p, m = self.path.split("?")[0], self.command
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n) if n else b""
        if p == "/api/v1/challenge": return self.j({})
        if p == "/api/v1/challenge-response":
            if json.loads(body).get("secret") == "123456": return self.j({}, hd={"Set-Cookie":"tok=secret; Path=/"})
            return self.j({"error":"bad"},401)
        if not self.authed(): return self.j({"error":"Unset credentials"},401)
        if p == "/api/v1/ssh": return self.j({"added": True})
        if p == "/api/v1/files/Recordings": return self.j({"paths":[{"path":"Set%2099%20Rec%201.wav","size":1000,"lastModifiedDateTime":"2026-09-11T12:24:29Z"},{"path":"Set%2099%20Rec%205%20-%2098%20bpm.wav","size":16044,"lastModifiedDateTime":"2026-10-11T12:24:29Z"},{"path":"Lofihouse%20Rec%201.wav","size":500,"lastModifiedDateTime":"2026-11-11T12:24:29Z"}]})
        if p.startswith("/api/v1/files/Recordings/"):
            d = wav(); self.send_response(200); self.send_header("Content-Type","audio/wav"); self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d); return
        if p == "/api/v1/data/Sets" and m == "GET":
            return self.j({"objects":[{"bucket":"Sets","objectId":k,"name":v["name"],"lastModifiedDateTime":v["mod"],"size":1} for k,v in SETS.items()]})
        if p == "/api/v1/data/Sets" and m == "POST":
            ct = self.headers["Content-Type"]; bnd = ct.split("boundary=")[1].encode()
            part = body.split(b"--"+bnd)[1]; head, data = part.split(b"\r\n\r\n",1); data = data.rsplit(b"\r\n",1)[0]
            fn = head.decode().split('filename="')[1].split('"')[0]
            zipfile.ZipFile(io.BytesIO(data)).testzip()
            add(fn.rsplit(".",1)[0], data); return self.j({"files":[{"path":fn,"error":None}]})
        if p.startswith("/api/v1/data/Sets/"):
            oid = p.rsplit("/",1)[1]
            if oid not in SETS: return self.j({},404)
            if m == "GET":
                d = SETS[oid]["data"]; self.send_response(200); self.send_header("Content-Type","application/octet-stream"); self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d); return
            if m == "PATCH": SETS[oid]["name"] = json.loads(body)["newName"]; return self.j({})
            if m == "DELETE":
                del SETS[oid]; import shutil; shutil.rmtree(ROOT/oid, ignore_errors=True); return self.j({})
        if p.startswith("/api/v1/render/") and m == "POST":
            rid = str(uuid.uuid4()); oid = p.rsplit("/",1)[1]
            if SETS.get(oid,{}).get("name") == "Set 104": STUCK.add(rid)
            else: RENDERS[rid] = time.time()
            return self.j({"id":rid,"href":"/api/v1/render/"+rid+"/file"})
        if p.startswith("/api/v1/render/") and m == "DELETE":
            DELETED.append(p.rsplit("/",1)[1]); return self.j({})
        if p == "/api/v1/render":
            self.send_response(200); self.send_header("Content-Type","text/event-stream"); self.send_header("Connection","close"); self.end_headers()
            for prog in (0,40,80):
                for rid in RENDERS: self.wfile.write(("data: "+json.dumps({"id":rid,"status":"rendering","progress":prog})+"\n\n").encode())
                self.wfile.flush(); time.sleep(0.3)
            for rid in RENDERS: self.wfile.write(("data: "+json.dumps({"id":rid,"status":"finished"})+"\n\n").encode())
            self.wfile.flush(); time.sleep(40); self.close_connection = True; return
        if p == "/deleted": return self.j(DELETED)
        if p.endswith("/file") and p.split("/")[-2] in STUCK: return self.j({"error":"Not a valid render ID"},404)
        if p.endswith("/file"):
            d = wav(); self.send_response(200); self.send_header("Content-Type","audio/wav"); self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d); return
        self.j({},404)
    do_GET=do_POST=do_PATCH=do_DELETE=any
ThreadingHTTPServer(("127.0.0.1",8799),H).serve_forever()
