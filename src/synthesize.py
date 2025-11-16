# src/synthesize.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
import numpy as np
import pyworld as pw
import soundfile as sf
from svs_utils import load_lab_file, time_to_frame
from pathlib import Path

SR = 22050
FRAME_PERIOD = 5.0
FFT_SIZE = 1024

# Carregar banco de fonemas
MODEL_PATH = Path("models/phoneme_stats.pkl")
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Modelo não encontrado! Execute 'build_db.py' primeiro.\n{MODEL_PATH}")

import pickle
with open(MODEL_PATH, "rb") as f:
    PHONEME_DB = pickle.load(f)

# Carregar espectros reais de SP/AP
if "__SILENCE_SP" in PHONEME_DB:
    SILENCE_SP = PHONEME_DB["__SILENCE_SP"]
    SILENCE_AP = PHONEME_DB["__SILENCE_AP"]
else:
    # Fallback (não deve acontecer se build_db.py rodou)
    SILENCE_SP = np.ones(FFT_SIZE // 2 + 1, dtype=np.float64) * 0.001
    SILENCE_AP = np.zeros(FFT_SIZE // 2 + 1, dtype=np.float64)

SILENCE_PHONEMES = {"SP", "AP", "sil", "pau", "br", "#", ""}

def synthesize_from_lab(lab_path, output_wav, default_pitch=261.63):
    lab = load_lab_file(lab_path)
    total_time = lab[-1][1] if lab else 1.0
    total_frames = time_to_frame(total_time, FRAME_PERIOD) + 10

    f0 = np.zeros(total_frames, dtype=np.float64)
    sp = np.zeros((total_frames, len(SILENCE_SP)), dtype=np.float64)
    ap = np.zeros((total_frames, len(SILENCE_AP)), dtype=np.float64)

    for start, end, ph in lab:
        f1 = time_to_frame(start, FRAME_PERIOD)
        f2 = time_to_frame(end, FRAME_PERIOD)
        f2 = min(f2, total_frames)
        if f1 >= total_frames:
            continue

        f0[f1:f2] = default_pitch

        if ph in SILENCE_PHONEMES:
            sp[f1:f2] = SILENCE_SP
            ap[f1:f2] = SILENCE_AP
        elif ph in PHONEME_DB:
            sp[f1:f2] = PHONEME_DB[ph]["sp_mean"]
            ap[f1:f2] = PHONEME_DB[ph]["ap_mean"]
        else:
            print(f"⚠️ Fonema desconhecido: '{ph}'. Usando silêncio real.")
            sp[f1:f2] = SILENCE_SP
            ap[f1:f2] = SILENCE_AP

    y = pw.synthesize(f0, sp, ap, SR, frame_period=FRAME_PERIOD)
    sf.write(output_wav, y, SR)
    print(f"🎵 Áudio salvo em: {output_wav}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python synthesize.py <lab> <output_wav> [pitch_Hz]")
        sys.exit(1)
    lab = sys.argv[1]
    out = sys.argv[2]
    pitch = float(sys.argv[3]) if len(sys.argv) > 3 else 261.63
    synthesize_from_lab(lab, out, pitch)