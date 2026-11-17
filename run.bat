cd /d "%~dp0"
set PYTHONPATH=src
py -m gameset --mode=gui %*
pause
