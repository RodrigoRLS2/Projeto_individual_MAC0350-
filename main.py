from typing import List, Optional
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from sqlmodel import Field, Relationship, SQLModel, create_engine, Session, select, delete
import random
import json

# ==========================================
# 1. MODELOS DO BANCO DE DADOS
# ==========================================
class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(default="waiting") 
    winner_player_id: Optional[int] = Field(default=None)
    current_turn_player_id: Optional[int] = Field(default=None)

    players: List["Player"] = Relationship(back_populates="match")
    tiles: List["Tile"] = Relationship(back_populates="match")

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    match_id: Optional[int] = Field(default=None, foreign_key="match.id")
    match: Optional[Match] = Relationship(back_populates="players")
    tiles: List["Tile"] = Relationship(back_populates="player")

class Tile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    left_value: int
    right_value: int
    played: bool = Field(default=False)
    play_order: int = Field(default=0) 
    board_side: Optional[str] = Field(default=None) 
    
    match_id: Optional[int] = Field(default=None, foreign_key="match.id")
    player_id: Optional[int] = Field(default=None, foreign_key="player.id")
    
    match: Optional[Match] = Relationship(back_populates="tiles")
    player: Optional[Player] = Relationship(back_populates="tiles")

# ==========================================
# 2. CONFIGURAÇÃO
# ==========================================
sqlite_file_name = "domino.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# ==========================================
# 3. ROTAS DO JOGO
# ==========================================
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.post("/match/create", response_class=HTMLResponse)
def create_match(request: Request, playerName: str = Form(...)):
    with Session(engine) as session:
        new_match = Match(status="waiting")
        session.add(new_match)
        session.commit()
        session.refresh(new_match)
        
        new_player = Player(name=playerName, match_id=new_match.id)
        session.add(new_player)
        session.commit()
        session.refresh(new_player)
        
        new_match.current_turn_player_id = new_player.id
        session.add(new_match)
        
        all_tiles = []
        for left in range(7):
            for right in range(left, 7):
                tile = Tile(left_value=left, right_value=right, match_id=new_match.id)
                all_tiles.append(tile)
                
        random.shuffle(all_tiles)
        for i in range(7):
            all_tiles[i].player_id = new_player.id
            
        session.add_all(all_tiles)
        session.commit()
        
        player_hand = all_tiles[:7]
        return templates.TemplateResponse(request, "match.html", {
            "match": new_match, "player": new_player, "hand": player_hand
        })

@app.put("/match/play/{tile_id}", response_class=HTMLResponse)
def play_tile(request: Request, tile_id: int, side: Optional[str] = None):
    with Session(engine) as session:
        tile = session.get(Tile, tile_id)
        match = session.get(Match, tile.match_id)
        player = session.get(Player, tile.player_id)

        if match.current_turn_player_id != player.id:
            resp = Response(status_code=204)
            resp.headers["HX-Trigger"] = json.dumps({"showError": "Não é sua vez!"})
            return resp

        played_tiles = session.exec(
            select(Tile).where(Tile.match_id == tile.match_id, Tile.played == True).order_by(Tile.play_order.asc())
        ).all()
        
        board_tiles = []
        for t in played_tiles:
            if t.board_side == "left":
                board_tiles.insert(0, t)
            else:
                board_tiles.append(t)
                
        if len(board_tiles) > 0:
            left_endpoint = board_tiles[0].left_value
            right_endpoint = board_tiles[-1].right_value
            
            if side == "left":
                if tile.right_value == left_endpoint: pass
                elif tile.left_value == left_endpoint:
                    tile.left_value, tile.right_value = tile.right_value, tile.left_value
                else:
                    resp = Response(status_code=204)
                    resp.headers["HX-Trigger"] = json.dumps({"showError": "Esta peça não encaixa no lado ESQUERDO!"})
                    return resp
            elif side == "right":
                if tile.left_value == right_endpoint: pass
                elif tile.right_value == right_endpoint:
                    tile.left_value, tile.right_value = tile.right_value, tile.left_value
                else:
                    resp = Response(status_code=204)
                    resp.headers["HX-Trigger"] = json.dumps({"showError": "Esta peça não encaixa no lado DIREITO!"})
                    return resp

        max_order_tile = session.exec(select(Tile).where(Tile.match_id == tile.match_id).order_by(Tile.play_order.desc())).first()
        tile.played = True
        tile.play_order = (max_order_tile.play_order + 1) if max_order_tile else 1
        tile.board_side = side or "right"
        session.add(tile)
        session.commit()

        hand_tiles = session.exec(select(Tile).where(Tile.player_id == player.id, Tile.played == False)).all()
        if len(hand_tiles) == 0:
            match.status = "finished"
            match.winner_player_id = player.id
            session.add(match)
            session.commit()
            return get_game_status(request, session, match, player)

        other_player = session.exec(select(Player).where(Player.match_id == match.id, Player.id != player.id)).first()
        if other_player:
            match.current_turn_player_id = other_player.id
            session.add(match)
            session.commit()

        return get_game_status(request, session, match, player)

