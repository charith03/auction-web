@echo off
echo ==========================================
echo      Auction App Backend Setup
echo ==========================================

echo [1/4] Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate
) else (
    echo Error: .venv not found. checking for venv...
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate
    ) else (
        echo Could not find virtual environment. Please create one.
        pause
        exit /b
    )
)

echo [2/4] Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies.
    pause
    exit /b
)

echo [3/4] Setting up database...
python setup_db.py
if %ERRORLEVEL% NEQ 0 (
    echo Error setting up database.
    pause
    exit /b
)

echo [4/4] Running migrations...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo Error running migrations.
    pause
    exit /b
)

echo.
echo ==========================================
echo      Setup Complete! Starting Server...
echo ==========================================
echo.
python manage.py runserver
pause
