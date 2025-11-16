# src/analyze.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
import numpy as np
import librosa
import pyworld as pw
from svs_utils import load_lab_file, align_phonemes_to_frames
import matplotlib
matplotlib.use('Agg')  # Usa backend não-interativo
import matplotlib.pyplot as plt

# Configurações seguras para Windows
SR = 22050          # Taxa fixa (reduz uso de memória)
FRAME_PERIOD = 5.0  # ms
FFT_SIZE = 1024      # Reduzido para evitar "Fail to allocate bitmap"

def sanitize_audio(x):
    """Remove NaN, inf e normaliza volume para evitar picos"""
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    max_val = np.max(np.abs(x))
    if max_val > 0:
        x = x / max_val * 0.95  # Evita saturação
    return x

def analyze_wav(wav_path, lab_path, out_dir):
    try:
        # 1. Carregar áudio bruto
        print(f"🔊 Carregando: {os.path.basename(wav_path)}")
        x, orig_sr = librosa.load(wav_path, sr=None, mono=True)

        # 2. Forçar mono e resample para SR fixo
        if orig_sr != SR:
            print(f"  ↻ Convertendo de {orig_sr} Hz → {SR} Hz")
            x = librosa.resample(x, orig_sr=orig_sr, target_sr=SR)
        else:
            print(f"  ✔ Já em {SR} Hz")

        # 3. Sanitizar
        x = sanitize_audio(x)
        x = x.astype(np.float64)

        print(f"  📏 Duração: {len(x)/SR:.2f} s | Amostras: {len(x)}")

        # 4. Extração WORLD
        print("  🌍 Extraindo features com WORLD...")
        _f0, t = pw.dio(x, SR, frame_period=FRAME_PERIOD)
        f0 = pw.stonemask(x, _f0, t, SR)
        sp = pw.cheaptrick(x, f0, t, SR, fft_size=FFT_SIZE)
        ap = pw.d4c(x, f0, t, SR, fft_size=FFT_SIZE)

        # 5. Alinhar fonemas
        lab = load_lab_file(lab_path)
        total_frames = len(f0)
        phonemes = align_phonemes_to_frames(lab, total_frames, FRAME_PERIOD)

        # 6. Salvar
        name = os.path.splitext(os.path.basename(wav_path))[0]
        os.makedirs(out_dir, exist_ok=True)
        np.save(os.path.join(out_dir, f"{name}_f0.npy"), f0)
        np.save(os.path.join(out_dir, f"{name}_sp.npy"), sp)
        np.save(os.path.join(out_dir, f"{name}_ap.npy"), ap)
        np.save(os.path.join(out_dir, f"{name}_ph.npy"), np.array(phonemes))

        # 7. Gráfico de alinhamento
        time_axis = np.arange(len(f0)) * (FRAME_PERIOD / 1000.0)
        plt.figure(figsize=(12, 4))
        plt.plot(time_axis, f0, label="F0", linewidth=1)
        for start, end, ph in lab:
            plt.axvspan(start, end, alpha=0.1)
            plt.text((start + end)/2, plt.ylim()[1]*0.9, ph, ha='center', fontsize=9)
        plt.xlabel("Tempo (s)")
        plt.ylabel("F0 (Hz)")
        plt.title(f"Alinhamento: {name} ({len(x)/SR:.1f}s)")
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"{name}_alignment.png"), dpi=120)
        plt.close()

        print(f"✅ Sucesso: {name}")

    except Exception as e:
        print(f"❌ FALHA CRÍTICA em {wav_path}:")
        print(f"   Erro: {e}")
        print("   Possíveis causas:")
        print("   - Áudio corrompido")
        print("   - Memória insuficiente (feche outros programas)")
        print("   - Problema no pyworld (tente reinstalar)")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Uso: python analyze.py <wav> <lab> <out_dir>")
        sys.exit(1)
    analyze_wav(sys.argv[1], sys.argv[2], sys.argv[3])