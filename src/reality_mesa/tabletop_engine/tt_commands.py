from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tabletop import Tabletop,PointerCtx
from reality_mesa.infra import Command, FutureCommand
from .pointer import Pointer

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

class LineCommand(Command["Tabletop"]):
    def __init__(self, start_id:int|pygame.Vector2, end_id: int|pygame.Vector2):
        super().__init__()
        self.start_id = start_id
        self.end_id = end_id
    def execute(self, input: Tabletop):
        tok_man = input.GetTokenManager()
        if tok_man is None:
            return
        if isinstance(self.end_id,pygame.Vector2):
            end_pos = self.end_id
        elif (tok := tok_man.GetToken(self.end_id)) is not None:
            end_pos = tok.pos
        elif (poi := tok_man.GetPOI(self.end_id)) is not None:
            end_pos = poi.pos
        else:
            return
        if isinstance(self.start_id,pygame.Vector2):
            start_pos = self.start_id
        elif (tok := tok_man.GetToken(self.start_id)) is not None:
            start_pos = tok.pos
        elif (poi := tok_man.GetPOI(self.start_id)) is not None:
            start_pos = poi.pos
        else:
            return
        
        if start_pos!=end_pos:
            point = Pointer(end_pos,start_pos)
        else:
            point = Pointer(end_pos,None)
        input.AddObject(point)
        input.undo_manager.AddUndo(UndoPointing(input,point.id))
        point.StartEndPointer(15)
        

class UndoTabletopCommand(Command["Tabletop"]):
    def execute(self, input: "Tabletop"):
        input.undo_manager.Undo()

from .undo_command import UndoCommand

class UndoMovement(UndoCommand):
    def __init__(self,tabletop:"Tabletop",tok_id:int,pos:pygame.Vector2):
        self.tt = tabletop
        self.tok_id = tok_id
        self.pos = pos

    def Undo(self) -> bool:
        tok_man = self.tt.GetTokenManager()
        if tok_man is None:
            return False
        tok = tok_man.GetToken(self.tok_id)
        if tok is None:
            return False
        
        tok.Move(self.pos,True,True,False)
        return True

class UndoPointing(UndoCommand):
    def __init__(self,tabletop:"Tabletop",point_id:int):
        self.tt = tabletop
        self.point_id = point_id

    def Undo(self) -> bool:
        ptr_man = self.tt.GetPointerManager()
        if ptr_man is None:
            return False
        ptr = ptr_man.GetPointer(self.point_id)
        if ptr is None:
            return False
        self.tt.RemoveObject(ptr.id)
        return True

class UndoTokenCreate(UndoCommand):
    def __init__(self,tabletop:"Tabletop",id:int):
        self.tt = tabletop
        self.id = id

    def Undo(self) -> bool:
        if self.tt.GetObject(self.id) is None:
            return False
        self.tt.RemoveObject(self.id)
        return True
    
