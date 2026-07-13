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
UninstallDisplayIcon={app}\backend\LearningPlatformBackend.exe
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
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher\start-learning-platform.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\backend\LearningPlatformBackend.exe"
Name: "{group}\{#MyAppName}"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher\start-learning-platform.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\backend\LearningPlatformBackend.exe"
Name: "{group}\停止{#MyAppName}"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher\stop-learning-platform.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\backend\LearningPlatformBackend.exe"
Name: "{group}\卸载{#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher\start-learning-platform.vbs"""; Description: "安装完成后立即启动学习平台"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\uploads"
