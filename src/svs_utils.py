import numpy as np

def load_lab_file(path):
    """Carrega .lab com tempos em unidades de 100ns (frequência de 10 MHz)"""
    segments = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 3:
                start_tick = int(parts[0])
                end_tick = int(parts[1])
                ph = parts[2]
                # Converter ticks (100ns) → segundos
                start_sec = start_tick / 10_000_000.0
                end_sec = end_tick / 10_000_000.0
                segments.append((start_sec, end_sec, ph))
    return segments

def time_to_frame(t_sec, frame_period_ms=5.0):
    return int(t_sec * 1000 / frame_period_ms)

def align_phonemes_to_frames(lab_segments, total_frames, frame_period_ms=5.0):
    phoneme_seq = [""] * total_frames
    for start, end, ph in lab_segments:
        f1 = time_to_frame(start, frame_period_ms)
        f2 = time_to_frame(end, frame_period_ms)
        for i in range(f1, min(f2, total_frames)):
            phoneme_seq[i] = ph
    return phoneme_seq