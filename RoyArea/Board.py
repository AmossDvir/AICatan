import hexgrid
import GameConstants as Consts
from random import shuffle
from typing import List, Dict
from HexTile import HexTile
from Hand import Hand
from Buildables import Buildable


class Board:
    def __init__(self):
        self.__init_hexes()
        self.__nodes = dict()
        self.__edges = dict()

    def __init_hexes(self) -> None:
        deck = Consts.HEX_DECK.copy()
        shuffle(deck)
        # use id that is 1 less than the pic @ https://github.com/rosshamish/hexgrid/, 0-indexing.
        self.__hexes = []
        curr_token_id = 0
        robber_placed = False  # this is added for cases where multiple deserts exist, place robber in first only
        for hex_id in range(Consts.NUM_HEXES):
            resource = deck[hex_id]
            if resource == Consts.ResourceType.DESERT and not robber_placed:  # desert hex
                token = 0
                has_robber = True
                robber_placed = True
            else:
                token = Consts.TOKEN_ORDER[curr_token_id]
                has_robber = False
                curr_token_id += 1

            self.__hexes.append(HexTile(hex_id, resource, token, has_robber))

    def hexes(self) -> List[HexTile]:
        return self.__hexes

    def nodes(self) -> Dict[int, Buildable]:
        return self.__nodes

    def edges(self) -> Dict[int, Buildable]:
        return self.__edges

    def robber_hex(self) -> HexTile:
        for hex_tile in self.hexes():
            if hex_tile.has_robber():
                return hex_tile

    def move_robber_to(self, hex_id: int) -> None:
        self.robber_hex().set_robber(False)
        self.hexes()[hex_id].set_robber(True)

    def resource_distributions_by_node(self, coord: int) -> Hand:
        print('coord', coord)
        print('adj', self.get_adj_tile_ids_to_node(coord))
        print([self.hexes()[h].resource() for h in self.get_adj_tile_ids_to_node(coord)])
        return Hand(*(self.hexes()[h].resource() for h in self.get_adj_tile_ids_to_node(coord)
                      if self.hexes()[h].resource() not in (Consts.ResourceType.DESERT, Consts.ResourceType.ANY)))

    def resource_distributions(self, dice_sum: int) -> Dict[int, Hand]:
        dist = {}
        for hex_tile in self.hexes():
            if hex_tile.token() == dice_sum and not hex_tile.has_robber():    # hex that distributes
                adj_nodes = hexgrid.nodes_touching_tile(hex_tile.id() + 1)  # he uses 1 indexing # todo check if other places too
                for node in adj_nodes:
                    if self.nodes().get(node):  # node has buildable on it
                        player_id = self.nodes().get(node).player_id()  # belongs to player_id
                        if player_id not in dist:
                            dist[player_id] = Hand()
                        dist[player_id].insert(Hand(hex_tile.resource()))   # add hex's resource to distributed hand
        return dist

    @staticmethod
    def get_adj_nodes_to_node(location: int) -> List[int]:
        if location % 2 == 1:
            return [location - 0x11, location + 0x11, location + 0x9]
        else:
            return [location - 0x11, location + 0x11, location - 0x9]

    @staticmethod
    def get_adj_edges_to_node(location: int) -> List[int]:
        if location % 2 == 1:
            return [location, location - 0x11, location - 0x1]
        else:
            return [location - 0x10, location - 0x11, location - 0x1]

    @staticmethod
    def get_adj_tile_ids_to_node(location: int) -> List[int]:
        if location not in hexgrid.legal_node_coords():
            raise ValueError(f'tried to access node {location}')
        if location % 2 == 0:
            tile_coords = [location - 0x1, location + 0x1, location - 0x21]
        else:
            tile_coords = [location + 0x20, location - 0x10, location - 0x12]
        return [hexgrid.tile_id_from_coord(coord) - 1 for coord in tile_coords if coord in hexgrid.legal_tile_coords()]


    def _city_legal_check(self, player_id: int, location: int) -> None:     # if not :
        if not (isinstance(self.nodes().get(location), Buildable) and   # 1. something is built there
                self.nodes().get(location).player_id() == player_id and     # 2, that thing belongs to this player
                self.nodes().get(location).type() == Consts.PurchasableType.SETTLEMENT):    # 3. and it's a settlement
            raise ValueError(f'player {player_id} cannot build city on {location}, '        # then no good...
                             f'player does not own a settlement there')

    def _road_legal_check(self, player_id: int, location: int) -> None:
        if self.edges().get(location) is not None:
            raise ValueError(f'player {player_id} cannot build road on {location}, not available')
        node_coords = hexgrid.nodes_touching_edge(location)
        for coord in node_coords:
            if self.nodes().get(coord) is not None and self.nodes().get(coord).player_id() == player_id:
                break
        else:  # road not connected to player settlement / city
            raise ValueError(f'player {player_id} cannot build road on {location}, no buildable in '
                             f'adjacent nodes {[hex(c) for c in node_coords]}')

    def build(self, buildable: Buildable) -> None:
        coords = self.nodes()
        if buildable.type() == Consts.PurchasableType.ROAD:
            # self._road_legal_check(player_id, location)
            coords = self.edges()
        # elif btype == Consts.PurchasableType.SETTLEMENT:
        #     self._settlement_legal_check(player_id, location, pre_game)
        # elif btype == Consts.PurchasableType.CITY:
        #     self._city_legal_check(player_id, location)
        # else:
        #     raise ValueError(f'cannot build PurchasableType {btype}')
        coords[buildable.coord()] = buildable

    def info(self) -> str:
        ret_val = []
        ret_val.append('\n[BOARD] Hexes')
        for h in self.hexes():
            ret_val.append(h.info())
        ret_val.append('\n[BOARD] Buildables')
        for n, buildable in self.nodes().items():
            ret_val.append(buildable.info())
        for n, buildable in self.edges().items():
            ret_val.append(buildable.info())
        return '\n'.join(ret_val)

    def __str__(self) -> str:
        h = self.__hexes

        return f"""
                                 _____ 
                               /       \\
                        _____ / {str(h[0]):^15}  \\ _____
                      /       \\   {h[0].token():^2}    /       \\
               _____ / {str(h[1]):^15}  \\ _____ / {str(h[11]):^15}  \\ _____
             /       \\   {h[1].token():^2}    /       \\   {h[11].token():^2}    /       \\
            / {str(h[2]):^15}  \\ _____ / {str(h[12]):^15}  \\ _____ / {str(h[10]):^15}  \\
            \   {h[2].token():^2}    /       \\   {h[12].token():^2}    /       \\   {h[10].token():^2}    /
             \ _____ / {str(h[13]):^15}  \\ _____ / {str(h[17]):^15}  \\ _____ /
             /       \\   {h[13].token():^2}    /       \\   {h[17].token():^2}    /       \\
            / {str(h[3]):^15}  \\ _____ / {str(h[18]):^15}  \\ _____ / {str(h[9]):^15}  \\
            \   {h[3].token():^2}    /       \\   {h[18].token():^2}    /       \\   {h[9].token():^2}    /
             \ _____ / {str(h[14]):^15}  \\ _____ /  {str(h[16]):^15} \\ _____ /
             /       \\   {h[14].token():^2}    /       \\   {h[16].token():^2}    /       \\
            / {str(h[4]):^15}  \\ _____ / {str(h[15]):^15}  \\ _____ / {str(h[8]):^15}  \\
            \   {h[4].token():^2}    /       \\   {h[15].token():^2}    /       \\   {h[8].token():^2}    /
             \ _____ / {str(h[5]):^15}  \\ _____ / {str(h[7]):^15}  \\ _____ /
                     \\   {h[5].token():^2}    /       \\   {h[7].token():^2}    /
                      \\ _____ / {str(h[6]):^15}  \\ _____ /
                              \\   {h[6].token():^2}    /
                               \\ _____ /

             """


if __name__ == '__main__':
    b = Board()
    print(b.info())
    exit()
    print(hexgrid.legal_node_coords())
    b.build(0, Consts.PurchasableType.SETTLEMENT, 0x49)
    print(hexgrid.legal_node_coords())
