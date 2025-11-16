@echo off
echo Normalizando labels...
python normalize_labels.py
set RAW=data\raw
set LAB=data\lab
set FEAT=data\features

for %%f in ("%RAW%\*.wav") do (
    echo Processando %%~nf
    python src\analyze.py "%%f" "%LAB%\%%~nf.lab" "%FEAT%"
)
echo.
echo ✅ Extração concluída!
pause