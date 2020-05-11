Write-Host "Running windows build in powershell"
$env:PATH += ";C:\Program Files (x86)\Python\;C:\Program Files (x86)\Python\Scripts"
pip install virtualenv
virtualenv venv --prompt "(build) "
venv/Scripts/activate
pip install pip --upgrade
pip install pyqt5-sip==12.7.2
pip install -r requirements.txt
python setup.py develop
pyinstaller EPI2ME-Labs-Launcher.spec
