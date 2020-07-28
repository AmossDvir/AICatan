from enum import Enum
from collections import defaultdict
from state import 
import hexgrid

# Some definitions:
class HexType(Enum):
    FOREST = 1
    PASTURE = 2
    FIELD = 3
    HILL = 4
    MOUNTAIN = 5
    DESERT = 6

class HarborType(Enum):
    WOOD = 1
    SHEEP = 2
    WHEAT = 3
    BRICK = 4
    ORE = 5
    ANY3 = 6

class Resource(IntEnum):
    WOOD = 0
    BRICK = 1
    SHEEP = 2
    WHEAT = 3
    ORE = 4

class PieceType(Enum):
    SETTLEMENT = 1
    CITY = 2


# The order is according to the first image in:
# https://github.com/rosshamish/hexgrid/

DEFAULT_TILES = [HexType.FOREST, HexType.FOREST, HexType.FOREST, HexType.FOREST, HexType.PASTURE, HexType.PASTURE, HexType.PASTURE, HexType.PASTURE,
                    HexType.FIELD, HexType.FIELD, HexType.FIELD, HexType.FIELD, HexType.HILL, HexType.HILL, HexType.HILL, HexType.MOUNTAIN,
                    HexType.MOUNTAIN, HexType.MOUNTAIN, HexType.DESERT]

DEFAULT_NUMBERS = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]

DEFAULT_HARBORS = {HarborType.WHEAT: [0x94, 0xA5], HarborType.ANY3: [0xC7, 0xD8, 0x23, 0x32, 0x5A, 0x49, 0x7C, 0x8D],
                    HarborType.SHEEP: [0x25, 0x36], HarborType.WOOD: [0xCB, 0xDA], HarborType.ORE: [0x52, 0x63], HarborType.BRICK: [0xAD, 0xBC]}

