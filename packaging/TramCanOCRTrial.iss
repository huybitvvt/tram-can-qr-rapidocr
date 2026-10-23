#define AppVersion "0.2.0-trial1"
[Setup]
AppId={{915E8EE7-4745-46E2-9BA6-3D315E582F6A}
AppName=Tram Can OCR - Ban thu
AppVersion={#AppVersion}
AppPublisher=TramCan QR
AppPublisherURL=https://github.com/huybitvvt/tram-can-qr-rapidocr
DefaultDirName={localappdata}\Programs\TramCanOCRTrial
DefaultGroupName=Tram Can OCR - Ban thu
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\TramCanOCRTrial.exe
CloseApplications=yes
RestartApplications=no
OutputDir=..\dist\installer
OutputBaseFilename=TramCanOCRTrial-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=..\LICENSE
InfoBeforeFile=trial-info.txt
SetupLogging=no
VersionInfoVersion=0.2.0.1
[Files]
Source: "..\dist\TramCanOCRTrial\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\docs\CAI-BAN-THU.md"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\Tram Can OCR - Ban thu"; Filename: "{app}\TramCanOCRTrial.exe"
Name: "{autodesktop}\Tram Can OCR - Ban thu"; Filename: "{app}\TramCanOCRTrial.exe"
[Run]
Filename: "{app}\TramCanOCRTrial.exe"; Description: "Mo ban thu nhan dien can (khong luu du lieu)"; Flags: nowait postinstall skipifsilent
