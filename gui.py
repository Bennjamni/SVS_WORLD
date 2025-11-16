# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import threading
from pathlib import Path
import shutil

# --- Configurações ---
PROJECT_ROOT = Path(__file__).parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
LAB_DIR = PROJECT_ROOT / "data" / "lab"
FEAT_DIR = PROJECT_ROOT / "data" / "features"
MODEL_DIR = PROJECT_ROOT / "models"

RAW_DIR.mkdir(parents=True, exist_ok=True)
LAB_DIR.mkdir(parents=True, exist_ok=True)
FEAT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def normalize_phoneme(ph):
    """Normaliza fonemas de silêncio/respiração para SP/AP"""
    ph = ph.strip()
    SILENCE_VARIANTS = {"sil", "pau", "silence", "#", "", "sp", "SIL", "PAU", "p", "S"}
    BREATH_VARIANTS = {"br", "bre", "breath", "AP", "ap", "BR", "BRE", "b"}
    
    if ph in SILENCE_VARIANTS:
        return "SP"
    elif ph in BREATH_VARIANTS:
        return "AP"
    else:
        return ph
    
class SVSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SVS-WORLD – Síntese de Voz Cantada (Multi-arquivo)")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Armazenamento dos pares carregados
        self.file_pairs = {}  # {base_name: {"wav": Path, "lab": Path}}

        # Frame superior: lista de arquivos
        list_frame = tk.Frame(root)
        list_frame.pack(padx=10, pady=(10, 5), fill=tk.BOTH, expand=False)

        tk.Label(list_frame, text="Pares carregados (.wav + .lab com mesmo nome):", font=("Arial", 10, "bold")).pack(anchor="w")

        # Treeview para mostrar pares
        tree_frame = tk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.tree = ttk.Treeview(tree_frame, columns=("wav", "lab"), show="headings", height=6)
        self.tree.heading("wav", text="Arquivo WAV")
        self.tree.heading("lab", text="Arquivo LAB")
        self.tree.column("wav", width=300)
        self.tree.column("lab", width=300)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Botões de ação
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        self.btn_load = tk.Button(btn_frame, text="📂 Carregar Múltiplos .wav + .lab", command=self.load_files, width=25)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_extract = tk.Button(btn_frame, text="🔍 Extrair Features (Todos)", command=self.run_extract_all, width=25, state='disabled')
        self.btn_extract.pack(side=tk.LEFT, padx=5)

        self.btn_build = tk.Button(btn_frame, text="🧠 Construir Modelo", command=self.run_build, width=25, state='disabled')
        self.btn_build.pack(side=tk.LEFT, padx=5)

        # Área de logs
        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=15, font=("Consolas", 9))
        self.log_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def log(self, msg):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        self.root.update()

    def load_files(self):
        # Selecionar múltiplos arquivos
        files = filedialog.askopenfilenames(
            title="Selecione arquivos .wav e .lab (devem ter nomes correspondentes)",
            filetypes=[("Arquivos de áudio e rótulo", "*.wav *.lab"), ("WAV", "*.wav"), ("LAB", "*.lab"), ("Todos", "*.*")]
        )
        if not files:
            return

        wav_files = {}
        lab_files = {}

        for f in files:
            p = Path(f)
            if p.suffix.lower() == ".wav":
                wav_files[p.stem] = p
            elif p.suffix.lower() == ".lab":
                lab_files[p.stem] = p

        # Encontrar pares com mesmo nome base
        common_names = set(wav_files.keys()) & set(lab_files.keys())
        new_pairs = {}

        for name in common_names:
            if name not in self.file_pairs:
                new_pairs[name] = {"wav": wav_files[name], "lab": lab_files[name]}

        if not new_pairs:
            if not common_names:
                messagebox.showwarning("Aviso", "Nenhum par .wav/.lab com nomes correspondentes foi encontrado.")
            else:
                messagebox.showinfo("Info", "Todos os pares já foram carregados.")
            return

        # Adicionar à interface e copiar para pastas
                # Adicionar à interface e copiar para pastas
        try:
            for name, paths in new_pairs.items():
                # Copiar .wav sem alteração
                wav_dest = RAW_DIR / f"{name}.wav"
                shutil.copy2(paths["wav"], wav_dest)

                # Ler, normalizar e salvar .lab
                lab_dest = LAB_DIR / f"{name}.lab"
                with open(paths["lab"], "r", encoding="utf-8") as fin, \
                     open(lab_dest, "w", encoding="utf-8") as fout:
                    for line in fin:
                        parts = line.strip().split()
                        if len(parts) == 3:
                            start, end, ph = parts
                            ph_norm = normalize_phoneme(ph)
                            fout.write(f"{start} {end} {ph_norm}\n")
                        else:
                            fout.write(line)  # mantém linhas inválidas como estão

                self.file_pairs[name] = {"wav": wav_dest, "lab": lab_dest}
                self.tree.insert("", "end", values=(f"{name}.wav", f"{name}.lab"))

            self.log(f"✅ {len(new_pairs)} novo(s) par(es) carregado(s) e normalizados. Total: {len(self.file_pairs)}")
            self.btn_extract.config(state='normal')
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao copiar/normalizar arquivos:\n{e}")

    def run_extract_all(self):
        if not self.file_pairs:
            messagebox.showwarning("Atenção", "Nenhum par carregado.")
            return

        self.btn_extract.config(state='disabled')
        self.btn_build.config(state='disabled')
        threading.Thread(target=self._extract_all_thread, daemon=True).start()

    def _extract_all_thread(self):
        self.log(f"🚀 Iniciando extração de {len(self.file_pairs)} arquivo(s)...")
        success = 0
        for name in self.file_pairs:
            try:
                self.log(f"  → Processando: {name}")
                from src.analyze import analyze_wav
                analyze_wav(
                    str(RAW_DIR / f"{name}.wav"),
                    str(LAB_DIR / f"{name}.lab"),
                    str(FEAT_DIR)
                )
                success += 1
            except Exception as e:
                self.log(f"  ❌ Erro em {name}: {e}")

        self.log(f"✅ Extração concluída! {success}/{len(self.file_pairs)} arquivos processados.")
        self.btn_build.config(state='normal')
        self.btn_extract.config(state='normal')

    def run_build(self):
        self.btn_build.config(state='disabled')
        threading.Thread(target=self._build_thread, daemon=True).start()

    def _build_thread(self):
        self.log("🧠 Construindo banco fonêmico a partir de todos os arquivos...")
        try:
            from src.build_db import build_phoneme_db
            build_phoneme_db()
            self.log("✅ Modelo fonêmico construído com sucesso!")
        except Exception as e:
            self.log(f"❌ Erro ao construir modelo: {e}")
        finally:
            self.btn_build.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = SVSApp(root)
    root.mainloop()