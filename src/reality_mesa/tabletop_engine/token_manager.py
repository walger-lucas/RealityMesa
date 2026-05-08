from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.tabletop_engine.token import Token
from reality_mesa.tabletop_engine.point_of_interest import PointOfInterest
import pygame
import math
from collections import deque
if TYPE_CHECKING:
    from .tabletop import Tabletop

class TokenManager:
    def __init__(self,tabletop:Tabletop):
        self._tokens: dict[int,Token] = {}
        self.tabletop = tabletop
        self._pick_token:dict[int,int] = {} #picker_id to token
        self._pick_token_inverse: dict[int,int] = {} #token to picker_id
        self._pois: dict[int, PointOfInterest] = {}

    def AddToken(self,token:Token):
        if token.id not in self._tokens:
            self._tokens[token.id] = token

    def RemoveToken(self,token_id:int):
        if token_id in self._tokens:
            self._tokens.pop(token_id)

    def AddPOI(self,poi:PointOfInterest):
        if poi.id not in self._pois:
            self._pois[poi.id] = poi

    def RemovePOI(self,poi_id:int):
        if poi_id in self._pois:
            self._pois.pop(poi_id)
    
    def GetToken(self,token_id:int):
        if token_id in self._tokens:
            return self._tokens[token_id]
        else:
            return None
        
    def GetPOI(self,poi_id:int):
        if poi_id in self._pois:
            return self._pois[poi_id]
        else:
            return None
    
    def HitRect(self,rect:pygame.FRect,disconsider:list[int]|None = None):
        if disconsider == None:
            disconsider = []
        out: Token | None = None
        for tok in self._tokens.values():
            if  (out is None or out.depth < tok.depth) and tok.HitRect(rect) and tok.id not in disconsider:
                out = tok
        return out
    
    def HitPointAll(self,pt:pygame.Vector2,disconsider:list[int]|None = None):
        hit:list[Token] = []
        if disconsider == None:
            disconsider = []
        for tok in self._tokens.values():
            if  tok.HitPoint(pt) and tok.id not in disconsider:
                hit.append(tok)
        return hit
    
    def AllNear(self,pt:pygame.Vector2,max_distance:float,disconsider:list[int]|None = None):
        hit:list[Token|PointOfInterest] = []
        if disconsider == None:
            disconsider = []
        for tok in self._tokens.values():
            if (tok.pos - pt).length() < max_distance and tok.id not in disconsider:
                hit.append(tok)

        for poi in self._pois.values():
            if (poi.pos - pt).length() < max_distance and poi.id not in disconsider:
                hit.append(poi)
        return hit
    
    def TokenNear(self,pt:pygame.Vector2,max_distance:float,disconsider:list[int]|None = None):
        hit:list[Token] = []
        if disconsider == None:
            disconsider = []
        for tok in self._tokens.values():
            if (tok.pos - pt).length() < max_distance and tok.id not in disconsider:
                hit.append(tok)
        return hit
    
    def HitPoint(self,pt:pygame.Vector2,disconsider:list[int]|None = None):
        if disconsider == None:
            disconsider = []
        out: Token | None = None
        for tok in self._tokens.values():
            if  (out is None or out.depth < tok.depth) and tok.HitPoint(pt) and tok.id not in disconsider:
                out = tok
        return out
    
    def FindEmpty(self,org:pygame.Vector2,dest:pygame.Vector2,size:pygame.Vector2,size_dest:pygame.Vector2 = pygame.Vector2(1,1),disconsider:list[int] | None=None):
        #find direction between origin and destination
        if dest == org:
            direc = 0
        else:
            direc = math.atan2(org[1]-dest[1],org[0]-dest[0]) + math.pi

        if disconsider == None:
            disconsider = []

        #find offset to start find
        direc_offsets = [pygame.Vector2(-1,0),pygame.Vector2(-1,-1),pygame.Vector2(0,-1),pygame.Vector2(1,-1),pygame.Vector2(1,0),pygame.Vector2(1,1),pygame.Vector2(0,1),pygame.Vector2(-1,1)]
        ord_start = math.floor(len(direc_offsets)*(direc/(2*math.pi)))%len(direc_offsets)
        offset = direc_offsets[ord_start]

        #correct alignment
        off_in_x, off_in_y = (False,False)
        if (math.ceil(size[0]+size_dest[0]))%2 == 1:
            off_in_x = True
        if (math.ceil(size[1]+size_dest[1]))%2 == 1:
            off_in_y = True
        dest = pygame.Vector2(dest[0]+offset[0]*0.5 if  off_in_x else dest[0],
                dest[1]+offset[1]*0.5 if off_in_y else dest[1])
        
        #sort search by the given start direction
        direc_offsets.sort(key=lambda d: math.dist(offset,d))

        #BFS
        cur_pos = dest
        to_process:deque[pygame.Vector2] = deque()
        to_process.append(dest)
        found = {}

        while((cur_pos-dest).length()<(max(size_dest)+max(size))+5):
            cur_pos = to_process.popleft()
            found[(cur_pos.x,cur_pos.y)] = True
            rect = pygame.FRect(cur_pos-size/2,size)
            if self.HitRect(rect,disconsider) == None:
                return cur_pos
            for d in direc_offsets:
                next_pos = pygame.Vector2(cur_pos[0]+d[0],cur_pos[1]+d[1])
                if (next_pos.x,next_pos.y) not in found:
                    to_process.append(next_pos)

    def PickToken(self,picker_id: int,position:pygame.Vector2):
        if not self.tabletop.last_camera:
            return
        pos = self.tabletop.last_camera.Screen2World(position)
        if picker_id in self._pick_token:
            return
        
        out = self.HitPoint(pos)
        if out is None:
            close = self.TokenNear(pos,1.5)
            if(len(close)==0):
                return
            close.sort(key= lambda key: (key.pos-pos).length())
            out = close[0]

        if out.id in self._pick_token_inverse.keys():
            return
        self._pick_token_inverse[out.id] = picker_id
        self._pick_token[picker_id] = out.id

    def PickUpdate(self,picker_id: int,position:pygame.Vector2):
        if not self.tabletop.last_camera:
            return
        pos = self.tabletop.last_camera.Screen2World(position)
        if picker_id not in self._pick_token:
            return
        tok_id = self._pick_token[picker_id]
        if tok_id in self._tokens:
            tok = self._tokens[tok_id]
            tok.Move(pos,False,False)

    def UnpickToken(self,picker_id: int,position:pygame.Vector2):
        if not self.tabletop.last_camera:
            return
        pos = self.tabletop.last_camera.Screen2World(position)
        if picker_id not in self._pick_token:
            return
        tok_id = self._pick_token.pop(picker_id)
        self._pick_token_inverse.pop(tok_id,None)
        if tok_id in self._tokens:
            tok = self._tokens[tok_id]
            tok.Move(pos,True,False)

    