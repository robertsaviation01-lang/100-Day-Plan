@echo off
REM Launch 100-Day Plan Dashboard (Production Path)
REM Runs mandatory preflight checks before starting Streamlit.

cd /d "%~dp0"
call go_live_production.cmd
