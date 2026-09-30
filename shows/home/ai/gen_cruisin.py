#!/usr/bin/env python3
"""Generate shows/home/Cruisin.xsq from the song analysis produced by analyze_song.py.

usage: python3 gen_cruisin.py analysis.json out.xsq
"""
import json, sys, random
from xml.sax.saxutils import escape

FRAME = 50
random.seed(7)

def snap(t):
    """seconds -> ms on the frame grid"""
    return int(round(t * 1000.0 / FRAME)) * FRAME

def snap_ms(t):
    """ms -> ms on the frame grid"""
    return int(round(t / FRAME)) * FRAME

# ---------------------------------------------------------------- palettes
XMAS   = ["#C80000", "#00A000", "#FFD700", "#FFF4D0"]
RG     = ["#D00000", "#00B000"]
WARM   = ["#FF2A00", "#FF8C00", "#FFD700", "#FFF4D0"]
COOL   = ["#0030C0", "#0090FF", "#A0E0FF", "#FFFFFF"]
GOLD   = ["#FFD700", "#FFF4D0"]
CANDY  = ["#FF0000", "#FFFFFF"]
WHITE  = ["#FFFFFF"]
WWHITE = ["#FFF0C0"]
ROYAL  = ["#5A00B0", "#FFD700", "#FF00A0"]
ICE    = ["#80D0FF", "#FFFFFF"]

def pal(colors, brightness=100, sparkle=0):
    s = []
    for i, c in enumerate(colors, 1):
        s.append(f"C_BUTTON_Palette{i}={c}")
        s.append(f"C_CHECKBOX_Palette{i}=1")
    s.append(f"C_SLIDER_Brightness={brightness}")
    if sparkle:
        s.append(f"C_SLIDER_SparkleFrequency={sparkle}")
    return ",".join(s)

# ---------------------------------------------------------------- effect builder
def E(name, t0, t1, settings=None, colors=XMAS, fi=0.0, fo=0.0, blend="Normal", mix=0,
      buf=None, xform=None, brightness=100, sparkle=0, tin="Fade", tout="Fade", blur=None):
    s = dict(settings or {})
    parts = []
    for k, v in s.items():
        if isinstance(v, bool):
            v = 1 if v else 0
        parts.append(f"E_{k}={v}")
    parts.append(f"T_CHOICE_LayerMethod={blend}")
    if mix:
        parts.append(f"T_SLIDER_EffectLayerMix={mix}")
    parts.append(f"T_TEXTCTRL_Fadein={fi:.2f}")
    parts.append(f"T_TEXTCTRL_Fadeout={fo:.2f}")
    parts.append(f"T_CHOICE_In_Transition_Type={tin}")
    parts.append(f"T_CHOICE_Out_Transition_Type={tout}")
    if buf:
        parts.append(f"B_CHOICE_BufferStyle={buf}")
    if xform:
        parts.append(f"B_CHOICE_BufferTransform={xform}")
    if blur:
        parts.append(f"B_SLIDER_Blur={blur}")
    return dict(name=name, t0=snap_ms(t0), t1=snap_ms(t1), settings=",".join(parts),
                palette=pal(colors, brightness, sparkle))

# ---------------------------------------------------------------- song analysis
A = json.load(open(sys.argv[1]))
DUR = snap(A["duration"])
beats = [snap(b) for b in A["beats"]]
energy = A["energy"]

def beat_at(t):
    """first beat >= t (ms)"""
    for b in beats:
        if b >= t:
            return b
    return beats[-1]

# section boundaries from the structural analysis, snapped to beats
raw = dict(intro=0, build=14.9, A=21.3, break1=83.3, B=102.1, break2=165.2, C=181.3, outro=227.8)
S = {k: (0 if v == 0 else beat_at(snap(v))) for k, v in raw.items()}
S["end"] = DUR

# bar phase: pick the beat phase that best lines up with section starts
def phase_score(p):
    sc = 0
    idx = {b: i for i, b in enumerate(beats)}
    for k in ("A", "B", "C", "break1", "break2"):
        i = idx.get(S[k], 0)
        sc += (i - p) % 4 == 0
    return sc
PH = max(range(4), key=phase_score)
bars = [b for i, b in enumerate(beats) if (i - PH) % 4 == 0]
phrases = [b for i, b in enumerate(beats) if (i - PH) % 16 == 0]

def bars_in(t0, t1):
    return [b for b in bars if t0 <= b < t1]

