@echo off
echo ========================================================
echo   Pushing UAV Disaster Management GA to GitHub
echo   Target: https://github.com/yarrmani/uav-disaster-management-ga
echo ========================================================
echo.
echo Please ensure you have created the empty repository on GitHub:
echo https://github.com/new (Name: uav-disaster-management-ga)
echo.
"C:\Program Files\Git\cmd\git.exe" push -u origin main
echo.
pause
