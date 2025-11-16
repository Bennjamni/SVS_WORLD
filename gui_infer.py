# gui_infer.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
MODEL_PATH = PROJECT_ROOT / "models" / "phoneme_stats.pkl"
OUTPUT_DIR = PROJECT_ROOT / "examples"
OUTPUT_DIR.mkdir(exist_ok=True)

# Verificar se modelo existe
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Modelo não encontrado! Execute primeiro a interface principal e construa o modelo.\n{MODEL_PATH}")

# Carregar banco fonêmico (mesmo do synthesize.py)
import pickle
with open(MODEL_PATH, "rb") as f:
    PHONEME_DB = pickle.load(f)

# Parâmetros WORLD
SR = 22050
FRAME_PERIOD = 5.0
FFT_SIZE = 1024
SILENCE_SP = np.ones(FFT_SIZE // 2 + 1, dtype=np.float64)
SILENCE_AP = np.zeros(FFT_SIZE // 2 + 1, dtype=np.float64)

def generate_lab_from_table(table_data):
    """Gera conteúdo .lab em microssegundos a partir da tabela"""
    lines = []
    time_us = 0
    for ph, dur_ms, pitch_hz in table_data:
        dur_us = int(dur_ms * 1000)
        end_us = time_us + dur_us
        lines.append(f"{time_us} {end_us} {ph}")
        time_us = end_us
    return "\n".join(lines)

def synthesize_from_table(table_data, output_wav):
    """Sintetiza diretamente a partir da lista de (fonema, duração_ms, pitch_hz)"""
    # Calcular duração total em segundos
    total_ms = sum(dur for _, dur, _ in table_data)
    total_sec = total_ms / 1000.0
    total_frames = int(total_sec * 1000 / FRAME_PERIOD) + 10

    f0 = np.zeros(total_frames, dtype=np.float64)
    sp = np.zeros((total_frames, FFT_SIZE // 2 + 1), dtype=np.float64)
    ap = np.zeros((total_frames, FFT_SIZE // 2 + 1), dtype=np.float64)

    time_ms = 0
    for ph, dur_ms, pitch_hz in table_data:
        start_frame = int((time_ms / 1000.0) * 1000 / FRAME_PERIOD)
        end_frame = int(((time_ms + dur_ms) / 1000.0) * 1000 / FRAME_PERIOD)
        end_frame = min(end_frame, total_frames)

        if start_frame < total_frames:
            f0[start_frame:end_frame] = pitch_hz
            if ph in ("SP", "AP", ""):
                sp[start_frame:end_frame] = SILENCE_SP
                ap[start_frame:end_frame] = SILENCE_AP
            elif ph in PHONEME_DB:
                sp[start_frame:end_frame] = PHONEME_DB[ph]["sp_mean"]
                ap[start_frame:end_frame] = PHONEME_DB[ph]["ap_mean"]
            else:
                print(f"⚠️ Fonema desconhecido: {ph}")
                sp[start_frame:end_frame] = SILENCE_SP
                ap[start_frame:end_frame] = SILENCE_AP

        time_ms += dur_ms

    # Síntese com WORLD
    import pyworld as pw
    import soundfile as sf
    y = pw.synthesize(f0, sp, ap, SR, frame_period=FRAME_PERIOD)
    sf.write(output_wav, y, SR)

class InferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SVS-WORLD – Inferência (Síntese de Canto)")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Lista de entradas
        self.entries = []

        # Frame da tabela
        table_frame = tk.Frame(root)
        table_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        tk.Label(table_frame, text="Fonema / Duração (ms) / Pitch (Hz)", font=("Arial", 10, "bold")).pack(anchor="w")

        # Cabeçalhos
        header = tk.Frame(table_frame)
        header.pack(fill=tk.X, pady=(0, 5))
        tk.Label(header, text="Fonema", width=12).pack(side=tk.LEFT)
        tk.Label(header, text="Duração (ms)", width=12).pack(side=tk.LEFT)
        tk.Label(header, text="Pitch (Hz)", width=12).pack(side=tk.LEFT)

        # Área rolável para entradas
        canvas = tk.Canvas(table_frame)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botões de controle
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="➕ Adicionar Linha", command=self.add_row, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Limpar Tudo", command=self.clear_all, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🎤 Sintetizar", command=self.synthesize, width=15, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="💾 Salvar .lab", command=self.save_lab, width=15).pack(side=tk.LEFT, padx=5)

        # Adicionar linha inicial
        self.add_row()
        self.add_row()
        self.add_row()

    def add_row(self):
        frame = tk.Frame(self.scrollable_frame)
        frame.pack(fill=tk.X, pady=2)

        ph_var = tk.StringVar(value="a")
        dur_var = tk.StringVar(value="500")
        pitch_var = tk.StringVar(value="261.63")

        ph_entry = tk.Entry(frame, textvariable=ph_var, width=12)
        dur_entry = tk.Entry(frame, textvariable=dur_var, width=12)
        pitch_entry = tk.Entry(frame, textvariable=pitch_var, width=12)

        ph_entry.pack(side=tk.LEFT, padx=2)
        dur_entry.pack(side=tk.LEFT, padx=2)
        pitch_entry.pack(side=tk.LEFT, padx=2)

        self.entries.append((ph_var, dur_var, pitch_var))

    def clear_all(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.entries.clear()
        self.add_row()

    def get_table_data(self):
        data = []
        for ph_var, dur_var, pitch_var in self.entries:
            ph = ph_var.get().strip()
            if not ph:
                continue
            try:
                dur = float(dur_var.get())
                pitch = float(pitch_var.get()) if ph not in ("SP", "AP") else 0.0
                data.append((ph, dur, pitch))
            except ValueError:
                messagebox.showerror("Erro", f"Valores inválidos na linha: {ph}")
                return None
        return data

    def synthesize(self):
        data = self.get_table_data()
        if data is None:
            return
        if not data:
            messagebox.showwarning("Atenção", "Nenhuma entrada válida.")
            return

        output_wav = OUTPUT_DIR / "inferencia_resultado.wav"
        try:
            synthesize_from_table(data, output_wav)
            messagebox.showinfo("Sucesso", f"Áudio gerado!\n{output_wav}")
            if os.name == 'nt':
                os.startfile(output_wav)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na síntese:\n{e}")

    def save_lab(self):
        data = self.get_table_data()
        if data is None:
            return
        if not data:
            messagebox.showwarning("Atenção", "Nenhuma entrada.")
            return

        lab_content = generate_lab_from_table(data)
        filepath = filedialog.asksaveasfilename(
            defaultextension=".lab",
            filetypes=[("Arquivo LAB", "*.lab")],
            initialdir=OUTPUT_DIR
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(lab_content)
            messagebox.showinfo("Salvo", f"Arquivo .lab salvo:\n{filepath}")

if __name__ == "__main__":
    root = tk.Tk()
    app = InferGUI(root)
    root.mainloop()