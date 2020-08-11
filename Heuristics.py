import GameSession
import Player
import GameConstants as Consts



VP_WEIGHT = 0  # victory points heuristic weight
PREFER_RESOURCES_WEIGHT = 0


def find_sim_player(session:GameSession,player:Player):
    # find the player's turn for the current session simulation
    for sim_player in session.players():
        if sim_player.get_id() == player.get_id():
            return sim_player

# We don't need the session for this specific heuristic, but this is the
# general form:
def vp_heuristic(session: GameSession, player: Player) -> int:
    __sim_player = find_sim_player(session, player)
    if __sim_player != None:
        return __sim_player.vp()
    return 0

def harbors_heuristic(session:GameSession,player:Player):
    """
    the more harbors - the higher the score gets
    :param session: a GameSession
    :param player: a Player
    :return: Integer, the score for the given game session
    """
    __sim_player = find_sim_player(session, player)
    player.harbors()
    return len(__sim_player.harbors())


def prefer_resources_in_each_part(session:GameSession,player:Player):
    """
    heuristic that gives priority for having bricks and woods in the
    the early stages of the game and having sheep, ore and wheat in
    the advanced phase of the game.
    :param session: a GameSession
    :param player: a Player
    :return: Integer, the score for the given game session
    """

    # resources:
    __sim_player = find_sim_player(session,player)
    __num_forest = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.FOREST).size()
    __num_bricks = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.BRICK).size()
    __num_sheep = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.SHEEP).size()
    __num_wheat = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.WHEAT).size()
    __num_ore = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.ORE).size()

    # buildings:
    __num_roads = __sim_player.num_roads()
    __num_cities = __sim_player.num_cities()
    __num_settles = __sim_player.num_settlements()
    __num_buildings =  __num_roads + __num_settles + __num_cities

    __calc_score = (100*(0.8*__num_forest + 1.2*__num_bricks+0.3*__num_sheep+0.3*__num_wheat)/((__num_buildings))+(__num_buildings)*(0.75*__num_sheep + 0.75*__num_wheat + 1.5*__num_ore))
    # print("resources heuristic: " , __calc_score)
    return __calc_score/100

def roads_heuristic(session:GameSession,player:Player):
    __sim_player = find_sim_player(session,player)
    return __sim_player.num_roads()

def settles_heuristic(session:GameSession,player:Player):
    __sim_player = find_sim_player(session,player)
    return __sim_player.num_settlements()*5


def resources_diversity_heuristic(session:GameSession,player:Player):
    """
    prefer having more resources and diversity in resources
    :param session:
    :param player:
    :return:
    """
    __sim_player = find_sim_player(session,player)
    __resources = [__sim_player.resource_hand().cards_of_type(resource) for resource in Consts.ResourceType]
    __num_types = 0
    __num_res = 0
    # print("--------------------")
    for res in __resources[0:5]:
        # print(res)
        if res:
            __num_types += 1
        __num_res += len(res)
    # print(__num_res * __num_types*10)
    # print("--------------------")
    return __num_res * __num_types/3

def build_in_good_places(session:GameSession,player:Player):
    __sim_player = find_sim_player(session, player)
    __board = session.board()
    # print(__sim_player.settlement_nodes())
    print(__board)
    nodes = []
    for node in __sim_player.settlement_nodes():
        nodes.append(node)
        tiles = __board.get_adj_tile_ids_to_node(node)
        for tile in tiles:
            print(__board.hexes()[tile])
            print(__board.hexes()[tile].token())
        # print(__board.hexes()[])
        # print(node)
    # res = [__board.hexes()[[tile for tile in __board.get_adj_tile_ids_to_node(node)]]]
    # print(res)

    # res = [(__board.resource_distributions_by_node(node)) for node in __sim_player.settlement_nodes()]
    # print([r for r in res])
    # print([hex_tile.token() for hex_tile in __board.hexes()])





def main_heuristic(session:GameSession,player:Player):
    __vp = vp_heuristic(session,player)
    __harbours = harbors_heuristic(session,player)
    __prefer = prefer_resources_in_each_part(session,player)
    __roads = roads_heuristic(session,player)
    __settles = settles_heuristic(session,player)
    __diversity = resources_diversity_heuristic(session,player)
    build_in_good_places(session,player)

#     print("////////////////////")
#     print(str.title(f"victory point: {__vp}\nharbours: \
# {__harbours}\nprefer resources in each part: {__prefer}\nroads: \
# {__roads}\nsettlements: {__settles}\nresource diversity: {__diversity}"))
#     print("////////////////////")


    return vp_heuristic(session,player) + harbors_heuristic(session,player) + \
           prefer_resources_in_each_part(session,player) + roads_heuristic(session,player) + \
           settles_heuristic(session,player)+resources_diversity_heuristic(session,player)


