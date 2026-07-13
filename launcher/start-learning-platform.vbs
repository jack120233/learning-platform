Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
launcherDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = launcherDir
shell.Run "cmd.exe /c """ & launcherDir & "\start-learning-platform.cmd""", 0, False
