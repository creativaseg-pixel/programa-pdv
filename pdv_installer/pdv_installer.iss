; ============================================================
; Inno Setup Script - Instalador UNIFICADO PDV Supermercado
; Detecta automaticamente Windows 32 ou 64 bits e instala a
; versao correta do executavel. UM UNICO arquivo .exe para
; distribuir ao cliente.
; ============================================================
; Compila com: Inno Setup Compiler 6 (https://jrsoftware.org/isinfo.php)
; Saida: output\setup_PDV_Supermercado_v1.0.0.exe (~25-50 MB)
; Suporta: Windows 7, 8, 10, 11 (32 e 64 bits)
; ============================================================

#define AppName        "PDV Supermercado"
#define AppVersion     "1.0.0"
#define AppPublisher   "Sua Empresa LTDA"
#define AppURL         "https://seusite.com.br"
#define AppExeName     "PDV_Supermercado.exe"
#define AppId          "{{A4D8F1B2-7C5E-4F3D-9A6B-2E0F1C8D5B7A}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=no
AllowNoIcons=yes

OutputDir=output
OutputBaseFilename=setup_PDV_Supermercado_v{#AppVersion}
SetupIconFile=icone.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Suporta 32 e 64 bits (instala a versao adequada)
ArchitecturesAllowed=x86 x64
ArchitecturesInstallIn64BitMode=x64

PrivilegesRequired=admin
MinVersion=6.1

UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; -------- INSTALACAO 64-BIT --------
; So instala em Windows 64-bit (Check: Is64BitInstallMode)
Source: "dist\PDV_Supermercado_x64.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion; Check: Is64BitInstallMode

; -------- INSTALACAO 32-BIT --------
; So instala em Windows 32-bit (Check: not Is64BitInstallMode)
Source: "dist\PDV_Supermercado_x86.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion; Check: not Is64BitInstallMode

; -------- ARQUIVOS COMUNS --------
Source: "icone.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Dirs]
; Pasta de dados (compartilhada entre usuarios)
Name: "{commonappdata}\{#AppName}"; Permissions: users-modify
Name: "{commonappdata}\{#AppName}\backups"; Permissions: users-modify
Name: "{commonappdata}\{#AppName}\qrcodes"; Permissions: users-modify
Name: "{commonappdata}\{#AppName}\etiquetas"; Permissions: users-modify

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icone.ico"
Name: "{group}\Manual do Usuário"; Filename: "{app}\README.txt"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icone.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Fecha o PDV se estiver aberto (atualizacao)
  Exec('taskkill.exe', '/F /IM PDV_Supermercado.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  Exec('taskkill.exe', '/F /IM PDV_Supermercado.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
  Response: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataDir := ExpandConstant('{commonappdata}\{#AppName}');
    if DirExists(DataDir) then
    begin
      Response := MsgBox('Deseja remover também o banco de dados, backups e arquivos do PDV?' + #13#10 + #13#10 +
                        'Pasta: ' + DataDir + #13#10 + #13#10 +
                        'Clique SIM para apagar TUDO ou NÃO para preservar os dados.',
                        mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
      if Response = IDYES then
        DelTree(DataDir, True, True, True);
    end;
  end;
end;
