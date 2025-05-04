@echo off
chcp 65001 >nul
cd /d C:\PRY-PI2\pi2.emociones
call env\Scripts\activate

:: Registrar salida en log.txt
python main.py > log.txt 2>&1

echo.
echo La salida ha sido guardada en log.txt
echo Presiona cualquier tecla para cerrar...
pause >nul
