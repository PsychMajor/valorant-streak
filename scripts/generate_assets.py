"""Original Streak Lab sounds and vector emblems. No samples or downloaded art.

Uses additive/FM synthesis and simple geometric drawings. Output is licensed
under AGPL-3.0-or-later with the rest of this project. Python standard library only.
"""
import array
import hashlib
import json
import math
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100
PACKS = [
    ('pulse', 'Pulse', '#68e8df', 220, 'pulse'),
    ('prism', 'Prism', '#c4a2ff', 330, 'bell'),
    ('orbit', 'Orbit', '#81b9ff', 196, 'space'),
    ('ember', 'Ember', '#ffb078', 165, 'warm'),
    ('circuit', 'Circuit', '#c6ef75', 262, 'chip'),
    ('bloom', 'Bloom', '#f5a6d2', 294, 'soft'),
]
SHAPES = {
    'pulse': '<path d="M24 60h24l10-24 18 48 17-42 11 18h32"/>',
    'prism': '<path d="m80 22 37 38-37 38-37-38z M80 22v76 M43 60h74"/>',
    'orbit': '<ellipse cx="80" cy="60" rx="50" ry="20" transform="rotate(-30 80 60)"/><circle cx="80" cy="60" r="16"/><circle cx="120" cy="37" r="5" fill="currentColor"/>',
    'ember': '<path d="M82 18c4 22 29 31 29 53a31 31 0 0 1-62 0c0-15 15-26 20-37 2 14 7 18 9 18 8-10 8-20 4-34z M81 63c-11 12-14 24 0 27 14-3 10-15 0-27z"/>',
    'circuit': '<path d="M57 37h46v46H57z M39 30v18h18 M121 30v18h-18 M39 90V72h18 M121 90V72h-18 M70 22v15 M90 22v15 M70 83v15 M90 83v15"/><circle cx="80" cy="60" r="10"/>',
    'bloom': ''.join(f'<ellipse cx="80" cy="43" rx="11" ry="22" transform="rotate({a} 80 60)"/>' for a in range(0,360,60))+'<circle cx="80" cy="60" r="8" fill="currentColor"/>',
}

def synth(kind, frequency, stage):
    duration = .48 + stage * .065 + (.28 if stage == 5 else 0)
    data = [0.] * int(duration * RATE)
    # Unique ascending interval progression, with a short triad at the final stage.
    tones = [(frequency * 2 ** ([0, 3, 7, 10, 15][stage-1] / 12), 0., 1.)]
    if stage == 5:
        tones += [(tones[0][0] * 1.25, .065, .33), (tones[0][0] * 1.5, .13, .25)]
    for freq, onset, gain in tones:
        for i in range(int(onset * RATE), len(data)):
            t = i / RATE - onset
            attack = min(1., t / .006)
            env = attack * math.exp(-t * (4.4 if stage < 5 else 3.4))
            phase = 2 * math.pi * freq * t
            if kind == 'bell':
                value = math.sin(phase) + .4 * math.sin(phase * 2.73) * math.exp(-6*t) + .15 * math.sin(phase * 4.1) * math.exp(-9*t)
            elif kind == 'pulse':
                value = math.sin(phase + 1.3 * math.exp(-12*t) * math.sin(phase*2)) + .23*math.sin(phase*.5)
            elif kind == 'space':
                value = math.sin(phase + .35*math.sin(2*math.pi*8*t)) + .35*math.sin(phase*1.003) + .2*math.sin(phase*2)
            elif kind == 'warm':
                value = math.sin(phase)+.32*math.sin(phase*2)+.14*math.sin(phase*3)
            elif kind == 'chip':
                value = sum(math.sin(phase*h)/h for h in (1,3,5,7))*.8
            else:
                value = math.sin(phase)+.18*math.sin(phase*2)*math.exp(-3*t)
            tail = min(1., (duration-i/RATE)/.06)
            data[i] += value * env * tail * gain
    peak = max(abs(v) for v in data) or 1
    pcm = array.array('h', (round(v / peak * 18000) for v in data))
    if sys.byteorder != 'little': pcm.byteswap()
    return pcm.tobytes()

def main():
    assets=ROOT/'addon/assets'; assets.mkdir(exist_ok=True)
    packs=[]
    for pid,name,color,frequency,kind in PACKS:
        banner=f'assets/{pid}.svg'
        (ROOT/'addon'/banner).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="120" viewBox="0 0 160 120"><g color="{color}" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none">{SHAPES[pid]}</g></svg>\n')
        sounds=[]
        for stage in range(1,6):
            filename=f'assets/{pid}_{stage}.wav'; path=ROOT/'addon'/filename
            with wave.open(str(path),'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
                w.writeframes(synth(kind,frequency,stage))
            sounds.append({'stage':stage,'file':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        packs.append(dict(id=pid,name=name,color=color,banner=banner,sounds=sounds))
    (ROOT/'addon/catalog.json').write_text(json.dumps({'license':'AGPL-3.0-or-later','provenance':'Original procedural synthesis and geometric SVG artwork; scripts/generate_assets.py','packs':packs},indent=2)+'\n')
    print('Generated 30 original WAV effects and six SVG emblems.')

if __name__=='__main__': main()
