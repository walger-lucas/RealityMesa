from .tabletop import Tabletop
from .token import Token
from reality_mesa.rendering.camera import Camera
import json
import pygame
import os
import random
from .point_of_interest import PointOfInterest

def resolve_path(path: str, base_file: str) -> str:
    if os.path.isabs(path):
        return path
    
    base_dir = os.path.dirname(os.path.abspath(base_file))
    return os.path.normpath(os.path.join(base_dir, path))

def load_image_alpha(path: str, image_folder: str) -> pygame.Surface | None:
    if not path:
        return None

    # Resolve path
    if not os.path.isabs(path):
        path = os.path.join(image_folder, path)

    # Load with transparency
    image = pygame.image.load(path).convert_alpha()
    return image

def load_tt_image(tt_image_path: str | None, image_folder: str, bg_color=None) -> pygame.Surface | None:
    if not tt_image_path:
        return None

    # Resolve path
    if not os.path.isabs(tt_image_path):
        tt_image_path = os.path.join(image_folder, tt_image_path)

    # Load image
    image = pygame.image.load(tt_image_path)

    # Handle transparency
    if image.get_alpha() is not None:
        # Image has per-pixel alpha
        image = image.convert_alpha()

        if bg_color is not None:
            # Apply background color behind transparent pixels
            bg = pygame.Surface(image.get_size())
            bg.fill(bg_color)
            bg.blit(image, (0, 0))
            image = bg.convert()
    else:
        # No alpha → faster conversion
        image = image.convert()

    return image

def tabletop_read(tt_queue,ctx_queue,file):
    with open(file, "r", encoding="utf-8") as f:
        data:dict = json.load(f)
    if not data:
        data = {}

    image_folder = data.pop("image_folder", ".")
    image_folder = resolve_path(image_folder, file)

    size:tuple[int,int] = tuple(data.pop("size",(10,10)))
    tt_image_path:str|None = data.pop("img",None)
    unit:str = data.pop("unit","m")
    unit_size:float = data.pop("unit_size",1.5)

    display_id:int = data.pop("display_id",0)

    width, height = pygame.display.get_desktop_sizes()[display_id]
    screen = pygame.display.set_mode(
        (width, height),
        pygame.NOFRAME,
        display=display_id
    )
    cam  = Camera((width, height),int(min(width//size[0],height//size[1])*0.8))
    cam.pos =  pygame.Vector2(size[0]/2.0,size[1]/2.0)

    tt_image = load_tt_image(tt_image_path,image_folder,(200,200,200))
    if not tt_image:
        tt_image= pygame.Surface(pygame.Vector2(1000,1000))
        tt_image.fill((200,200,200))

    cam_config:dict = data.pop("cam_config",{})

    

    tt = Tabletop(tt_queue,ctx_queue,tt_image,size,unit,unit_size,cam_config)

    tokens:list[dict] = data.pop("tokens",[])
    for tok in tokens:
        size_tok = pygame.Vector2(tok.pop("size",(1,1)))
        pos = pygame.Vector2(tok.pop("pos",(random.randint(0,size[0]),random.randint(0,size[1]))))
        token_img = load_image_alpha(tok.pop("img",None),image_folder)
        description = tok.pop("description","")
        if not token_img:
            token_img = pygame.Surface(pygame.Vector2(50,50))
            token_img.fill((255,0,0))
        token = Token(description,pos,size_tok,token_img)
        tt.AddObject(token)

    pois:list[dict] = data.pop("poi",[])
    for poi in pois:
        pos = pygame.Vector2(poi.pop("pos",(random.randint(0,size[0]),random.randint(0,size[1]))))
        description = poi.pop("description","")
        p = PointOfInterest(pos,description)
        tt.AddObject(p)
    
    
    
    return tt, cam, screen