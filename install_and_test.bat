@echo off
echo Installing fuzzywuzzy...
python -m pip install fuzzywuzzy python-Levenshtein
echo.
echo Installation complete!
echo.
echo Now running test...
python test_enhanced_pipeline.py
pause
