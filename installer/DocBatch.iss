#define AppName "DocBatch"
#define AppVersion "1.0.0"
#define AppExeName "DocBatch.exe"
#define BundleDir "..\dist\DocBatch"

[Setup]
AppId={{4C3B9A2E-6F81-4D5A-9E7B-2D1C8F0A6B34}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=DocBatch
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
DirExistsWarning=no
AllowNoIcons=yes
OutputDir=..\dist\installer
OutputBaseFilename=DocBatch-1.0.0-setup
UninstallDisplayName={#AppName} {#AppVersion}
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/max
SolidCompression=yes

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch DocBatch"; Flags: nowait postinstall skipifsilent