def chunks(t0, t1, nbars=4):
    """split [t0,t1) into consecutive nbars-bar blocks, snapped to bar lines"""
    bs = [t0] + [b for b in bars if t0 < b < t1]
    out = []
    i = 0
    while i < len(bs):
        a = bs[i]
        j = min(i + nbars, len(bs))
        b = bs[j] if j < len(bs) else t1
        out.append((a, b))
        i = j
    return out

# ---------------------------------------------------------------- elements
TREE = "Tree"
BAY = "Matrix - Front Bay"
UL = "Matrix - Upper Left"
UR = "Matrix - Upper Right"
ICI = "ICICLES GRP"
WIN = "windows border"
CANES = "canes"
OUT = "Strip - Front Porch Outline"
MODELS = [TREE, BAY, UL, UR, ICI, WIN, CANES, OUT]
LAYERS = {m: [[], [], []] for m in MODELS}   # 0 = top accents, 1 = main, 2 = background

def add(model, layer, eff):
    LAYERS[model][layer].append(eff)

def add_all(layer, fn):
    for m in MODELS:
        add(m, layer, fn(m))

# ---------------------------------------------------------------- vocabulary
def tree_high(v, t0, t1, cols):
    nb = max(1, len(bars_in(t0, t1)))
    v = v % 6
    if v == 0:
        return E("Bars", t0, t1, {"SLIDER_Bars_BarCount": 3, "TEXTCTRL_Bars_Cycles": f"{nb*2:.1f}",
                                  "CHOICE_Bars_Direction": "up", "CHECKBOX_Bars_3D": True}, cols, fi=0.3, fo=0.3)
    if v == 1:
        return E("Spirals", t0, t1, {"SLIDER_Spirals_Count": 3, "SLIDER_Spirals_Rotation": 30,
                                     "SLIDER_Spirals_Thickness": 60, "TEXTCTRL_Spirals_Movement": f"{nb*1.0:.1f}",
                                     "CHECKBOX_Spirals_3D": True}, cols[:2], fi=0.3, fo=0.3)
    if v == 2:
        return E("Meteors", t0, t1, {"CHOICE_Meteors_Type": "Palette", "CHOICE_Meteors_Effect": "Down",
                                     "SLIDER_Meteors_Count": 25, "SLIDER_Meteors_Length": 35,
                                     "SLIDER_Meteors_Speed": 18}, cols, fi=0.3, fo=0.5)
    if v == 3:
        return E("Fire", t0, t1, {"SLIDER_Fire_Height": 65, "CHECKBOX_Fire_GrowWithMusic": True,
                                  "TEXTCTRL_Fire_GrowthCycles": "0.0"}, WARM, fi=0.5, fo=0.5)
    if v == 4:
        return E("Butterfly", t0, t1, {"CHOICE_Butterfly_Colors": "Palette", "SLIDER_Butterfly_Style": 2,
                                       "SLIDER_Butterfly_Chunks": 3, "SLIDER_Butterfly_Skip": 2,
                                       "SLIDER_Butterfly_Speed": 25}, cols, fi=0.3, fo=0.3)
    return E("Color Wash", t0, t1, {"TEXTCTRL_ColorWash_Cycles": f"{nb*1.0:.1f}", "CHECKBOX_ColorWash_VFade": True,
                                    "CHECKBOX_ColorWash_CircularPalette": True}, cols, fi=0.3, fo=0.3, sparkle=40)

def tree_pulse(t0, t1):
    # beat-driven white jump on the top layer; Additive so it rides over the main effect (Max hides the layer below)
    return E("VU Meter", t0, t1, {"CHOICE_VUMeter_Type": "Timing Event Jump", "CHOICE_VUMeter_TimingTrack": "Beats",
                                  "SLIDER_VUMeter_Bars": 6}, WWHITE, blend="Additive", brightness=55)

def text_eff(text, t0, t1, cols, fi=0.3, fo=0.3, speed=14):
    if len(text) * 7 <= 60:
        return E("Text", t0, t1, {"TEXTCTRL_Text": text, "CHOICE_Text_Font": "7-7x9 Bold", "CHOICE_Text_Dir": "none",
                                  "CHECKBOX_TextToCenter": True}, cols, fi=fi, fo=fo)
    return E("Text", t0, t1, {"TEXTCTRL_Text": text, "CHOICE_Text_Font": "10-12x12 Bold", "CHOICE_Text_Dir": "left",
                              "TEXTCTRL_Text_Speed": speed}, cols, fi=fi, fo=fo)

