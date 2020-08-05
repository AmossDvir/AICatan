from __future__ import annotations
import hexgrid
import GameConstants as Consts
from random import shuffle
from typing import List, Dict
import HexTile
import Player
import Hand
import Buildable


class Board:
    COLORS = {
        'TEAL': '\033[96m',
        'YELLOW': '\033[93m',
        'RED': '\033[91m',
        'BLUE': '\033[94m',
        'END': '\033[0m'
    }

    def __init__(self):
        self.__init_hexes()
        self.__nodes = dict()
        self.__edges = dict()
        self.__player_colors = list(Board.COLORS.values())
        self.__players = []

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

            self.__hexes.append(HexTile.HexTile(hex_id, resource, token, has_robber))

    def hexes(self) -> List[HexTile.HexTile]:
        return self.__hexes

    def nodes(self) -> Dict[int, Buildable.Buildable]:
        return self.__nodes

    def edges(self) -> Dict[int, Buildable.Buildable]:
        return self.__edges

    def robber_hex(self) -> HexTile.HexTile:
        for hex_tile in self.hexes():
            if hex_tile.has_robber():
                return hex_tile

    def move_robber_to(self, hex_id: int) -> None:
        self.robber_hex().set_robber(False)
        self.hexes()[hex_id].set_robber(True)

    def resource_distributions_by_node(self, coord: int) -> Hand.Hand:
        print('coord', coord)
        print('adj', self.get_adj_tile_ids_to_node(coord))
        print([self.hexes()[h].resource() for h in self.get_adj_tile_ids_to_node(coord)])
        return Hand.Hand(*(self.hexes()[h].resource() for h in self.get_adj_tile_ids_to_node(coord)
                           if self.hexes()[h].resource() in Consts.YIELDING_RESOURCES))

    def resource_distributions(self, dice_sum: int) -> Dict[Player.Player, Hand.Hand]:
        dist = {}
        for hex_tile in self.hexes():
            if hex_tile.token() == dice_sum and not hex_tile.has_robber():  # hex that distributes
                adj_nodes = hexgrid.nodes_touching_tile(hex_tile.id() + 1)  # he uses 1 indexing
                for node in adj_nodes:
                    if self.nodes().get(node):  # node has buildable on it
                        player = self.nodes().get(node).player()  # belongs to player_id
                        if player not in dist:
                            dist[player] = Hand.Hand()
                        dist[player].insert(Hand.Hand(hex_tile.resource()))  # add hex's resource to distributed hand
        return dist

    @staticmethod
    def get_adj_nodes_to_node(location: int) -> List[int]:
        if location % 2 == 1:
            locs = [location - 0x11, location + 0x11, location + 0xf]
        else:
            locs = [location - 0x11, location + 0x11, location - 0xf]
        return [loc for loc in locs if loc in hexgrid.legal_node_coords()]

    @staticmethod
    def get_adj_edges_to_node(location: int) -> List[int]:
        if location % 2 == 1:
            locs = [location, location - 0x11, location - 0x1]
        else:
            locs = [location - 0x10, location - 0x11, location]
        return [loc for loc in locs if loc in hexgrid.legal_edge_coords()]

    @staticmethod
    def get_adj_tile_ids_to_node(location: int) -> List[int]:
        if location not in hexgrid.legal_node_coords():
            raise ValueError(f'tried to access node {location}')
        if location % 2 == 0:
            tile_coords = [location - 0x1, location + 0x1, location - 0x21]
        else:
            tile_coords = [location + 0x20, location - 0x10, location - 0x12]
        return [hexgrid.tile_id_from_coord(coord) - 1 for coord in tile_coords if coord in hexgrid.legal_tile_coords()]

    def build(self, buildable: Buildable.Buildable) -> None:
        player = buildable.player()
        if player not in self.__players:
            self.__players.append(player)
        coords = self.nodes()
        if buildable.type() == Consts.PurchasableType.ROAD:
            coords = self.edges()
        coords[buildable.coord()] = buildable

    def info(self) -> str:
        ret_val = ['\n[BOARD] Hexes']
        for h in self.hexes():
            ret_val.append(h.info())
        ret_val.append('\n[BOARD] Buildables')
        for n, buildable in self.nodes().items():
            ret_val.append(buildable.info())
        for n, buildable in self.edges().items():
            ret_val.append(buildable.info())
        return '\n'.join(ret_val)

    def __str__(self) -> str:
        def player_color(player):
            return self.__player_colors[self.__players.index(player)]

        def get_color(edge, is_edge=True):
            coords = self.edges() if is_edge else self.nodes()
            if coords.get(edge) is not None:
                return self.__player_colors[self.__players.index(coords.get(edge).player())]
            else:
                return Board.COLORS['END']

        def get_node_str(node):
            if self.nodes().get(node) is not None:
                if self.nodes().get(node).type() == Consts.PurchasableType.SETTLEMENT:
                    return 's'
                else:
                    return 'C'
            else:
                return ' '

        dh = {f'h{i}': str(h) for i, h in enumerate(self.hexes())}
        dht = {f'h{i}t': h.token() for i, h in enumerate(self.hexes())}
        x = 'x'
        dr = {f'r{hex(edge).split(x)[1]}': get_color(edge) for edge in hexgrid.legal_edge_coords()}
        legend = ' '.join('{}{}{}'.format(player_color(player), player, Board.COLORS['END'])
                          for player in self.__players)
        detc = {'e': Board.COLORS['END'], 'legend': legend}
        dn = {f'n{hex(node).split(x)[1]}': '{}{}{}'.format(get_color(node, is_edge=False), get_node_str(node),
                                                           Board.COLORS['END']) for node in hexgrid.legal_node_coords()}
        dy = {f'y{i}': 'R' if h.has_robber() else ' ' for i, h in enumerate(self.hexes())}
        d = dict()
        for other_dict in (dh, dht, dr, dn, dy, detc):
            for key, value in other_dict.items():
                d[key] = value

        return """
                                {n27}{r27}_____{e}{n38} 
                               {r26}/{e}   {y0}   {r38}\\{e}
                       {n25}{r25}_____{e}{n36}{r26}/{e} {h0:^15}  {r38}\\{e}{n49}{r49}_____{e}{n5a}
                      {r24}/{e}   {y1}   {r36}\\{e}   {h0t:^2}    {r48}/{e}   {y11}   {r5a}\\{e}
              {n23}{r23}_____{e}{n34}{r24}/{e} {h1:^15}  {r36}\\{e}{n47}{r47}_____{e}{n58}{r48}/{e} {h11:^15}  {r5a}\\{e}{n6b}{r6b}_____{e}{n7c}
             {r22}/{e}   {y2}   {r34}\\{e}   {h1t:^2}    {r46}/{e}   {y12}   {r58}\\{e}   {h11t:^2}    {r6a}/{e}   {y10}   {r7c}\\{e}
           {n32}{r22}/{e} {h2:^15}  {r34}\\{e}{n45}{r45}_____{e}{n56}{r46}/{e} {h12:^15}  {r58}\\{e}{n69}{r69}_____{e}{n7a}{r6a}/{e} {h10:^15}  {r7c}\\{e}{n8d}
            {r32}\\{e}   {h2t:^2}    {r44}/{e}   {y13}   {r56}\\{e}   {h12t:^2}    {r68}/{e}   {y17}   {r7a}\\{e}   {h10t:^2}    {r8c}/{e}
             {r32}\\{e}{n43}{r43}_____{e}{n54}{r44}/{e} {h13:^15}  {r56}\\{e}{n67}{r67}_____{e}{n78}{r68}/{e} {h17:^15}  {r7a}\\{e}{n8b}{r8b}_____{e}{n9c}{r8c}/{e}
             {r42}/{e}   {y3}   {r54}\\{e}   {h13t:^2}    {r66}/{e}   {y18}   {r78}\\{e}   {h17t:^2}    {r8a}/{e}   {y9}   {r9c}\\{e}
           {n52}{r42}/{e} {h3:^15}  {r54}\\{e}{n65}{r65}_____{e}{n76}{r66}/{e} {h18:^15}  {r78}\\{e}{n89}{r89}_____{e}{n9a}{r8a}/{e} {h9:^15}  {r9c}\\{e}{nad}
            {r52}\\{e}   {h3t:^2}    {r64}/{e}   {y14}   {r76}\\{e}   {h18t:^2}    {r88}/{e}   {y16}   {r9a}\\{e}   {h9t:^2}    {rac}/{e}
             {r52}\\{e}{n63}{r63}_____{e}{n74}{r64}/{e} {h14:^15}  {r76}\\{e}{n87}{r87}_____{e}{n98}{r88}/{e}  {h16:^15} {r9a}\\{e}{nab}{rab}_____{e}{nbc}{rac}/{e}
             {r62}/{e}   {y4}   {r74}\\{e}   {h14t:^2}    {r86}/{e}   {y15}   {r98}\\{e}   {h16t:^2}    {raa}/{e}   {y8}   {rbc}\\{e}
           {n72}{r62}/{e} {h4:^15}  {r74}\\{e}{n85}{r85}_____{e}{n96}{r86}/{e} {h15:^15}  {r98}\\{e}{na9}{ra9}_____{e}{nba}{raa}/{e} {h8:^15}  {rbc}\\{e}{ncd}
            {r72}\\{e}   {h4t:^2}    {r84}/{e}   {y5}   {r96}\\{e}   {h15t:^2}    {ra8}/{e}   {y7}   {rba}\\{e}   {h8t:^2}    {rcc}/{e}
             {r72}\\{e}{n83}{r83}_____{e}{n94}{r84}/{e} {h5:^15}  {r96}\\{e}{na7}{ra7}_____{e}{nb8}{ra8}/{e} {h7:^15}  {rba}\\{e}{ncb}{rcb}_____{e}{ndc}{rcc}/{e}
                     {r94}\\{e}   {h5t:^2}    {ra6}/{e}   {y6}   {rb8}\\{e}   {h7t:^2}    {rca}/{e}
                      {r94}\\{e}{na5}{ra5}_____{e}{nb6}{ra6}/{e} {h6:^15}  {rb8}\\{e}{nc9}{rc9}_____{e}{nda}{rca}/{e}
                              {rb6}\\{e}   {h6t:^2}    {rc8}/{e}
                               {rb6}\\{e}{nc7}{rc7}_____{e}{nd8}{rc8}/{e}

             {legend}""".format(**d)
