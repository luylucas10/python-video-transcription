# Python Fast Whisper

Transcreve `.mp4` para Markdown usando `faster-whisper`. Aceita um diretório, arquivos específicos, ou pede o diretório interativamente quando nenhum argumento de entrada é fornecido.

## O que este projeto faz

- Aceita `-d path\to\videos` para varrer a raiz de um diretório
- Aceita `-v path\to\video.mp4` (repetível) para transcrever arquivos específicos
- Pede o diretório interativamente quando nenhum `-d`/`-v` é fornecido
- Grava `arquivo.md` ao lado de cada `arquivo.mp4` selecionado
- Tenta GPU (CUDA/float16) primeiro; cai automaticamente para CPU (int8) se o modelo não carregar ou a primeira transcrição falhar
- Mantém estado em `data\processed_videos.json` para não retranscrever vídeos já processados
- Gera log em `logs\last-run.log`
- Pula vídeos cujo tamanho ainda está mudando (gravação em andamento)

## Pré-requisitos

- Windows ou Linux
- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado
- GPU NVIDIA com driver funcional (recomendado; CPU funciona como fallback)
- `ffmpeg` instalado (necessário para processamento de vídeo)

## Configuração

### Windows

#### 1. Instalar uv

```powershell
winget install astral-sh.uv
```

#### 2. Criar o ambiente virtual

Na raiz do projeto:

```powershell
uv python pin 3.11
uv sync
```

Isso cria `.venv` com Python 3.11 e instala todas as dependências do `uv.lock`.

### Linux

#### 1. Instalar uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Adicione `~/.local/bin` ao PATH se necessário:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

#### 2. Instalar ffmpeg

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# Fedora/RHEL
sudo dnf install ffmpeg