def bay_high(v, t0, t1, cols):
    v = v % 6
    if v == 0:
        return [E("Text", t0, t1, {"TEXTCTRL_Text": "CRUISIN'", "CHOICE_Text_Font": "12-15x15 Bold",
                                   "CHOICE_Text_Dir": "left", "TEXTCTRL_Text_Speed": 14}, GOLD, fi=0.3, fo=0.3),
                E("Plasma", t0, t1, {"CHOICE_Plasma_Color": "Normal", "SLIDER_Plasma_Style": 2,
                                     "SLIDER_Plasma_Line_Density": 2, "SLIDER_Plasma_Speed": 12}, cols, fi=0.5, fo=0.5, brightness=45)]
    if v == 1:
        return [E("VU Meter", t0, t1, {"CHOICE_VUMeter_Type": "Spectrogram Peak", "SLIDER_VUMeter_Bars": 15,
                                       "SLIDER_VUMeter_Sensitivity": 75}, cols, fi=0.3, fo=0.3)]
    if v == 2:
        return [E("Shape", t0, t1, {"CHOICE_Shape_ObjectToDraw": "Circle", "SLIDER_Shape_Thickness": 3, "TEXTCTRL_Shape_Count": 3,
                                    "SLIDER_Shape_StartSize": 5, "SLIDER_Shape_Lifetime": 20, "SLIDER_Shape_Growth": 30,
                                    "CHECKBOX_Shape_FireTiming": True, "CHOICE_Shape_FireTimingTrack": "Beats"}, WHITE + cols, fi=0.3, fo=0.3),
                E("Plasma", t0, t1, {"CHOICE_Plasma_Color": "Normal", "SLIDER_Plasma_Style": 3, "SLIDER_Plasma_Line_Density": 2,
                                     "SLIDER_Plasma_Speed": 10}, cols, fi=0.5, fo=0.5, brightness=30)]
    if v == 3:
        return [E("Pinwheel", t0, t1, {"SLIDER_Pinwheel_Arms": 4, "SLIDER_Pinwheel_Speed": 14, "SLIDER_Pinwheel_Twist": 90,
                                       "SLIDER_Pinwheel_Thickness": 40}, cols, fi=0.3, fo=0.3)]
    if v == 4:
        nb = max(1, len(bars_in(t0, t1)))
        return [E("Bars", t0, t1, {"SLIDER_Bars_BarCount": 3, "TEXTCTRL_Bars_Cycles": f"{nb*1.0:.1f}", "CHOICE_Bars_Direction": "Left",
                                   "CHECKBOX_Bars_Gradient": True, "CHECKBOX_Bars_3D": True}, cols, fi=0.3, fo=0.3)]
    return [E("Text", t0, t1, {"TEXTCTRL_Text": "Vincent Antone", "CHOICE_Text_Font": "10-12x12 Bold",
                               "CHOICE_Text_Dir": "left", "TEXTCTRL_Text_Speed": 14}, WHITE, fi=0.3, fo=0.3),
            E("Color Wash", t0, t1, {"TEXTCTRL_ColorWash_Cycles": "3.0", "CHECKBOX_ColorWash_HFade": True,
                                     "CHECKBOX_ColorWash_CircularPalette": True}, cols, fi=0.5, fo=0.5, brightness=40)]

def upper_high(v, t0, t1, cols, right):
    v = v % 6
    xf = "Flip Horizontal" if right else None
    if v == 0:
        return E("Fire", t0, t1, {"SLIDER_Fire_Height": 60, "CHECKBOX_Fire_GrowWithMusic": True}, WARM, fi=0.5, fo=0.5)
    if v == 1:
        return E("Spirals", t0, t1, {"SLIDER_Spirals_Count": 2, "SLIDER_Spirals_Rotation": 25, "SLIDER_Spirals_Thickness": 60,
                                     "TEXTCTRL_Spirals_Movement": "6.0", "CHECKBOX_Spirals_3D": True}, cols, fi=0.3, fo=0.3, xform=xf)
    if v == 2:
        return E("Butterfly", t0, t1, {"CHOICE_Butterfly_Colors": "Palette", "SLIDER_Butterfly_Style": 3,
                                       "SLIDER_Butterfly_Chunks": 2, "SLIDER_Butterfly_Speed": 20}, cols, fi=0.3, fo=0.3, xform=xf)
    if v == 3:
        return E("VU Meter", t0, t1, {"CHOICE_VUMeter_Type": "Spectrogram Peak", "SLIDER_VUMeter_Bars": 11,
                                      "SLIDER_VUMeter_Sensitivity": 75}, cols, fi=0.3, fo=0.3, xform=xf)
    if v == 4:
        return E("Meteors", t0, t1, {"CHOICE_Meteors_Type": "Palette", "CHOICE_Meteors_Effect": "Down",
                                     "SLIDER_Meteors_Count": 20, "SLIDER_Meteors_Length": 40, "SLIDER_Meteors_Speed": 16,
                                     "CHECKBOX_Meteors_UseMusic": True}, cols, fi=0.3, fo=0.5)
    return E("Pinwheel", t0, t1, {"SLIDER_Pinwheel_Arms": 3, "SLIDER_Pinwheel_Speed": 12, "SLIDER_Pinwheel_Twist": 60,
                                  "SLIDER_Pinwheel_Thickness": 50, "CHOICE_Pinwheel_3D": "3D"}, cols, fi=0.3, fo=0.3, xform=xf)

