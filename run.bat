@echo off
cd /d "%~dp0"
python main.py >> logs\crawler.log 2>&1
