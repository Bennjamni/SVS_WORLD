# 🎶 SVS-WORLD  
SVS-WORLD: Singing Voice Synthesis with WORLD Vocoder (Windows-ready) *RESEARCH* *Under Development & AI Based, using QWEN*
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)]()

**SVS-WORLD** is a minimal yet fully functional **Singing Voice Synthesis (SVS)** system built from scratch using the **WORLD vocoder**. Designed for beginners and researchers, it runs entirely on **Windows** (no Linux/WSL needed) and supports real-world datasets with automatic preprocessing.

Unlike deep learning-based systems (e.g., DiffSinger, NNSVS), this project focuses on **classical parametric synthesis**, making it easy to understand, debug, and extend.

---

## ✨ Features

- 🖥️ **100% Windows-compatible** (tested on Python 3.8–3.11)
- 📂 **Supports HTS-style label files** with flexible time units:
  - 10 MHz ticks (e.g., `1824671232`)
  - Microseconds, milliseconds, or seconds
- 🧹 **Automatic label normalization**:
  - `pau`, `sil`, `#` → `SP` (silence)
  - `br`, `bre`, `AP` → `AP` (breath)
- 🔊 **Real silence modeling** – no artificial "TV static" in pauses
- 🖼️ **Alignment visualization** – see F0 vs. phonemes
- 🖱️ **Graphical user interface** for:
  - Loading `.wav` + `.lab` pairs
  - Batch feature extraction
  - Model building
  - Interactive synthesis (phoneme-by-phoneme)
- 🧪 **No GPU required** – runs on CPU only

---

## 🛠️ Tech Stack

- **Vocoder**: [WORLD](https://github.com/mmorise/World) (via `pyworld`)
- **Audio I/O**: `librosa`, `soundfile`
- **GUI**: `tkinter` (built-in)
- **Alignment**: Manual (HTS-style labels)
- **Language**: Python 3

---

## 🚀 Quick Start (Windows)

1. Install dependencies:
   ```cmd
   pip install -r requirements.txt

## Use cases
Educational projects on speech/singing synthesis
Custom voice banks for amateur music production
Baseline system for SVS research
Lightweight alternative to UTAU/DeepVocal

## 🙌 Acknowledgements
WORLD Vocoder by Masanori Morise
pyworld
HTS, Sinsy, and OpenUTAU for inspiration