def icicles_high(v, t0, t1, cols):
    nb = max(1, len(bars_in(t0, t1)))
    v = v % 6
    if v == 0:
        return E("Meteors", t0, t1, {"CHOICE_Meteors_Type": "Palette", "CHOICE_Meteors_Effect": "Icicles + bkg",
                                     "SLIDER_Meteors_Count": 30, "SLIDER_Meteors_Length": 40, "SLIDER_Meteors_Speed": 14,
                                     "CHECKBOX_Meteors_UseMusic": True}, cols, fi=0.3, fo=0.5)
    if v == 1:
        return E("SingleStrand", t0, t1, {"CHOICE_SingleStrand_Colors": "Palette", "SLIDER_Number_Chases": 6,
                                          "SLIDER_Color_Mix1": 25, "TEXTCTRL_Chase_Rotations": f"{nb*1.0:.1f}",
                                          "CHOICE_Chase_Type1": "Dual Chase", "CHOICE_Fade_Type": "Head and Tail"},
                 cols, fi=0.3, fo=0.3, buf="Single Line")
    if v == 2:
        return E("VU Meter", t0, t1, {"CHOICE_VUMeter_Type": "Timing Event Sweep", "CHOICE_VUMeter_TimingTrack": "Beats",
                                      "SLIDER_VUMeter_Bars": 16}, cols, fi=0.3, fo=0.3, buf="Single Line")
    if v == 3:
        return E("Marquee", t0, t1, {"SLIDER_Marquee_Band_Size": 6, "SLIDER_Marquee_Skip_Size": 6, "SLIDER_Marquee_Speed": 8,
                                     "SLIDER_Marquee_Thickness": 100}, cols, fi=0.3, fo=0.3, buf="Single Line")
    if v == 4:
        return E("Bars", t0, t1, {"SLIDER_Bars_BarCount": 4, "TEXTCTRL_Bars_Cycles": f"{nb*2:.1f}",
                                  "CHOICE_Bars_Direction": "Left", "CHECKBOX_Bars_Gradient": True}, cols, fi=0.3, fo=0.3)
    return E("Color Wash", t0, t1, {"TEXTCTRL_ColorWash_Cycles": f"{nb*1.0:.1f}", "CHECKBOX_ColorWash_HFade": True,
                                    "CHECKBOX_ColorWash_CircularPalette": True}, cols, fi=0.3, fo=0.3, sparkle=60)

def icicles_pulse(t0, t1):
    return E("VU Meter", t0, t1, {"CHOICE_VUMeter_Type": "Timing Event Pulse", "CHOICE_VUMeter_TimingTrack": "Bars"},
             WHITE, blend="Additive", brightness=35)

