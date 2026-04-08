Funcionalidades Principais:
- Criacao de Partidas: Geracao automatica do banco de dados, embaralhamento das 28 pecas e distribuicao inicial.
- Lobby e Busca em Tempo Real: Filtro de mesas por ID utilizando requisicoes GET via HTMX enquanto o usuario digita.
- Multiplayer Assincrono: Sincronizacao da mesa e das maos dos jogadores atraves de short polling (a cada 2 segundos) acionado por HTMX
- CRUD Completo: Implementacao das operacoes fundamentais (Create, Read, Update, Delete) com exclusao em cascata (Partidas -> Jogadores -> Pecas).

Como Executar o Projeto

1. Pre-requisitos:
Certifique-se de ter o Python 3.8 ou superior instalado em sua maquina.

2. Instalar Dependencias:
Instale os pacotes necessarios executando:
pip install fastapi[standard] sqlmodel jinja2

3. Iniciar o Servidor:
 python -m uvicorn main:app --reload ou  py -m fastapi dev main.py

(Para testar o multiplayer localmente, abra uma janela normal e uma janela anonima, ou dois navegadores diferentes simultaneamente).

Estrutura do Projeto

- main.py: Nucleo do back-end, contendo a configuracao do FastAPI, os modelos do SQLModel e todos os endpoints e rotas de logica do jogo.
- templates/: Diretorio contendo as visualizacoes do Jinja2.
  - index.html: Tela inicial e menu principal.
  - lobby.html: Tela de busca e listagem de partidas abertas.
  - match.html: Interface principal do jogo (tabuleiro e pecas do jogador).
  - play_update.html: Fragmento de HTML usado pelo HTMX para atualizar a mesa.
  - game_over.html: Tela de encerramento e declaracao do vencedor.
- domino.db: Arquivo gerado automaticamente pelo banco de dados SQLite.

Nota: A redacao e formatacao base deste arquivo foram geradas com o auxilio de Inteligencia Artificial.
