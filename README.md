# Projeto_individual_MAC0350-

Desenvolvimento de um aplicativo web multiplayer de dominó onde dois jogadores podem participar da mesma partida online.

O sistema permitirá que cada jogador veja apenas suas próprias peças enquanto ambos visualizam o tabuleiro compartilhado. O foco do projeto não é validar todas as regras do dominó, mas sim demonstrar a integração entre backend, banco de dados e interface dinâmica utilizando HTMX.

O tabuleiro será atualizado dinamicamente conforme as jogadas forem realizadas.

Prototipo inicial (Criado com ajuda de LLM, arquitetura não definida ainda):

* Criar uma nova partida
* Entrar em uma partida existente
* Gerar automaticamente as **28 peças de dominó**
* Distribuir **7 peças para cada jogador**
* Permitir que jogadores coloquem peças no tabuleiro
* Atualizar o tabuleiro automaticamente usando **HTMX**
* Botão para **desfazer a última jogada**
* Botão para **declarar vencedor**

### Tela Inicial

Permite que o usuário:

* Crie uma nova partida
* Entre em uma partida existente informando seu nome

### Tela da Partida

Nesta tela o jogador poderá:

* Visualizar o tabuleiro
* Ver suas próprias peças
* Jogar peças
* Desfazer a última jogada
* Declarar o vencedor

A interface será **responsiva**, permitindo o uso tanto em computadores quanto em dispositivos móveis.

---

## Modelos do Banco de Dados

O sistema utilizará três modelos principais no banco de dados.

### Match

Representa uma partida de dominó.

Campos:

* `id`
* `status`
* `winner_player_id`

### Player

Representa um jogador dentro de uma partida.

Campos:

* `id`
* `name`
* `match_id`

### Tile

Representa uma peça de dominó.

Campos:

* `id`
* `left_value`
* `right_value`
* `player_id`
* `match_id`
* `played`

---

## Operações CRUD com HTMX

O projeto utilizará **HTMX** para realizar operações CRUD diretamente na interface.

Serão utilizados os seguintes métodos:

* `hx-get` – carregar dados dinamicamente
* `hx-post` – criar registros
* `hx-put` – atualizar registros
* `hx-delete` – remover registros

Essas operações permitirão atualizar partes da página sem necessidade de recarregamento completo.

---

## Objetivo Acadêmico

O principal objetivo do projeto é demonstrar o uso integrado de:

* FastAPI como backend
* SQLAlchemy para persistência de dados
* HTMX para interação dinâmica no frontend

O projeto busca implementar um exemplo simples de aplicação web interativa utilizando tecnologias modernas de desenvolvimento web.