def windows_high(v, t0, t1, cols):
    nb = max(1, len(bars_in(t0, t1)))
    v = v % 5
    if v == 0:
        return E("SingleStrand", t0, t1, {"CHOICE_SingleStrand_Colors": "Palette", "SLIDER_Number_Chases": 3,
                                          "SLIDER_Color_Mix1": 30, "TEXTCTRL_Chase_Rotations": f"{nb*1.0:.1f}",
                                          "CHOICE_Chase_Type1": "Left-Right", "CHOICE_Fade_Type": "From Tail"},
                 cols, fi=0.3, fo=0.3, buf="Per Model Single Line")
    if v == 1:
        return E("Marquee", t0, t1, {"SLIDER_Marquee_Band_Size": 4, "SLIDER_Marquee_Skip_Size": 4, "SLIDER_Marquee_Speed": 6,
                                     "SLIDER_Marquee_Thickness": 100}, cols, fi=0.3, fo=0.3, buf="Per Model Single Line")
    if v == 2:
        return E("VU Meter", t0, t1, {"CHOICE_VUMeter_Type": "Timing Event Pulse Color", "CHOICE_VUMeter_TimingTrack": "Beats"},
                 cols, fi=0.3, fo=0.3, buf="Per Model Default")
    if v == 3:
        return E("Bars", t0, t1, {"SLIDER_Bars_BarCount": 2, "TEXTCTRL_Bars_Cycles": f"{nb*1.0:.1f}",
                                  "CHOICE_Bars_Direction": "up", "CHECKBOX_Bars_Gradient": True}, cols, fi=0.3, fo=0.3,
                 buf="Per Model Default")
    return E("Color Wash", t0, t1, {"TEXTCTRL_ColorWash_Cycles": f"{nb*0.5:.1f}"}, cols, fi=0.3, fo=0.3, sparkle=40)

def canes_high(v, t0, t1, cols):
    nb = max(1, len(bars_in(t0, t1)))
    v = v % 4
    if v == 0:
        return E("Marquee", t0, t1, {"SLIDER_Marquee_Band_Size": 3, "SLIDER_Marquee_Skip_Size": 3, "SLIDER_Marquee_Speed": 8,
                                     "SLIDER_Marquee_Thickness": 100}, CANDY, fi=0.3, fo=0.3, buf="Per Model Single Line")
    if v == 1:
        return E("VU Meter", t0, t1, {"CHOICE_VUMeter_Type": "Timing Event Pulse Color", "CHOICE_VUMeter_TimingTrack": "Beats"},
                 cols, fi=0.3, fo=0.3, buf="Per Model Default")
    if v == 2:
        return E("SingleStrand", t0, t1, {"CHOICE_SingleStrand_Colors": "Palette", "SLIDER_Number_Chases": 2,
                                          "SLIDER_Color_Mix1": 40, "TEXTCTRL_Chase_Rotations": f"{nb*2.0:.1f}",
                                          "CHOICE_Chase_Type1": "Bounce from Left", "CHOICE_Fade_Type": "From Tail"},
                 CANDY, fi=0.3, fo=0.3, buf="Per Model Single Line")
    return E("Bars", t0, t1, {"SLIDER_Bars_BarCount": 5, "TEXTCTRL_Bars_Cycles": f"{nb*2:.1f}", "CHOICE_Bars_Direction": "Left"},
             cols, fi=0.3, fo=0.3, buf="Single Line")

def outline_high(v, t0, t1, cols):
    nb = max(1, len(bars_in(t0, t1)))
    v = v % 4
    if v == 0:
        return E("SingleStrand", t0, t1, {"CHOICE_SingleStrand_Colors": "Palette", "SLIDER_Number_Chases": 5,
                                          "SLIDER_Color_Mix1": 20, "TEXTCTRL_Chase_Rotations": f"{nb*1.0:.1f}",
                                          "CHOICE_Chase_Type1": "Dual Chase", "CHOICE_Fade_Type": "Head and Tail"}, cols, fi=0.3, fo=0.3)
    if v == 1:
        return E("VU Meter", t0, t1, {"CHOICE_VUMeter_Type": "Timing Event Sweep 2", "CHOICE_VUMeter_TimingTrack": "Beats",
                                      "SLIDER_VUMeter_Bars": 12}, cols, fi=0.3, fo=0.3)
    if v == 2:
        return E("Marquee", t0, t1, {"SLIDER_Marquee_Band_Size": 5, "SLIDER_Marquee_Skip_Size": 5, "SLIDER_Marquee_Speed": 10,
                                     "SLIDER_Marquee_Thickness": 100}, cols, fi=0.3, fo=0.3)
    return E("Bars", t0, t1, {"SLIDER_Bars_BarCount": 6, "TEXTCTRL_Bars_Cycles": f"{nb*2:.1f}", "CHOICE_Bars_Direction": "Left",
                              "CHECKBOX_Bars_Gradient": True}, cols, fi=0.3, fo=0.3)

# ---------------------------------------------------------------- section fillers
def flash(t, dur=150, fade=0.45):
    for m in MODELS:
        add(m, 0, E("On", t, t + dur + int(fade * 1000), {}, WHITE, fo=fade, tout="Fade"))

