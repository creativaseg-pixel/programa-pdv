; ============================================================
; Inno Setup Script - Instalador PDV Supermercado
; ============================================================
; Compila com: Inno Setup Compiler (https://jrsoftware.org/isinfo.php)
; Resultado: setup_PDV_Supermercado_v1.0.0.exe
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

; Pasta padrão de instalação: C:\Program Files (x86)\PDV Supermercado em 64-bit
; ou C:\Program Files\PDV Supermercado em 32-bit
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}

; Permite ao usuário escolher pasta
DisableProgramGroupPage=no
AllowNoIcons=yes

; Saída
OutputDir=output
OutputBaseFilename=setup_PDV_Supermercado_v{#AppVersion}
SetupIconFile=icone.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Suporte 32 e 64 bits
ArchitecturesAllowed=x86 x64
ArchitecturesInstallIn64BitMode=x64

; Privilégios admin para instalar em Program Files
PrivilegesRequired=admin

; Imagens do wizard (opcional, coloque na mesma pasta)
; WizardImageFile=installer-side.bmp
; WizardSmallImageFile=installer-icon.bmp

; Idiomas
ShowLanguageDialog=no
LanguageDetectionMethod=locale

; Versão mínima do Windows: 7
MinVersion=6.1

; Desinstalador
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Executável principal (gerado pelo PyInstaller)
Source: "dist\PDV_Supermercado.exe"; DestDir: "{app}"; Flags: ignoreversion

; Ícone para atalhos
Source: "icone.ico"; DestDir: "{app}"; Flags: ignoreversion

; Documentação (opcional)
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

; Pasta de dados inicial (banco SQLite vazio será criado no primeiro uso)
; Se você quiser distribuir um banco pré-populado:
; Source: "data\pdv.db"; DestDir: "{commonappdata}\{#AppName}"; Flags: onlyifdoesntexist uninsneveruninstall

[Dirs]
; Cria a pasta de dados em C:\ProgramData\PDV Supermercado (acessível por todos os usuários)
Name: "{commonappdata}\{#AppName}"; Permissions: users-modify
Name: "{commonappdata}\{#AppName}\backups"; Permissions: users-modify
Name: "{commonappdata}\{#AppName}\logs"; Permissions: users-modify

[Icons]
; Atalho no menu iniciar
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icone.ico"
Name: "{group}\Manual do Usuário"; Filename: "{app}\README.txt"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Atalho na área de trabalho (se marcado)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icone.ico"; Tasks: desktopicon

; Atalho na barra de inicialização rápida (Windows antigos)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icone.ico"; Tasks: quicklaunchicon

[Run]
; Pergunta se quer abrir após instalar
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Ao desinstalar, mantém os dados do usuário por padrão
; Se quiser apagar TUDO ao desinstalar, descomente as linhas abaixo:
; Type: filesandordirs; Name: "{commonappdata}\{#AppName}"

[Code]
// ============================================================
// Verifica se o PDV já está rodando antes de instalar/atualizar
// ============================================================
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Mata processo se estiver aberto (atualização)
  Exec('taskkill.exe', '/F /IM PDV_Supermercado.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  Exec('taskkill.exe', '/F /IM PDV_Supermercado.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// ============================================================
// Pergunta se quer manter os dados ao desinstalar
// ============================================================
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
      Response := MsgBox('Deseja remover também o banco de dados e backups do PDV?' + #13#10 + #13#10 +
                        'Pasta: ' + DataDir + #13#10 + #13#10 +
                        'Clique SIM para apagar TUDO ou NÃO para preservar os dados.',
                        mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
      if Response = IDYES then
        DelTree(DataDir, True, True, True);
    end;
  end;
end;
