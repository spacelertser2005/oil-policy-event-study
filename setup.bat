@echo off
REM Setup script for Oil Policy Event Study project
REM Run this from: C:\Users\mattl\Projects\oil-policy-event-study

echo === Setting up Oil Policy Event Study ===

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

echo.
echo === Setup complete ===
echo.
echo Next steps:
echo   1. Copy your FRED CSV files into data\raw\
echo   2. Run: python src\pull_wrds_data.py  (for CRSP equity data)
echo   3. Run: python src\event_study.py      (for the analysis)
echo.
pause