def high_section(t0, t1, palettes, voffset=0):
    blocks = chunks(t0, t1, 4)
    for i, (a, b) in enumerate(blocks):
        v = i + voffset
        cols = palettes[i % len(palettes)]
        add(TREE, 1, tree_high(v, a, b, cols))
        if v % 6 in (0, 1, 4, 5):
            add(TREE, 0, tree_pulse(a, b))
        for i, e in enumerate(bay_high(v + 2, a, b, cols)):
            add(BAY, 1 + i, e)
        add(UL, 1, upper_high(v + 1, a, b, cols, False))
        add(UR, 1, upper_high(v + 1, a, b, cols, True))
        add(ICI, 1, icicles_high(v, a, b, cols))
        if v % 6 in (0, 3, 5):
            add(ICI, 0, icicles_pulse(a, b))
        add(WIN, 1, windows_high(v, a, b, cols))
        add(CANES, 1, canes_high(v, a, b, cols))
        add(OUT, 1, outline_high(v, a, b, cols))

def low_section(t0, t1, cols, text):
    mid = (t0 + t1) // 2
    add(TREE, 1, E("Spirals", t0, t1, {"SLIDER_Spirals_Count": 2, "SLIDER_Spirals_Rotation": 15, "SLIDER_Spirals_Thickness": 70,
                                        "TEXTCTRL_Spirals_Movement": "1.5", "CHECKBOX_Spirals_Blend": True},
                   cols, fi=1.5, fo=1.0, brightness=55))
    add(TREE, 0, E("Twinkle", t0, t1, {"SLIDER_Twinkle_Count": 4, "SLIDER_Twinkle_Steps": 40}, WHITE, blend="Additive", brightness=50, fi=1.5, fo=1.0))
    add(BAY, 1, text_eff(text[0], t0, mid, ICE, fi=0.5, fo=0.5))
    add(BAY, 1, text_eff(text[1], mid, t1, ICE, fi=0.5, fo=0.5))
    add(BAY, 2, E("Snowflakes", t0, t1, {"SLIDER_Snowflakes_Count": 8, "SLIDER_Snowflakes_Type": 3, "SLIDER_Snowflakes_Speed": 6,
                                          "CHOICE_Falling": "Falling"}, ICE, fi=1.0, fo=1.0, brightness=50))
    for m in (UL, UR):
        add(m, 1, E("Snowflakes", t0, t1, {"SLIDER_Snowflakes_Count": 6, "SLIDER_Snowflakes_Type": 3, "SLIDER_Snowflakes_Speed": 6,
                                            "CHOICE_Falling": "Falling"}, ICE, fi=1.0, fo=1.0))
    add(ICI, 1, E("Meteors", t0, t1, {"CHOICE_Meteors_Type": "Palette", "CHOICE_Meteors_Effect": "Icicles", "SLIDER_Meteors_Count": 12,
                                       "SLIDER_Meteors_Length": 50, "SLIDER_Meteors_Speed": 5}, ICE, fi=1.5, fo=1.0))
    add(WIN, 1, E("Color Wash", t0, t1, {"TEXTCTRL_ColorWash_Cycles": "2.0", "CHECKBOX_ColorWash_VFade": True}, cols, fi=1.5, fo=1.0,
                  brightness=60, buf="Per Model Default"))
    add(CANES, 1, E("Twinkle", t0, t1, {"SLIDER_Twinkle_Count": 6, "SLIDER_Twinkle_Steps": 40}, WHITE, fi=1.5, fo=1.0, brightness=70))
    add(OUT, 1, E("SingleStrand", t0, t1, {"CHOICE_SingleStrand_Colors": "Palette", "SLIDER_Number_Chases": 2, "SLIDER_Color_Mix1": 30,
                                            "TEXTCTRL_Chase_Rotations": "3.0", "CHOICE_Chase_Type1": "Bounce from Middle",
                                            "CHOICE_Fade_Type": "Head and Tail"}, cols, fi=1.5, fo=1.0))

# ---------------------------------------------------------------- build the show
t_intro, t_build, tA, tB1, tB, tB2, tC, tOut, tEnd = (S[k] for k in ("intro", "build", "A", "break1", "B", "break2", "C", "outro", "end"))

