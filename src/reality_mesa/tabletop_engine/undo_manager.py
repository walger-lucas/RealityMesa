from .undo_command import UndoCommand

class UndoManager:
    def __init__(self) -> None:
        self.undo:list[UndoCommand] = []

    def AddUndo(self,undo:UndoCommand):
        self.undo.append(undo)
    
    def Undo(self):
        while len(self.undo)>0:
            undo = self.undo.pop()
            if undo.Undo():
                break

