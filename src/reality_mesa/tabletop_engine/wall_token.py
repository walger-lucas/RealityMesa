from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.infra import send_command, Command
from reality_mesa.nlp.context_manager.context_commands import RemoveToken, AddTriples
from pygame import Surface, Vector2
from .token import Token, TabletopObject
from .point_of_interest import PointOfInterest
from reality_mesa.rendering import Camera
from dataclasses import dataclass
from .tt_commands import UndoTokenCreate
if TYPE_CHECKING:
    from .token_manager import TokenManager
    from .tabletop import Tabletop


class WallTokenBorder(Token):
    def __init__(self, pos: Vector2, depth: int = 0):
        super().__init__("",pos,Vector2(1,1),None,depth+1)
    def Start(self):
        if self.tabletop:
            tok_manager = self.tabletop.GetTokenManager()
            tok_manager.AddToken(self)

    def Remove(self):
        if self.tabletop:
            tok_manager = self.tabletop.GetTokenManager()
            tok_manager.RemoveToken(self.id)
            
            
class WallToken(PointOfInterest):
    def __init__(self, pos_start: Vector2,pos_end:Vector2, triple_type: WallType,description:str="Muralha"):
        super().__init__((pos_start+pos_end)/2, description)
        self.start = WallTokenBorder(pos_start)
        self.end = WallTokenBorder(pos_end)
        self.triple_type = triple_type


    def Start(self):
        if self.tabletop:
            tok_manager = self.tabletop.GetTokenManager()
            tok_manager.AddPOI(self)
            self.tabletop.AddObject(self.start)
            self.tabletop.AddObject(self.end)
            tok_start_name = f"border{self.start.id}"
            tok_end_name = f"border{self.end.id}"
            wall_name = f"wall{self.id}"
            triples = self.triple_type.GetTriples(wall_name,tok_start_name,tok_end_name)
            send_command(self.tabletop.ctx_queue,
                         AddTriples(self.id,wall_name,triples[0]))
            send_command(self.tabletop.ctx_queue,
                         AddTriples(self.start.id,tok_start_name,triples[1]))
            send_command(self.tabletop.ctx_queue,
                         AddTriples(self.end.id,tok_end_name,triples[2]))

    def Update(self):
        if (self.tabletop 
            and (tman :=self.tabletop.GetTokenManager()) 
            and (tman.GetToken(self.start.id) is None 
                 or tman.GetToken(self.end.id) is None)):
                self.tabletop.RemoveObject(self.id)
                self.pos = (self.start.pos+self.end.pos)/2

    def Remove(self):
        if self.tabletop:
            self.tabletop.RemoveObject(self.start.id)
            self.tabletop.RemoveObject(self.end.id)
            tok_manager = self.tabletop.GetTokenManager()
            tok_manager.RemovePOI(self.id)
            send_command(self.tabletop.ctx_queue,
                         RemoveToken(self.id))
            send_command(self.tabletop.ctx_queue,
                         RemoveToken(self.end.id))
            send_command(self.tabletop.ctx_queue,
                         RemoveToken(self.start.id))

    def DrawUnderlay(self, surface: Surface, camera: Camera):
        camera.DrawWorldArrow(surface,
                              self.triple_type.COLOR,
                              self.start.pos,
                              self.end.pos,
                              max(1,int(camera.pixels_per_unit*camera.zoom*self.triple_type.WIDTH)),
                              0,
                              0)
        
    def Draw(self, surface: Surface, camera: Camera):
        camera.DrawWorldElipse(surface,self.start.pos,Vector2(1,1),0,self.triple_type.COLOR)
        camera.DrawWorldElipse(surface,self.end.pos,Vector2(1,1),0,self.triple_type.COLOR)

_BASE_WALL_TRIPLES = """({wall};ser;"muralha")\n
                        ({wall};ser;"muro")\n"""

_BASE_WALL_START_BORDER_TRIPLES = """({tok_start};ser;"borda inicial de muralha")\n
({tok_start};ser; "local/ponto inicial de muralha")\n
({tok_start},ser borda inicial de;{wall})|"ser borda inicial de uma muralha"|\n
({tok_start},fazer reta com;{tok_end})|"o começo ao fim de uma reta ou linha"|\n"""

_BASE_WALL_END_BORDER_TRIPLES = """({tok_end};ser;"borda final de muralha")\n
({tok_end};ser; "local/ponto inicial de muralha")\n
({tok_end},ser borda final de;{wall})|"ser borda final de uma muralha"|\n
({tok_end},fazer reta com;{tok_start})|"o fim ao começo de uma reta ou linha"|\n"""

@dataclass
class WallType:
    MATERIALS:list[str]
    COLOR:tuple
    WIDTH:float = 0.75

    def GetTriples(self,wall_tok:str,border_start_tok:str,border_end_tok:str):
        made_of_triples:str = ""
        for m in self.MATERIALS:
            made_of_triples += "({tok};ser feito de; \""+m+"\")\n"

        start_triples:str = (_BASE_WALL_START_BORDER_TRIPLES+made_of_triples).format(tok=border_start_tok,
                                                                                 tok_start=border_start_tok,
                                                                                 tok_end=border_end_tok,
                                                                                 wall=wall_tok)
        end_triples:str = (_BASE_WALL_END_BORDER_TRIPLES+made_of_triples).format(tok=border_end_tok,
                                                                                 tok_start=border_start_tok,
                                                                                 tok_end=border_end_tok,
                                                                                 wall=wall_tok)
        wall_triples:str = (_BASE_WALL_TRIPLES+made_of_triples).format(tok=wall_tok,
                                                                    tok_start=border_start_tok,
                                                                    tok_end=border_end_tok,
                                                                    wall=wall_tok)
        return wall_triples,start_triples,end_triples


wallTypeRegistry = {
    "fogo": WallType(["fogo","flamejante"],(217,118,49),0.6),
    "gelo": WallType(["gelo","congelante","congelada"],(116,148,167),0.9),
    "pedra": WallType(["pedra"],(167,167,167),0.95)
}

class CreateWall(Command["Tabletop"]):
    def __init__(self,type:str) -> None:
        super().__init__()
        self.type = type

    def execute(self, input: "Tabletop"):
        if self.type not in wallTypeRegistry:
            return
        
        focus = input.GetPointerManager().GetFocus()
        if focus is None or focus.point_start is None:
            return
        tok = WallToken(focus.point_start,focus.point_end,wallTypeRegistry[self.type])
        input.AddObject(tok)
        input.undo_manager.AddUndo(UndoTokenCreate(input,tok.id))