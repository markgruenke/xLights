# AI sequencing tools

- `analyze_song.py <audio> <out.json>` – beats, bars, energy and section boundaries (needs `pip install librosa soundfile`).
- `gen_cruisin.py <analysis.json> <out.xsq>` – builds the Cruisin' sequence from that analysis.

Copy `Cruisin.xsq` into the real show folder next to the MP3 and open it in xLights.
Timing tracks `Beats`, `Bars`, `Phrases` and `Sections` are included and drive the beat-reactive effects.

## Verifying a render without opening xLights

`xLights --headless -s <showdir> --outputdir <dir> <seq.xsq>` renders to `.fseq`, then
`fseq_report.py <file.fseq>` prints mean brightness per prop per 10 s so dark or dead
sections stand out before anyone watches it.