@app.get("/match/status/{match_id}/{player_id}", response_class=HTMLResponse)
def match_status(request: Request, match_id: int, player_id: int):
    with Session(engine) as session:
        match = session.get(Match, match_id)
        player = session.get(Player, player_id)
        return get_game_status(request, session, match, player)

@app.post("/match/draw/{player_id}", response_class=HTMLResponse)
def draw_tile(request: Request, player_id: int):
    with Session(engine) as session:
        player = session.get(Player, player_id)
        match = session.get(Match, player.match_id)

        if match.current_turn_player_id != player.id:
            resp = Response(status_code=204)
            resp.headers["HX-Trigger"] = json.dumps({"showError": "Não é sua vez!"})
            return resp

        available_tiles = session.exec(select(Tile).where(Tile.match_id == match.id, Tile.player_id == None)).all()
        if not available_tiles:
            resp = Response(status_code=204)
            resp.headers["HX-Trigger"] = json.dumps({"showError": "O monte está vazio!"})
            return resp

        drawn_tile = random.choice(available_tiles)
        drawn_tile.player_id = player.id
        session.add(drawn_tile)
        session.commit()
        return get_game_status(request, session, match, player)

@app.post("/match/pass/{player_id}", response_class=HTMLResponse)
def pass_turn(request: Request, player_id: int):
    with Session(engine) as session:
        player = session.get(Player, player_id)
        match = session.get(Match, player.match_id)

        if match.current_turn_player_id != player.id:
            resp = Response(status_code=204)
            resp.headers["HX-Trigger"] = json.dumps({"showError": "Não é sua vez!"})
            return resp

        other_player = session.exec(select(Player).where(Player.match_id == match.id, Player.id != player.id)).first()
        if other_player:
            match.current_turn_player_id = other_player.id
            session.add(match)
            session.commit()

        return get_game_status(request, session, match, player)

@app.get("/matches", response_class=HTMLResponse)
def list_matches(request: Request, search_id: Optional[str] = None):
    with Session(engine) as session:
        query = select(Match).where(Match.status == "waiting")
        
        # Se o usuário digitou algo e é um número, aplica o filtro. 
        # Se ele apagou tudo, cai fora do if e traz a lista original completa.
        if search_id and search_id.strip().isdigit():
            query = query.where(Match.id == int(search_id.strip()))
        
        matches = session.exec(query.order_by(Match.id.desc())).all()
        
        # O pulo do gato: devolvemos o 'search_id' para o HTML não esquecer o que estava lá
        return templates.TemplateResponse(request, "lobby.html", {
            "matches": matches, 
            "search_id": search_id if search_id else ""
        })

@app.post("/match/join/{match_id}", response_class=HTMLResponse)
def join_match(request: Request, match_id: int, playerName: str = Form(...)):
    with Session(engine) as session:
        match = session.get(Match, match_id)
        if not match or match.status != "waiting":
            return HTMLResponse("<p>Partida não disponível.</p>")

        new_player = Player(name=playerName, match_id=match.id)
        session.add(new_player)
        session.commit()
        session.refresh(new_player)

        match.status = "playing"
        session.add(match)

        available_tiles = session.exec(select(Tile).where(Tile.match_id == match.id, Tile.player_id == None)).all()
        random.shuffle(available_tiles)
        for i in range(7):
            available_tiles[i].player_id = new_player.id
            session.add(available_tiles[i])
        session.commit()
        
        hand = session.exec(select(Tile).where(Tile.player_id == new_player.id)).all()
        return templates.TemplateResponse(request, "match.html", {
            "match": match, "player": new_player, "hand": hand
        })

@app.delete("/match/delete/{match_id}", response_class=HTMLResponse)
def delete_match(request: Request, match_id: int):
    with Session(engine) as session:
        match = session.get(Match, match_id)
        if match:
            session.exec(delete(Tile).where(Tile.match_id == match_id))
            session.exec(delete(Player).where(Player.match_id == match_id))
            session.delete(match)
            session.commit()
        matches = session.exec(select(Match).where(Match.status == "waiting").order_by(Match.id.desc())).all()
        return templates.TemplateResponse(request, "lobby.html", {"matches": matches})

def get_game_status(request, session, match, player):
    if match.status == "finished":
        winner = session.get(Player, match.winner_player_id)
        return templates.TemplateResponse(request, "game_over.html", {"player": player, "winner": winner})
        
    played_tiles = session.exec(select(Tile).where(Tile.match_id == match.id, Tile.played == True).order_by(Tile.play_order.asc())).all()
    
    board_tiles = []
    for t in played_tiles:
        if t.board_side == "left": board_tiles.insert(0, t)
        else: board_tiles.append(t)
            
    hand = session.exec(select(Tile).where(Tile.player_id == player.id, Tile.played == False)).all()
    turn_player = session.get(Player, match.current_turn_player_id)
    is_my_turn = (match.current_turn_player_id == player.id)

    return templates.TemplateResponse(request, "play_update.html", {
        "match": match, "player": player, "board_tiles": board_tiles, "hand": hand,
        "is_my_turn": is_my_turn, "turn_name": turn_player.name if turn_player else "Aguardando..."
    })