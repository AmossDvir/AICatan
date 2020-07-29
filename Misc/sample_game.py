from catan.game import Game
from catan.board import Board
from catan.board import Port
from catan.board import PortType
from catan.game import Player
from DisplayBoard import display_board

INITIAL_BOARD = "w w w w s s s s h h h h o o o b b b d 2 3 3 4 4 5 5 6 6 8 8 9 9 10 10 11 11 12 None"
PORTS = [Port(1,'NW',PortType.any3), Port(2,'W',PortType.ore), Port(4,'W',PortType.brick),
            Port(5,'SW',PortType.any3), Port(6,'SE',PortType.any3), Port(8,'SE',PortType.sheep),
            Port(9,'E',PortType.any3), Port(10,'NE',PortType.wood), Port(12,'Ne',PortType.wheat)]

def sample_game():
    board = Board(board=INITIAL_BOARD)
    board.set_ports(PORTS)
    game = Game(board=board)    
    game.start([Player(1, 'Boaz', 'blue')])
    print(game.get_cur_player())  # -> ross (red)
    game.buy_settlement(0x37)
    game.buy_road(0x37)
    game.end_turn()
    display_board(board)


if __name__ == "__main__":
    sample_game()
