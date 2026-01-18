@echo off
echo Starting test... > c:\Users\Acer\Desktop\clinical-ml-pipeline\debug_log.txt
c:\Users\Acer\Desktop\clinical-ml-pipeline\.venv\Scripts\python.exe --version >> c:\Users\Acer\Desktop\clinical-ml-pipeline\debug_log.txt 2>&1
echo Running script... >> c:\Users\Acer\Desktop\clinical-ml-pipeline\debug_log.txt
c:\Users\Acer\Desktop\clinical-ml-pipeline\.venv\Scripts\python.exe c:\Users\Acer\Desktop\clinical-ml-pipeline\test_pmc_dataset.py >> c:\Users\Acer\Desktop\clinical-ml-pipeline\debug_log.txt 2>&1
echo Done. >> c:\Users\Acer\Desktop\clinical-ml-pipeline\debug_log.txt
