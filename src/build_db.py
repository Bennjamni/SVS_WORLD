# src/build_db.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
import numpy as np
import pickle
from collections import defaultdict
from pathlib import Path
from svs_utils import load_lab_file, time_to_frame, align_phonemes_to_frames

FEATURES_DIR = Path("data/features")

def build_phoneme_db():
    stats = defaultdict(lambda: {"sp": [], "ap": []})
    all_sp = []
    all_ap = []
    all_ph = []

    # Coletar todos os dados primeiro
    for file in os.listdir(FEATURES_DIR):
        if not file.endswith("_ph.npy"):
            continue
        base = file.replace("_ph.npy", "")
        ph_seq = np.load(os.path.join(FEATURES_DIR, file), allow_pickle=True)
        sp = np.load(os.path.join(FEATURES_DIR, base + "_sp.npy"))
        ap = np.load(os.path.join(FEATURES_DIR, base + "_ap.npy"))

        if len(ph_seq) != len(sp):
            print(f"⚠️ Tamanho inconsistente em {base}. Ignorando.")
            continue

        # Acumular para fonemas normais
        for i, ph in enumerate(ph_seq):
            if ph and ph not in {"SP", "AP"} and i < len(sp):
                stats[ph]["sp"].append(sp[i])
                stats[ph]["ap"].append(ap[i])

        # Acumular tudo para SP/AP
        all_sp.extend(sp)
        all_ap.extend(ap)
        all_ph.extend(ph_seq)

    # Construir banco de fonemas normais
    db = {}
    for ph, data in stats.items():
        db[ph] = {
            "sp_mean": np.mean(data["sp"], axis=0),
            "ap_mean": np.mean(data["ap"], axis=0)
        }
        print(f"Fonema '{ph}': {len(data['sp'])} exemplos")

    # Extrair SP/AP reais
    silence_sp = []
    silence_ap = []
    for i, ph in enumerate(all_ph):
        if ph in {"SP", "AP"} and i < len(all_sp):
            silence_sp.append(all_sp[i])
            silence_ap.append(all_ap[i])

    if silence_sp:
        db["__SILENCE_SP"] = np.mean(silence_sp, axis=0)
        db["__SILENCE_AP"] = np.mean(silence_ap, axis=0)
        print(f"✅ Silêncio/respiração: {len(silence_sp)} frames usados.")
    else:
        # Fallback suave (quase silêncio)
        if all_sp:
            dummy_sp = np.ones_like(all_sp[0]) * 0.001
            dummy_ap = np.zeros_like(all_ap[0])
        else:
            dummy_sp = np.ones(513) * 0.001  # WORLD usa 513 por padrão (1024 FFT)
            dummy_ap = np.zeros(513)
        db["__SILENCE_SP"] = dummy_sp
        db["__SILENCE_AP"] = dummy_ap
        print("⚠️ Nenhum SP/AP encontrado. Usando fallback suave.")

    # Salvar modelo
    os.makedirs("models", exist_ok=True)
    model_path = Path("models/phoneme_stats.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(db, f)
    print(f"✅ Banco de fonemas salvo em {model_path}")

if __name__ == "__main__":
    build_phoneme_db()