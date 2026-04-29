# Video to Text

Projeto Python para Windows que processa apenas os arquivos `.mp4` na raiz de `E:\obs`, transcreve a fala com GPU NVIDIA e grava um arquivo `.md` com o mesmo nome do vídeo.

## O que este projeto faz

- varre somente a raiz de `E:\obs`
- ignora subpastas
- usa `faster-whisper` com `device="cuda"`
- grava `arquivo.md` ao lado de `arquivo.mp4`
- mantém um estado simples em `%LOCALAPPDATA%\video-to-text\processed_videos.json`
- gera log em `%LOCALAPPDATA%\video-to-text\logs\last-run.log`
- empacota um executável Windows com `PyInstaller`

## Pré-requisitos

- Windows
- GPU NVIDIA disponível
- Python 3.11
- Driver NVIDIA funcional

## Instalação

Ative a `.venv` antes de instalar qualquer pacote:

```powershell
Set-Location "E:\projetos\video-to-text"
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

## Execução em modo de desenvolvimento

```powershell
Set-Location "E:\projetos\video-to-text"
.\.venv\Scripts\Activate.ps1
python -m video_to_text
```

## Build do executável

```powershell
Set-Location "E:\projetos\video-to-text"
.\.venv\Scripts\Activate.ps1
.\build.ps1
```

O executável será gerado em `dist\video-to-text\video-to-text.exe`.

## Uso por duplo clique

- durante desenvolvimento: dê dois cliques em `run.bat`
- após o build: dê dois cliques em `dist\video-to-text\video-to-text.exe`

## Observações

- O aplicativo usa um diretório fixo para reduzir risco de processamento acidental fora de `E:\obs`.
- Se um vídeo ainda estiver sendo gravado, ele será pulado e poderá ser processado na próxima execução.
- Se o `.md` for removido manualmente, o vídeo será transcrito novamente.