# macOS (com Homebrew)
brew install ffmpeg
```

#### 3. Criar o ambiente virtual

Na raiz do projeto:

```bash
uv python pin 3.11
uv sync
```

Isso cria `.venv` com Python 3.11 e instala todas as dependências do `uv.lock`.

### 3. Baixar o modelo

O modelo padrão é `Systran/faster-whisper-large-v3` (~3 GB). Baixe-o para um diretório local dentro do projeto:

> hf - [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli). Depois de instalar > hf auth login - Com uma conta, você aumenta a taxa de download dos modelos

**Windows:**

```powershell
hf download Systran/faster-whisper-large-v3 --local-dir models\faster-whisper-large-v3
```

**Linux/macOS:**

```bash
hf download Systran/faster-whisper-large-v3 --local-dir models/faster-whisper-large-v3
```

Modelo alternativo (mais rápido, menor precisão):

**Windows:**

```powershell
hf download mobiuslabsgmbh/faster-whisper-large-v3-turbo --local-dir models\faster-whisper-large-v3-turbo
```

**Linux/macOS:**

```bash
hf download mobiuslabsgmbh/faster-whisper-large-v3-turbo --local-dir models/faster-whisper-large-v3-turbo
```

## Execução

### Windows

#### Varrer um diretório

```powershell
uv run python -m video_to_text -d path\to\videos --model models\faster-whisper-large-v3
```

#### Transcrever arquivos específicos

```powershell
uv run python -m video_to_text -v path\to\aula.mp4 -v path\to\outra.mp4 --model models\faster-whisper-large-v3
```

#### Modo interativo (sem argumentos de entrada)

```powershell
uv run python -m video_to_text --model models\faster-whisper-large-v3
```

O programa pedirá o caminho do diretório antes de iniciar.

#### Via `run.bat` (duplo clique)

```bat
run.bat
```

> O `run.bat` usa o modelo padrão `large-v3` com cache automático do faster-whisper.
> Para usar o modelo baixado localmente, passe `--model models\faster-whisper-large-v3` diretamente.

### Linux/macOS

#### Varrer um diretório

```bash
uv run python -m video_to_text -d /path/to/videos --model models/faster-whisper-large-v3
```

#### Transcrever arquivos específicos

```bash
uv run python -m video_to_text -v /path/to/aula.mp4 -v /path/to/outra.mp4 --model models/faster-whisper-large-v3
```

#### Modo interativo (sem argumentos de entrada)

```bash
uv run python -m video_to_text --model models/faster-whisper-large-v3
```

O programa pedirá o caminho do diretório antes de iniciar.

#### Via launcher `run.sh`

```bash
./run.sh --model models/faster-whisper-large-v3
```

> O `run.sh` é o equivalente Linux do `run.bat`. Passa todos os argumentos para o CLI.

#### Dry-run (listar vídeos sem transcrever)

```bash
uv run python -m video_to_text -d /path/to/videos --dry-run
```

#### Reprocessar todos os vídeos

```bash
uv run python -m video_to_text -d /path/to/videos --reprocess --model models/faster-whisper-large-v3
```

## Comportamento de entrada

| Forma de uso          | Comportamento                                            |
| --------------------- | -------------------------------------------------------- |
| `-d path\to\videos`   | Varre somente a raiz do diretório informado              |
| `-v v1.mp4 -v v2.mp4` | Transcreve exatamente esses arquivos, na ordem fornecida |
| Sem `-d` nem `-v`     | Pede o caminho do diretório interativamente              |
| `-d` e `-v` juntos    | Erro: são mutuamente exclusivos                          |

**Saída:** cada `.md` é gravado ao lado do `.mp4` correspondente, com o mesmo nome base (ex.: `aula.mp4` → `aula.md`).

## Dispositivo e fallback automático

A aplicação tenta GPU (CUDA, float16) primeiro. Se o modelo não carregar ou a primeira transcrição falhar antes de qualquer vídeo ser processado com sucesso, ela registra o erro e repete automaticamente com CPU (int8). Depois que ao menos um vídeo é processado com sucesso na GPU, falhas posteriores vão para o log de erros sem trocar de dispositivo.

## Opções

### Entrada/Saída

| Flag            | Descrição                                         |
| --------------- | ------------------------------------------------- |
| `-d`, `--dir`   | Diretório a escanear (raiz apenas, sem subpastas) |
| `-v`, `--video` | Arquivo `.mp4` específico (pode ser repetido)     |

### Modelo e processamento

| Flag           | Descrição                                                                                                   |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| `--model`      | Modelo faster-whisper: shorthand (`large-v3`), ID do HF (`Systran/faster-whisper-large-v3`), ou pasta local |
| `--language`   | Idioma (`pt` padrão, `auto` para detecção automática)                                                       |
| `--batch-size` | Chunks de áudio em paralelo na GPU (padrão: 16 para RTX 3090)                                               |

### Qualidade de transcrição

| Flag                            | Padrão    | Descrição                                                                                                         |
| ------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------- |
| `--prompt-type`                 | `general` | Preset de prompt inicial: `tech` para vídeos técnicos, `meeting` para reuniões corporativas, `general` sem prompt |
| `--initial-prompt`              | `None`    | Prompt inicial customizado (sobrescreve `--prompt-type`)                                                          |
| `--no-speech-threshold`         | `0.6`     | Limite para detecção de silêncio (0.0-1.0; maior = mais sensível)                                                 |
| `--compression-ratio-threshold` | `2.4`     | Limite de compressão para detectar alucinações (aumentar para mais tolerância)                                    |
| `--log-prob-threshold`          | `-1.0`    | Limite de log-probability para filtrar segmentos baixa confiança (aumentar para mais rigoroso)                    |
| `--temperature`                 | `0.0`     | Temperatura para decodificação (0.0=determinístico, >0=sampling)                                                  |

### Arquivo

| Flag          | Descrição                                              |
| ------------- | ------------------------------------------------------ |
| `--dry-run`   | Mostra quais vídeos seriam processados sem transcrever |
| `--reprocess` | Ignora o estado salvo e retranscreve todos os vídeos   |

### Estabilidade

| Flag                       | Padrão | Descrição                                                     |
| -------------------------- | ------ | ------------------------------------------------------------- |
| `--stability-wait-seconds` | `2.0`  | Espera entre verificações de estabilidade do arquivo          |
| `--stability-checks`       | `2`    | Quantidade de comparações para detectar arquivo em escrita    |
| `--max-tokens-per-chunk`   | `500`  | Limite de tokens por chunk no markdown (encoding cl100k_base) |

## Presets de prompt

### `--prompt-type tech`

Otimizado para **vídeos técnicos** (YouTube, tutoriais, talks):

```
"Conteúdo técnico de software. Mantenha termos em inglês (API, framework, library, deploy, etc.)
e nomes de produtos exatamente como pronunciados. Use português formal."
```

→ Preserva vocabulário técnico em inglês. Ideal para conteúdo dev/tech.

### `--prompt-type meeting`

Otimizado para **reuniões corporativas** (business calls, apresentações internas):

```
"Reunião corporativa. Use português formal. Mantenha nomes de empresas, produtos e pessoas
exatamente como pronunciados. Minimize palavras de hesitação."
```

→ Transcrição limpa e formal. Remove ruído de fala ("uh", "né", "assim").

### `--prompt-type general` (padrão)

Sem prompt inicial. Whisper usa comportamento padrão.

### Customização

Para um prompt específico:

```powershell
uv run python -m video_to_text -v video.mp4 --initial-prompt "Sua instrução aqui"
```

O flag `--initial-prompt` sobrescreve `--prompt-type`.

## Exemplos de uso

### Transcrever vídeo técnico (YouTube)

```powershell
uv run python -m video_to_text -v tutorial.mp4 --prompt-type tech
```

### Transcrever reunião corporativa

```powershell
uv run python -m video_to_text -v meeting.mp4 --prompt-type meeting
```

### Transcrever com qualidade máxima (mais lento)

```powershell
uv run python -m video_to_text -d path\to\videos --batch-size 8 --beam-size 10 --temperature 0.1
```

### Customizar prompt

```powershell
uv run python -m video_to_text -v video.mp4 --initial-prompt "Transcrição de podcast sobre história. Mantenha nomes de lugares corretos."
```

### Filtrar alucinações mais agressivamente

```powershell
uv run python -m video_to_text -d path\to\videos --compression-ratio-threshold 1.5 --log-prob-threshold -0.5
```

## Estado e logs

| Arquivo                      | Descrição                                                                        |
| ---------------------------- | -------------------------------------------------------------------------------- |
| `data\processed_videos.json` | Estado dos vídeos já processados (fingerprint por tamanho e data de modificação) |
| `logs\last-run.log`          | Log da última execução                                                           |

Para forçar a retranscrição de um vídeo específico, remova o `.md` correspondente e rode com `--reprocess`, ou delete a entrada do vídeo em `data\processed_videos.json`.

## Reprocessar todos os vídeos

```powershell
uv run python -m video_to_text -d path\to\videos --model models\faster-whisper-large-v3 --reprocess
```

## Troubleshooting

**CUDA não encontrado**

Verifique o driver NVIDIA e o CUDA toolkit. O `faster-whisper` exige CUDA compatível com o `ctranslate2` instalado. Se não houver GPU disponível, a aplicação cai automaticamente para CPU.

**Modelo não carrega de pasta local**

Confirme que o diretório contém os arquivos do modelo (`.bin`, `config.json`, etc.). O caminho passado em `--model` deve ser o diretório raiz do modelo, não um arquivo individual.

**Vídeo não é processado**

Verifique `logs/last-run.log` (Linux) ou `logs\last-run.log` (Windows). O vídeo pode ter sido pulado por:

- Já estar em `data/processed_videos.json` com o `.md` existente → use `--reprocess`
- Arquivo ainda em gravação → aguarde e execute novamente
- Erro na transcrição → verifique o log para detalhes

### Linux Específico

**ffmpeg não encontrado**

Instale `ffmpeg` usando o gerenciador de pacotes da sua distribuição:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# Fedora/RHEL
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

**CUDA não disponível no Linux**

A aplicação detecta automaticamente se CUDA está disponível. Se CUDA falhar durante a inicialização do modelo, a aplicação cai automaticamente para CPU (int8). Isso pode ser mais lento, mas funciona em qualquer máquina.

Para forçar CPU do início:

```bash
# Desabilitar CUDA (se necessário)
CUDA_VISIBLE_DEVICES="" uv run python -m video_to_text -d /path/to/videos
```

**CTranslate2 não compila**

O `ctranslate2` requer compilação em algumas distribuições Linux. Certifique-se de ter as ferramentas de build instaladas:

```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# Fedora/RHEL
sudo dnf install gcc gcc-c++ python3-devel
```

Em seguida, execute `uv sync` novamente.
