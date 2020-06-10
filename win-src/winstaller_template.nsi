# The installer simply:
#    - installs the pyinstaller bundle directory,
#    - creates a start menu shortcut,
#    - builds an uninstaller, and
#    - adds uninstall information to the registry for Add/Remove Programs
# Run makensis on this file to produce the installer
 
!define APPNAME "EPI2ME Labs Launcher"
!define COMPANYNAME "Oxford Nanopore Technologies"
!define DESCRIPTION "EPI2ME Labs Notebook Server Controller"
# These three must be integers
!define VERSIONMAJOR <<VERSIONMAJOR>>
!define VERSIONMINOR <<VERSIONMINOR>>
!define VERSIONBUILD <<VERSIONBUILD>>
# These will be displayed by the "Click here for support information" link in "Add/Remove Programs"
# It is possible to use "mailto:" links in here to open the email client
!define HELPURL "mailto:support@nanoporetech.com" # "Support Information" link
!define UPDATEURL "https://github.com/epi2me-labs/labslauncher/releases" # "Product Updates" link
!define ABOUTURL "https://colab.research.google.com/github/epi2me-labs/resources/blob/master/welcome.ipynb" # "Publisher" link
!define INSTALLSIZE 99924 # size (in kB), used in Add/Remove programs
!define SOURCELOCATION "dist\EPI2ME-Labs-Launcher\"  # backslash important
!define ICONLOCATION "labslauncher\epi2me.ico"  # this is used as both relative to make directory and install directory
!define APPEXENAME "EPI2ME-Labs-Launcher"
outFile "dist\epi2melabs-installer.exe"
LicenseData "LICENSE.rtf"

# No need to edit below here

# This will be in the installer/uninstaller's title bar
Name "${COMPANYNAME} - ${APPNAME}"
Icon "${ICONLOCATION}"
RequestExecutionLevel admin ;Require admin rights on NT6+ (When UAC is turned on)
InstallDir "$PROGRAMFILES\${COMPANYNAME}\${APPNAME}"
!define UNINSTALL_REG_PATH "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"

!include LogicLib.nsh

# Just three pages - license agreement, install location, and installation
page license
page directory
page instfiles

# Require admin
!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin" ;Require admin rights on NT4+
        messageBox mb_iconstop "Administrator rights required!"
        setErrorLevel 740 ;ERROR_ELEVATION_REQUIRED
        quit
${EndIf}
!macroend

!macro UninstallExisting exitcode uninstcommand
Push `${uninstcommand}`
Call UninstallExisting
Pop ${exitcode}
!macroend
Function UninstallExisting
Exch $1 ; uninstcommand
Push $2 ; Uninstaller
Push $3 ; Len
StrCpy $3 ""
StrCpy $2 $1 1
StrCmp $2 '"' qloop sloop
sloop:
	StrCpy $2 $1 1 $3
	IntOp $3 $3 + 1
	StrCmp $2 "" +2
	StrCmp $2 ' ' 0 sloop
	IntOp $3 $3 - 1
	Goto run
qloop:
	StrCmp $3 "" 0 +2
	StrCpy $1 $1 "" 1 ; Remove initial quote
	IntOp $3 $3 + 1
	StrCpy $2 $1 1 $3
	StrCmp $2 "" +2
	StrCmp $2 '"' 0 qloop
run:
	StrCpy $2 $1 $3 ; Path to uninstaller
	StrCpy $1 161 ; ERROR_BAD_PATHNAME
	GetFullPathName $3 "$2\.." ; $InstDir
	IfFileExists "$2" 0 +4
	ExecWait '"$2" /S _?=$3' $1 ; This assumes the existing uninstaller is a NSIS uninstaller, other uninstallers don't support /S nor _?=
	IntCmp $1 0 "" +2 +2 ; Don't delete the installer if it was aborted
	Delete "$2" ; Delete the uninstaller
	RMDir "$3" ; Try to delete $InstDir
	RMDir "$3\.." ; (Optional) Try to delete the parent of $InstDir
Pop $3
Pop $2
Exch $1 ; exitcode
FunctionEnd

# Installer
# ---------
Function .onInit
	setShellVarContext all
	!insertmacro VerifyUserIsAdmin

	ReadRegStr $0 HKLM "${UNINSTALL_REG_PATH}" "UninstallString"
	${If} $0 != ""
	${AndIf} ${Cmd} `MessageBox MB_YESNO|MB_ICONQUESTION "Uninstall previous version?" /SD IDYES IDYES`
		!insertmacro UninstallExisting $0 $0
		${If} $0 <> 0
			MessageBox MB_YESNO|MB_ICONSTOP "Failed to uninstall, continue anyway?" /SD IDYES IDYES +2
			Abort
		${EndIf}
	${EndIf}
FunctionEnd


section "install"
	# Install path
	setOutPath $INSTDIR
	# Files
	File /nonfatal /r "${SOURCELOCATION}"

	# Uninstaller
	writeUninstaller "$INSTDIR\uninstall.exe"
	# Start Menu
	createDirectory "$SMPROGRAMS\${COMPANYNAME}"
	createShortCut "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk" "$INSTDIR\${APPEXENAME}" "" "$INSTDIR\${ICONLOCATION}"
	# Registry information for add/remove programs
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "DisplayName" "${COMPANYNAME} - ${APPNAME} - ${DESCRIPTION}"
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "InstallLocation" "$\"$INSTDIR$\""
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "DisplayIcon" "$\"$INSTDIR\${ICONLOCATION}$\""
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "Publisher" "$\"${COMPANYNAME}$\""
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "HelpLink" "$\"${HELPURL}$\""
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "URLUpdateInfo" "$\"${UPDATEURL}$\""
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "URLInfoAbout" "$\"${ABOUTURL}$\""
	WriteRegStr HKLM "${UNINSTALL_REG_PATH}" "DisplayVersion" "$\"${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}$\""
	WriteRegDWORD HKLM "${UNINSTALL_REG_PATH}" "VersionMajor" ${VERSIONMAJOR}
	WriteRegDWORD HKLM "${UNINSTALL_REG_PATH}" "VersionMinor" ${VERSIONMINOR}
	WriteRegDWORD HKLM "${UNINSTALL_REG_PATH}" "NoModify" 1
	WriteRegDWORD HKLM "${UNINSTALL_REG_PATH}" "NoRepair" 1
	WriteRegDWORD HKLM "${UNINSTALL_REG_PATH}" "EstimatedSize" ${INSTALLSIZE}
sectionEnd
 
# Uninstaller
# -----------
function un.onInit
	SetShellVarContext all
 
	#Verify the uninstaller - last chance to back out
	MessageBox MB_OKCANCEL "Permanantly remove ${APPNAME}?" IDOK next
		Abort
	next:
	!insertmacro VerifyUserIsAdmin
functionEnd
 
section "uninstall"
	# Remove Start Menu launcher
	delete "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk"
	# Try to remove the Start Menu folder - this will only happen if it is empty
	rmDir "$SMPROGRAMS\${COMPANYNAME}"
	# Remove files
	<<UNINSTALL_LIST>>
	# Always delete uninstaller as the last action
	delete $INSTDIR\uninstall.exe
	# Try to remove the install directory - this will only happen if it is empty
	rmDir $INSTDIR
	# Remove uninstaller information from the registry
	DeleteRegKey HKLM "${UNINSTALL_REG_PATH}"
sectionEnd

