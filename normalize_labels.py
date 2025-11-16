# normalize_labels.py
import os
from pathlib import Path

# Configuração: mapeamento de fonemas para padrão SP/AP
SILENCE_VARIANTS = {"sil", "pau", "silence", "#", "", "sp", "SIL", "PAU"}
BREATH_VARIANTS = {"br", "bre", "breath", "AP", "ap", "BR", "BRE"}

# Diretório dos arquivos .lab
LAB_DIR = Path("data/lab")
LAB_DIR.mkdir(exist_ok=True)

def normalize_lab_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    normalized_lines = []
    changed = False

    for line in lines:
        parts = line.strip().split()
        if len(parts) == 3:
            start, end, ph = parts
            orig_ph = ph

            # Normalizar silêncio
            if ph in SILENCE_VARIANTS:
                ph = "SP"
            # Normalizar respiração
            elif ph in BREATH_VARIANTS:
                ph = "AP"

            if ph != orig_ph:
                changed = True

            normalized_lines.append(f"{start} {end} {ph}\n")
        else:
            normalized_lines.append(line)

    # Salvar de volta (sobrescreve o original)
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(normalized_lines)

    return changed

def main():
    lab_files = list(LAB_DIR.glob("*.lab"))
    if not lab_files:
        print("⚠️ Nenhum arquivo .lab encontrado em data/lab/")
        return

    print(f"🔍 Encontrados {len(lab_files)} arquivos .lab. Normalizando...")
    total_changed = 0

    for lab_file in lab_files:
        if normalize_lab_file(lab_file):
            print(f" ✅ {lab_file.name}")
            total_changed += 1
        else:
            print(f" ➖ {lab_file.name} (sem alterações)")

    print(f"\n✨ Normalização concluída! {total_changed}/{len(lab_files)} arquivos modificados.")
    print("\nPadronização aplicada:")
    print("  → Silêncio: qualquer variação → 'SP'")
    print("  → Respiração: qualquer variação → 'AP'")

if __name__ == "__main__":
    main()