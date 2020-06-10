Write-Host " ++ Running windows build in powershell"
$env:PATH += ";C:\Program Files (x86)\Python\;C:\Program Files (x86)\Python\Scripts"
Write-Host " ++ Creating build environment"
pip install virtualenv
virtualenv venv --prompt "(build) "
venv/Scripts/activate
Write-Host " ++ Installing requirements"
pip install pip --upgrade
pip install pyqt5-sip==12.7.2
pip install -r requirements.txt
Write-Host " ++ Running setup.py"
python setup.py develop
Write-Host " ++ Creating Bundle"
pyinstaller EPI2ME-Labs-Launcher.spec
Write-Host " ++ Creating Installer"
python win-src/create_nsi.py .\dist\EPI2ME-Labs-Launcher\ winstaller.nsi
cp LICENSE.md LICENSE.rtf
& 'C:\Program Files (x86)\NSIS\makensis.exe' .\winstaller.nsi
