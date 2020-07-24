from enum import Enum
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
        # The number (the result of a dice roll) of each hex, dictionary with tile coordinates, NOT ids (see the link up)
        self.hex_numbers = {}
        for i in range(len(numbers)):
            self.hex_numbers[hexgrid.tile_id_to_coord(i +1)] = numbers[i];

        # Dictionary of roads (from index to player index)
        self.roads = {}

        # Dictionary of settelments and cities, from index to tuple (player index, PieceType)
        self.pieces = {}
        
        # Dictionary of harbors (from type to location)
        self.harbors = harbors.copy()

        # Location of the robber:
        self.robber_tile = hexgrid.tile_id_to_coord(tiles.index(HexType.DESERT) + 1)

        # Information we keep to simplify calculations:
        self.legal_nodes = hexgrid.legal_node_coords()

    def get_empty_edges_around_node(self, node):
        ret = []
        edges = get_edges_adjacent_to_node(node)
        for edge in edges:
            if not edge in self.roads.keys():
                ret.append(edge)
        return ret

    # Methods for the setup phase of the game:
    def setup_get_available_settlement_nodes(self):
        return self.legal_nodes.copy()

    def setup_place_settlement_and_road(self, player_id, node_id, edge_id):
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

if __name__ == "__main__":
    board = CatanBoard()



        