#define MyAppName "学习平台"
#define MyAppVersion "1.0.0"
#ifndef SourceDir
  #define SourceDir "..\build\windows-release\bundle"
#endif
#ifndef OutputDir
  #define OutputDir "..\build\windows-release\installer"
#endif

[Setup]
AppId={{1A90D8A0-3D53-4A67-8F83-9FD9B5E87A62}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Codex
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir={#OutputDir}
OutputBaseFilename=学习平台-Setup
UninstallDisplayIcon={app}\LearningPlatformControlPanel.exe
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
DiskSpanning=yes
DiskSliceSize=max
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#SourceDir}\*"; Excludes: "uploads\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{#SourceDir}\uploads\*"; DestDir: "{app}\uploads"; Flags: recursesubdirs createallsubdirs ignoreversion nocompression

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\LearningPlatformControlPanel.exe"; WorkingDir: "{app}"; IconFilename: "{app}\LearningPlatformControlPanel.exe"
Name: "{group}\{#MyAppName}"; Filename: "{app}\LearningPlatformControlPanel.exe"; WorkingDir: "{app}"; IconFilename: "{app}\LearningPlatformControlPanel.exe"
Name: "{group}\卸载{#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\LearningPlatformControlPanel.exe"; Description: "安装完成后立即启动学习平台"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\LearningPlatformControlPanel.exe"; Parameters: "--shutdown-existing"; WorkingDir: "{app}"; Flags: runhidden waituntilterminated; RunOnceId: "StopLearningPlatform"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\uploads"
