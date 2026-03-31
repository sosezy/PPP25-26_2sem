
class Move:
    def __init__(self,piece,start,end,captured=None):
        self.piece=piece
        self.start=start
        self.end=end
        self.captured=captured

class Piece:
    def __init__(self,color,row,col):
        self.color=color
        self.row=row
        self.col=col
    def symbol(self): return "?"
    def get_moves(self,board): return []

# ------------------- Фигуры -------------------

class Pawn(Piece):
    def symbol(self): return "БП" if self.color=="white" else "ЧП"
    def get_moves(self,board):
        moves=[]; direction=-1 if self.color=="white" else 1
        r1=self.row+direction
        if board.inside(r1,self.col) and board.empty(r1,self.col):
            moves.append((r1,self.col))
            start_row=6 if self.color=="white" else 1
            r2=self.row+2*direction
            if self.row==start_row and board.empty(r2,self.col):
                moves.append((r2,self.col))
        for dc in [-1,1]:
            r=self.row+direction;c=self.col+dc
            if board.inside(r,c) and board.enemy(r,c,self.color):
                moves.append((r,c))
        return moves

class Rook(Piece):
    def symbol(self): return "БЛ" if self.color=="white" else "ЧЛ"
    def get_moves(self,board):
        moves=[]; directions=[(1,0),(-1,0),(0,1),(0,-1)]
        for dr,dc in directions:
            r,c=self.row,self.col
            while True:
                r+=dr;c+=dc
                if not board.inside(r,c): break
                if board.empty(r,c): moves.append((r,c))
                elif board.enemy(r,c,self.color): moves.append((r,c)); break
                else: break
        return moves

