@echo off
cd /d "%~dp0"
start cmd /k "streamlit run app.py"
timeout /t 3 >nul
start http://localhost:8501