# intro: soft warm twinkle everywhere, title on the bay
add(TREE, 1, E("Twinkle", t_intro, t_build, {"SLIDER_Twinkle_Count": 3, "SLIDER_Twinkle_Steps": 50}, WWHITE, fi=3.0, fo=0.5, brightness=70))
add(BAY, 1, text_eff("CRUISIN'", t_intro + 1000, t_build, GOLD, fi=2.0, fo=1.0))
for m in (UL, UR):
    add(m, 1, E("Twinkle", t_intro, t_build, {"SLIDER_Twinkle_Count": 4, "SLIDER_Twinkle_Steps": 50}, WWHITE, fi=3.0, fo=0.5, brightness=60))
add(ICI, 1, E("Twinkle", t_intro, t_build, {"SLIDER_Twinkle_Count": 3, "SLIDER_Twinkle_Steps": 50}, ICE, fi=3.0, fo=0.5, brightness=70))
add(WIN, 1, E("On", t_intro, t_build, {"TEXTCTRL_Eff_On_Start": 0, "TEXTCTRL_Eff_On_End": 100}, WWHITE, brightness=35, fo=0.5))
add(OUT, 1, E("Twinkle", t_intro, t_build, {"SLIDER_Twinkle_Count": 3, "SLIDER_Twinkle_Steps": 50}, GOLD, fi=3.0, fo=0.5, brightness=60))

# build: things start moving, rising toward the first drop
nbb = max(1, len(bars_in(t_build, tA)))
add(TREE, 1, E("Meteors", t_build, tA, {"CHOICE_Meteors_Type": "Palette", "CHOICE_Meteors_Effect": "Up", "SLIDER_Meteors_Count": 15,
                                         "SLIDER_Meteors_Length": 40, "SLIDER_Meteors_Speed": 20}, WARM, fi=0.5))
add(BAY, 1, E("Curtain", t_build, tA, {"CHOICE_Curtain_Edge": "center", "CHOICE_Curtain_Effect": "open", "TEXTCTRL_Curtain_Speed": "1.0",
                                        "SLIDER_Curtain_Swag": 4}, WARM))
for m, r in ((UL, False), (UR, True)):
    add(m, 1, E("Curtain", t_build, tA, {"CHOICE_Curtain_Edge": "bottom", "CHOICE_Curtain_Effect": "open", "TEXTCTRL_Curtain_Speed": "1.0",
                                         "SLIDER_Curtain_Swag": 4}, WARM, xform="Flip Horizontal" if r else None))
add(ICI, 1, E("Marquee", t_build, tA, {"SLIDER_Marquee_Band_Size": 6, "SLIDER_Marquee_Skip_Size": 6, "SLIDER_Marquee_Speed": 14,
                                        "SLIDER_Marquee_Thickness": 100}, WARM, buf="Single Line"))
add(WIN, 1, E("Curtain", t_build, tA, {"CHOICE_Curtain_Edge": "center", "CHOICE_Curtain_Effect": "open", "TEXTCTRL_Curtain_Speed": "1.0"},
              WARM, buf="Per Model Default"))
add(CANES, 1, E("VU Meter", t_build, tA, {"CHOICE_VUMeter_Type": "Timing Event Pulse", "CHOICE_VUMeter_TimingTrack": "Beats"}, CANDY,
                buf="Per Model Single Line"))
add(OUT, 1, E("SingleStrand", t_build, tA, {"CHOICE_SingleStrand_Colors": "Palette", "SLIDER_Number_Chases": 4, "SLIDER_Color_Mix1": 20,
                                             "TEXTCTRL_Chase_Rotations": f"{nbb*2.0:.1f}", "CHOICE_Chase_Type1": "From Middle",
                                             "CHOICE_Fade_Type": "From Tail"}, GOLD))

# main groove blocks, each with its own palette rotation so the three choruses read differently
flash(tA)
high_section(tA, tB1, [XMAS, RG, WARM, ROYAL], voffset=0)
low_section(tB1, tB, COOL, ("Vincent Antone", "Cruisin'"))
flash(tB)
high_section(tB, tB2, [ROYAL, XMAS, GOLD + ["#C80000"], RG], voffset=3)
low_section(tB2, tC, COOL, ("Happy", "Holidays"))
flash(tC)
high_section(tC, tOut, [XMAS, WARM, ROYAL, RG], voffset=1)

# outro: sign-off and a long fade to black
add(BAY, 1, text_eff("Merry Christmas", tOut, tEnd, GOLD, fi=0.5, fo=2.0))
for m in MODELS:
    if m == BAY:
        continue
    add(m, 1, E("Color Wash", tOut, tEnd, {"TEXTCTRL_ColorWash_Cycles": "1.0"}, RG if m != ICI else ICE, fi=0.5, fo=4.0, brightness=70, sparkle=30))

