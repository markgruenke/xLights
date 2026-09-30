import librosa, numpy as np, json, sys
y, sr = librosa.load(sys.argv[1], sr=22050, mono=True)
dur = len(y)/sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time', trim=False)
tempo = float(np.atleast_1d(tempo)[0])
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time', backtrack=False)
# energy per 0.5s window
hop=512
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
t_rms = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
win=1.0
bins=int(dur/win)+1
energy=[float(rms[(t_rms>=i*win)&(t_rms<(i+1)*win)].mean()) if ((t_rms>=i*win)&(t_rms<(i+1)*win)).any() else 0 for i in range(bins)]
emax=max(energy); energy=[round(e/emax,3) for e in energy]
# structure segmentation
C = librosa.feature.chroma_cqt(y=y, sr=sr)
mf = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
feat = np.vstack([librosa.util.normalize(C), librosa.util.normalize(mf)])
bf = librosa.util.sync(feat, librosa.time_to_frames(beats, sr=sr), aggregate=np.median)
k=8
bounds = librosa.segment.agglomerative(bf, k)
bt = beats[np.clip(bounds,0,len(beats)-1)]
# spectral: bass vs treble energy per second
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
bass = S[freqs<150].sum(0); high = S[freqs>4000].sum(0)
def per_sec(a):
    o=[]
    for i in range(bins):
        m=(t_rms>=i*win)&(t_rms<(i+1)*win)
        o.append(float(a[m].mean()) if m.any() else 0)
    mx=max(o); return [round(v/mx,3) for v in o]
out=dict(duration=round(dur,3), tempo=round(tempo,2), beats=[round(b,3) for b in beats],
         onsets=[round(o,3) for o in onsets], energy=energy, bass=per_sec(bass), high=per_sec(high),
         segments=[round(float(b),3) for b in bt])
json.dump(out, open(sys.argv[2],'w'))
print("dur",round(dur,2),"tempo",round(tempo,2),"beats",len(beats),"onsets",len(onsets))
print("segments", [round(float(b),1) for b in bt])
print("energy/sec", ' '.join(f"{int(e*9)}" for e in energy))
