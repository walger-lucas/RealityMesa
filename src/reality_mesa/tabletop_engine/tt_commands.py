from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tabletop import Tabletop,PointerCtx
from reality_mesa.infra import Command, FutureCommand

class VisionStarted(Command["Tabletop"]):
    def __init__(self) -> None:
        super().__init__()
    def execute(self, input: Tabletop):
        print("[CALIBRATE PLZ]")
        input.Calibrate()

class GetPointerCtx(FutureCommand["Tabletop","PointerCtx|None"]):
    def __init__(self, max_near:int = 6, norm_distance:float = 2.0,max_distance = 8.0):
        super().__init__()
        self.max_near = max_near
        self.norm_distance = norm_distance
        self.max_distance = max_distance

    def _run(self, input: Tabletop) -> None | PointerCtx:
        return input.GetPointerCtx(self.max_near,self.norm_distance,self.max_distance)
    

import pygame
class MoveCommand(Command["Tabletop"]):
    def __init__(self, target_id:int, pos_id: int|pygame.Vector2):
        super().__init__()
        self.target_id = target_id
        self.pos_id = pos_id
    def execute(self, input: Tabletop):
        tok_man = input.GetTokenManager()
        if tok_man is None:
            return
        if isinstance(self.pos_id,pygame.Vector2):
            end_pos = self.pos_id
        elif (tok := tok_man.GetToken(self.pos_id)) is not None:
            end_pos = tok.pos
        elif (poi := tok_man.GetPOI(self.pos_id)) is not None:
            end_pos = poi.pos
        else:
            return
        
        if (tok := tok_man.GetToken(self.target_id)) is not None:
            move_tok = tok
        else:
            return
        
        move_tok.Move(end_pos,True,False)