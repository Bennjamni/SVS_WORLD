@echo off
python src\build_db.py
python src\synthesize.py examples\input.lab examples\output.wav 293.66
echo.
echo 🎵 Síntese concluída! Áudio salvo em examples\output.wav
pause