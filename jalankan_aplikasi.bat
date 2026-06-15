@echo off
REM ============================================================
REM   SPK Saham Undervalued - Launcher Windows
REM   Klik dua kali file ini untuk menjalankan aplikasi.
REM ============================================================

cd /d "%~dp0"

echo ============================================================
echo  SPK Pemilihan Saham Undervalued - TOPSIS Graham Lynch
echo ============================================================
echo.

REM 1) Cek Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python belum terpasang di komputer ini.
    echo.
    echo Silakan unduh Python di:
    echo     https://www.python.org/downloads/
    echo Saat instalasi, CENTANG "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo [OK] Python ditemukan:
python --version
echo.

REM 2) Pasang dependensi (sekali saja - aman dijalankan ulang)
echo [STEP 1/2] Memasang library yang dibutuhkan...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Gagal memasang dependensi. Cek koneksi internet.
    pause
    exit /b 1
)
echo [OK] Library siap.
echo.

REM 3) Jalankan Streamlit
echo [STEP 2/2] Menjalankan aplikasi...
echo Browser akan terbuka otomatis di http://localhost:8501
echo Tekan CTRL+C di jendela ini untuk menghentikan aplikasi.
echo.
python -m streamlit run app.py

pause