class CatanBoard:
    def __init__(self, tiles=DEFAULT_TILES, numbers=DEFAULT_NUMBERS, harbors=DEFAULT_HARBORS):
        # The type of each hex, dictionary with tile coordinates, NOT ids (see the link up)
        self.hex_types = {}
        for i in range(len(tiles)):
            self.hex_types[hexgrid.tile_id_to_coord(i +1)] = tiles[i];
        # The number (the result of a dice roll) of each hex
        # dictionary with roll result -> tile coordinates
        self.tile_numbers = defaultdict(list)
        for i in range(len(numbers)):
            self.tile_numbers[numbers[i]] += [hexgrid.tile_id_to_coord(i +1)];

        # Dictionary of roads (from index to player index)
        self.roads = {}

        # Dictionary of settelments and cities, from index to tuple (player index, PieceType)
        self.pieces = {}
        
        # Dictionary of harbors (from type to location)
        self.harbors = harbors.copy()

        # Location of the robber:
        self.robber_tile = hexgrid.tile_id_to_coord(tiles.index(HexType.DESERT) + 1)

        # Information we keep to avoid complex calculations:
        self.legal_nodes = hexgrid.legal_node_coords()
        self.longest_road_player = None
        self.longest_road_length = 4 # So once someone gets to five he gets it

    def get_empty_edges_around_node(self, node):
        """
        :param node: The index number of the node
        :return: Array of edges (can be empty)
        """
        ret = []
        edges = get_edges_adjacent_to_node(node)
        for edge in edges:
            if not edge in self.roads.keys():
                ret.append(edge)
        return ret

    # Methods for the setup phase of the game:
    def setup_get_available_settlement_nodes(self):
        """
        returns all the legal places to put a settlement in
        """
        return self.legal_nodes.copy()

    def setup_place_settlement_and_road(self, player_id, node_id, edge_id):
        """
        Places a settlement and road on the board (used in the setup phase of the game)
        """
        if not node_id in self.legal_nodes:
            raise ValueError("Couldn't place settlement, illegal node id.")
        if edge_id in self.roads.keys():
            raise ValueError("Couldn't place road, illegal edge id.")
        self.legal_nodes.remove(node_id)
        # Remove adjecent nodes (since it's illegal to build next to a settlement)
        for node in get_nodes_adjacent_node(node_id):
            self.legal_nodes.remove(node)
        self.roads[edge_id] = player_id
        self.pieces[node_id] = (player_id, PieceType.SETTLEMENT)
        # TODO: Return the resources from the city
        

    def build_settlement(self, player_id, node_id):
        """
        :param player_id: The id of the player that builds the settlement
        :node_id: The index of the node we build in
        """
        # Make sure the node is legal
        if not node_id in self.legal_nodes:
            raise ValueError("Couldn't place settlement, illegal node id.")
        # Make sure there is a road that belongs to the player around the node
        if player_id not in [self.roads.get(e, -1) for e in get_edges_adjacent_to_node(node_id)]

        self.legal_nodes.remove(node_id)
        # Remove adjecent nodes (since it's illegal to build next to a settlement)
        for node in get_nodes_adjacent_node(node_id):
            self.legal_nodes.remove(node)
        self.pieces[node_id] = (player_id, PieceType.SETTLEMENT)

    def build_road(self, player_id, edge_id):
        """
        :param player_id: The id of the player that builds the road
        :node_id: The index of the edge we buildthe road in
        """
        # Make sure the position is clear:
        if self.roads.get(edge_id, -1) != -1:
            raise ValueError("Couldn't place road, another road already exist in the edge.")
        # Make sure the player have another road touching this road:
        if player_id not in [self.roads.get(e, -1) for e in get_edges_adjacent_to_edge(edge_id)]
            raise ValueError("Couldn't place road, the player own no adjecent roads.")
        self.roads[edge_id] = player_id
        self.update_player_longest_road(player_id)

    def distribute_resources(self, rolled_number):
        """
        :param rolled_number: A number from 2 to 12, the result of the dice 
        :return: A dict player_id -> len 5 list [WOOD, BRICK, SHEEP, WHEAT, ORE]
        """
        ret = defaultdict(lambda: [0]*5)
        tiles = self.tile_numbers[rolled_number]
        for tile in tiles:
            resource_type = get_resource_type_of_tile(tile)
            nodes = get_nodes_adjacent_to_tile(tile)
            for node in nodes:
                player, piece = self.pieces.get(node, (None, None))
                if player is not None:
                    if piece == PieceType.SETTLEMENT:
                        ret[player][resource_type] += 1
                    elif piece == PieceType.CITY:
                        ret[player][resource_type] += 2
        return ret
            

    # Methods for the game_state:
    def get_player_harbors(self, player_id):
        """
        :param player_id: The player we want the info about
        :return: A list of HarborType that describes what kind of harbors the player control
        """
        harbors = []
        for t in HarborType:
            for node in self.harbors[t]:
                if self.pieces.get(node, (None, None)) == player_id:
                    harbors.append(t)
                    break
        return harbors

    def get_player_legal_settlement_nodes(self, player_id):
        """
        :param player_id: The player we want the info about
        :return: A list of nodes that the player allowed to build settlement in
        """
        ret = set()
        for node in self.legal_nodes:
            # Check if we have road nearby:
            for edge in get_edges_adjacent_to_node(node):
                if self.roads.get(edge, None) == player_id:
                    ret.append(node)
                    break
        return ret

    def get_player_legal_road_edges(self, player_id):
        """
        :param player_id: The player we want the info about
        :return: A list of edges that the player in build road in
        """
        ret = []
        for edge in self.roads:
            for adj in get_edges_adjacent_to_edge(edge):
                if adj not in self.roads:
                    ret.append(adj)
        return ret


    def get_player_legal_city_nodes(self, player_id):
        """
        :param player_id: The player we want the info about
        :return: A list of nodes that the player allowed to build settlement in
        """
        ret = []
        for piece_node in self.pieces:
            player, piece_type = self.pieces[piece_node]
            if player == player_id and piece_type == PieceType.SETTLEMENT:
                ret.append(piece_node)
        return ret

    def get_player_with_longest_road(self):
        return self.longest_road_player

    def update_player_longest_road(self, player_id):
        """
        Checks if the player have the longest road,
        and update self.longest_road_player and self.longest_road_length 
        """
        # This is complicated...
        pass

    def get_board_victory_points(self):
        """
        returns a dict from player_id to amount of victory points of boards
        """
        points = defaultdict(lambda: 0)
        for piece in self.pieces:
            player_id, piece_type = self.pieces[piece]
            if piece_type == PieceType.SETTLEMENT:
                points[player_id] += 1
            elif piece_type == PieceType.CITY:
                points[player_id] += 2
        return points 


# Auxiliary functions for hexgrid
def get_nodes_adjacent_node(node):
    if node % 2 == 0:
        return [node - 0xF, node + 0x11, node - 0x11] # N, SE, SW
    else:
        return [node - 0x11, node + 0x11, node + 0xF] # NW, NE, S

def get_edges_adjacent_to_node(node):
    if node % 2 == 0:
        return [node, node - 0x10, node - 0x11]
    else:
        return [node, node - 0x01, node - 0x11]

def get_edges_adjacent_to_edge(edge):
    edges = []
    nodes = hexgrid.nodes_touching_edge(edge)
    for node in nodes:
        edges += get_edges_adjacent_to_node(node)
    return edges

def get_nodes_adjacent_to_tile(tile):
    return [tile + 0x1, tile + 0x10, tile+0x21, tile+0x12, tile-0x10, tile-0x1]

def get_resource_type_of_tile(tile):
    hextype = self.tile_numbers[tile]
    if hextype == HexType.FOREST:
        return Resource.WOOD
    elif hextype == HexType.PASTURE:
        return Resource.SHEEP
    elif hextype == HexType.HILL:
        return Resource.BRICK
    elif hextype == HexType.FIELD:
        return Resource.WHEAT
    elif hextype == HexType.MOUNTAIN:
        return Resource.ORE



        