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