class Knight(Piece):
    def symbol(self): return "БК" if self.color=="white" else "ЧК"
    def get_moves(self,board):
        moves=[]; steps=[(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
        for dr,dc in steps:
            r=self.row+dr;c=self.col+dc
            if board.inside(r,c) and not board.friend(r,c,self.color):
                moves.append((r,c))
        return moves

class Bishop(Piece):
    def symbol(self): return "БС" if self.color=="white" else "ЧС"
    def get_moves(self,board):
        moves=[]; directions=[(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr,dc in directions:
            r,c=self.row,self.col
            while True:
                r+=dr;c+=dc
                if not board.inside(r,c): break
                if board.empty(r,c): moves.append((r,c))
                elif board.enemy(r,c,self.color): moves.append((r,c)); break
                else: break
        return moves

class Queen(Piece):
    def symbol(self): return "БФ" if self.color=="white" else "ЧФ"
    def get_moves(self,board):
        moves=[]; directions=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr,dc in directions:
            r,c=self.row,self.col
            while True:
                r+=dr;c+=dc
                if not board.inside(r,c): break
                if board.empty(r,c): moves.append((r,c))
                elif board.enemy(r,c,self.color): moves.append((r,c)); break
                else: break
        return moves

class King(Piece):
    def symbol(self): return "БКр" if self.color=="white" else "ЧКр"
    def get_moves(self,board):
        moves=[]
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr==0 and dc==0: continue
                r=self.row+dr;c=self.col+dc
                if board.inside(r,c) and not board.friend(r,c,self.color):
                    moves.append((r,c))
        return moves

# ------------------- Новые фигуры -------------------

class H(Piece):
    """Лошадь: длинный конь"""
    def symbol(self): return "БЛш" if self.color=="white" else "ЧЛш"
    def get_moves(self,board):
        moves=[]; steps=[(3,1),(3,-1),(-3,1),(-3,-1),(1,3),(1,-3),(-1,3),(-1,-3)]
        for dr,dc in steps:
            r=self.row+dr;c=self.col+dc
            if board.inside(r,c) and not board.friend(r,c,self.color): moves.append((r,c))
        return moves

class RKN(Piece):
    """Ладья+Конь"""
    def symbol(self): return "БЛК" if self.color=="white" else "ЧЛК"
    def get_moves(self,board):
        return Rook.get_moves(self,board)+Knight.get_moves(self,board)

class BKN(Piece):
    """Слон+Конь"""
    def symbol(self): return "БСК" if self.color=="white" else "ЧСК"
    def get_moves(self,board):
        return Bishop.get_moves(self,board)+Knight.get_moves(self,board)

# ------------------- Доска -------------------

class Board:
    def __init__(self): self.grid=[[None]*8 for _ in range(8)]
    def inside(self,r,c): return 0<=r<8 and 0<=c<8
    def empty(self,r,c): return self.grid[r][c] is None
    def enemy(self,r,c,color): p=self.grid[r][c]; return p and p.color!=color
    def friend(self,r,c,color): p=self.grid[r][c]; return p and p.color==color
    def place(self,piece): self.grid[piece.row][piece.col]=piece

    def print(self,game=None):
        print("\nБ = белые | Ч = чёрные")
        for r in range(8):
            print(8-r,end=" ")
            for c in range(8):
                piece=self.grid[r][c]
                print(f"{piece.symbol():>3}" if piece else " --",end="")
            print()
        print("   a  b  c  d  e  f  g  h\n")
        if game:
            if game.is_checkmate(game.turn):
                print("МАТ! Победитель:", "Чёрные" if game.turn=="white" else "Белые")
            elif game.is_check(game.turn):
                print("ШАХ!")

# ------------------- Игра -------------------

class Game:
    def __init__(self):
        self.board=Board(); self.turn="white"; self.history=[]
        self.setup()

    def setup(self):
        for c in range(8):
            self.board.place(Pawn("white",6,c))
            self.board.place(Pawn("black",1,c))
        pieces=[Rook,H,BKN,Queen,King,BKN,H,Rook]
        for c in range(8):
            self.board.place(pieces[c]("white",7,c))
            self.board.place(pieces[c]("black",0,c))

    def parse(self,text):
        col=ord(text[0])-ord('a'); row=8-int(text[1]); return row,col

    def coord_to_text(self,r,c):
        return f"{chr(ord('a')+c)}{8-r}"

    def show_moves(self,pos):
        r,c=pos; piece=self.board.grid[r][c]
        if piece:
            moves=[]
            for mr,mc in piece.get_moves(self.board):
                moves.append(f"{self.coord_to_text(r,c)} {self.coord_to_text(mr,mc)}")
            print("Возможные ходы:", ", ".join(moves))
        else:
            print("Нет фигуры")

    def move(self,start,end):
        sr,sc=start; er,ec=end; piece=self.board.grid[sr][sc]
        if piece is None: print("Нет фигуры"); return
        if piece.color!=self.turn: print("Сейчас ход другого игрока"); return
        if (er,ec) not in piece.get_moves(self.board): print("Недопустимый ход"); return
        captured=self.board.grid[er][ec]
        self.history.append(Move(piece,start,end,captured))
        self.board.grid[sr][sc]=None; self.board.grid[er][ec]=piece
        piece.row,piece.col=er,ec
        if isinstance(piece,Pawn) and ((piece.color=="white" and er==0) or (piece.color=="black" and er==7)):
            print("Пешка превращена в Ферзя!"); self.board.grid[er][ec]=Queen(piece.color,er,ec)
        self.turn="black" if self.turn=="white" else "white"

    def back(self):
        if not self.history: print("Нет ходов для отката"); return
        move=self.history.pop(); sr,sc=move.start; er,ec=move.end; piece=move.piece
        self.board.grid[sr][sc]=piece; self.board.grid[er][ec]=move.captured
        piece.row,piece.col=sr,sc; self.turn=piece.color

    def is_check(self,color):
        king=None
        for r in range(8):
            for c in range(8):
                p=self.board.grid[r][c]
                if p and isinstance(p,King) and p.color==color: king=p
        for r in range(8):
            for c in range(8):
                p=self.board.grid[r][c]
                if p and p.color!=color and king:
                    if (king.row,king.col) in p.get_moves(self.board): return True
        return False

    def is_checkmate(self,color):
        if not self.is_check(color): return False
        for r in range(8):
            for c in range(8):
                p=self.board.grid[r][c]
                if p and p.color==color:
                    for move in p.get_moves(self.board):
                        sr,sc=p.row,p.col; er,ec=move
                        captured=self.board.grid[er][ec]
                        self.board.grid[er][ec]=p; self.board.grid[sr][sc]=None; p.row,p.col=er,ec
                        if not self.is_check(color):
                            self.board.grid[sr][sc]=p; self.board.grid[er][ec]=captured; p.row,p.col=sr,sc
                            return False
                        self.board.grid[sr][sc]=p; self.board.grid[er][ec]=captured; p.row,p.col=sr,sc
        return True

# ------------------- MAIN -------------------

def main():
    game=Game()
    while True:
        game.board.print(game)
        if game.is_checkmate(game.turn): break
        print("Ход:", "Белые" if game.turn=="white" else "Чёрные")
        cmd=input("Введите ход (например e2 e4), 'возможные ходы e2' или 'откат': ")
        if cmd=="откат": game.back(); continue
        if cmd.startswith("возможные ходы"):
            pos = cmd.split()[-1] 
            game.show_moves(game.parse(pos))
            continue
        try:
            s,e=cmd.split(); game.move(game.parse(s),game.parse(e))
        except: print("Ошибка ввода")

if __name__=="__main__":
    main()
