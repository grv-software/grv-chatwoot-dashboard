@echo off
setlocal
set /p NXLITE_USER="Usuario CRM (crm.nxlite.com.br): "
set /p NXLITE_PASS="Senha: "
python "%~dp0atualizar_dados.py"
set NXLITE_USER=
set NXLITE_PASS=
pause
