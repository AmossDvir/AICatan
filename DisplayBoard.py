import tkinter
import pprint
import logging
import argparse
from catan.board import Board
from catan.game import Game

import views


class CatanSpectator(tkinter.Frame):

    def __init__(self, board):
        super(CatanSpectator, self).__init__()
        self.game = Game(board=board)
        self.game.observers.add(self)
        self._in_game = self.game.state.is_in_game()

        self._board_frame = views.BoardFrame(self, self.game)
        self._log_frame = views.LogFrame(self, self.game)
        self._board_frame.grid(row=0, column=0, sticky=tkinter.NSEW)
        self._log_frame.grid(row=1, column=0, sticky=tkinter.W)

        self._board_frame.redraw()

        self._setup_game_toolbar_frame = views.SetupGameToolbarFrame(self, self.game)
        self._toolbar_frame = self._setup_game_toolbar_frame
        self._toolbar_frame.grid(row=0, column=1, rowspan=2, sticky=tkinter.N)

        self.lift()

    def notify(self, observable):
        was_in_game = self._in_game
        self._in_game = self.game.state.is_in_game()
        if was_in_game and not self.game.state.is_in_game():
            logging.debug('we were in game, NOW WE\'RE NOT')
            self._toolbar_frame.grid_forget()
            self._toolbar_frame = self._setup_game_toolbar_frame
            self._toolbar_frame.grid(row=0, column=1, rowspan=2, sticky=tkinter.N)
        elif not was_in_game and self.game.state.is_in_game():
            logging.debug('we were not in game, NOW WE ARE')
            self._toolbar_frame.grid_forget()
            self._toolbar_frame = views.GameToolbarFrame(self, self.game)
            self._toolbar_frame.grid(row=0, column=1, rowspan=2, sticky=tkinter.N)

    def setup_options(self):
        return self._setup_game_toolbar_frame.options.copy()


def display_board(board):
    app = CatanSpectator(board=board)
    app.mainloop()