# ---------------------------------------------------------------- timing tracks
def contiguous(marks, end):
    out = []
    for i, m in enumerate(marks):
        e = marks[i + 1] if i + 1 < len(marks) else end
        if e > m:
            out.append((m, e, ""))
    return out

TIMINGS = {
    "Beats": contiguous(beats, DUR),
    "Bars": contiguous(bars, DUR),
    "Phrases": contiguous(phrases, DUR),
    "Sections": [(t_intro, t_build, "intro"), (t_build, tA, "build"), (tA, tB1, "groove 1"), (tB1, tB, "breakdown"),
                 (tB, tB2, "groove 2"), (tB2, tC, "breakdown 2"), (tC, tOut, "groove 3"), (tOut, tEnd, "outro")],
}

# ---------------------------------------------------------------- write the .xsq
effect_db, effect_ref = [], {}
pal_db, pal_ref = [], {}

def ref(db, index, s):
    if s not in index:
        index[s] = len(db)
        db.append(s)
    return index[s]

def effect_xml(e):
    r = ref(effect_db, effect_ref, e["settings"])
    p = ref(pal_db, pal_ref, e["palette"])
    return f'        <Effect ref="{r}" name="{escape(e["name"])}" startTime="{e["t0"]}" endTime="{e["t1"]}" palette="{p}"/>'

elements_xml = []
display_xml = []
for name, tl in TIMINGS.items():
    display_xml.append(f'    <Element collapsed="0" type="timing" name="{escape(name)}" visible="1" active="{1 if name == "Beats" else 0}" views=""/>')
    rows = "\n".join(f'        <Effect label="{escape(l)}" startTime="{a}" endTime="{b}"/>' for a, b, l in tl)
    elements_xml.append(f'    <Element type="timing" name="{escape(name)}">\n      <EffectLayer>\n{rows}\n      </EffectLayer>\n    </Element>')

for m in MODELS:
    display_xml.append(f'    <Element collapsed="0" type="model" name="{escape(m)}" visible="1"/>')
    layers = []
    for lay in LAYERS[m]:
        lay.sort(key=lambda e: e["t0"])
        # drop overlaps inside one layer (keep the earlier one)
        clean, last = [], -1
        for e in lay:
            if e["t0"] >= last and e["t1"] > e["t0"]:
                clean.append(e); last = e["t1"]
        layers.append("      <EffectLayer>\n" + "\n".join(effect_xml(e) for e in clean) + "\n      </EffectLayer>")
    elements_xml.append(f'    <Element type="model" name="{escape(m)}">\n' + "\n".join(layers) + "\n    </Element>")

doc = f'''<?xml version="1.0" encoding="UTF-8"?>
<xsequence BaseChannel="0" ChanCtrlBasic="0" ChanCtrlColor="0" FixedPointTiming="1" ModelBlending="true">
  <head>
    <version>2026.17</version>
    <author>Mark Gruenke</author>
    <author-email></author-email>
    <author-website></author-website>
    <song>Cruisin'</song>
    <artist>Vincent Antone</artist>
    <album></album>
    <MusicURL></MusicURL>
    <comment>Generated by shows/home/ai/gen_cruisin.py</comment>
    <sequenceTiming>{FRAME} ms</sequenceTiming>
    <sequenceType>Media</sequenceType>
    <mediaFile>006 - Vincent Antone - Cruisin'.mp3</mediaFile>
    <sequenceDuration>{DUR/1000:.3f}</sequenceDuration>
    <imageDir></imageDir>
  </head>
  <ColorPalettes>
{chr(10).join(f"    <ColorPalette>{escape(p)}</ColorPalette>" for p in pal_db)}
  </ColorPalettes>
  <EffectDB>
{chr(10).join(f"    <Effect>{escape(s)}</Effect>" for s in effect_db)}
  </EffectDB>
  <DataLayers/>
  <DisplayElements>
{chr(10).join(display_xml)}
  </DisplayElements>
  <ElementEffects>
{chr(10).join(elements_xml)}
  </ElementEffects>
  <lastView>Master View</lastView>
  <TimingTags/>
</xsequence>
'''
open(sys.argv[2], "w").write(doc)
n = sum(len(l) for m in MODELS for l in LAYERS[m])
print(f"wrote {sys.argv[2]}: {n} effects, {len(effect_db)} unique settings, {len(pal_db)} palettes, bar phase {PH}")
print("sections(ms):", {k: S[k] for k in S})
