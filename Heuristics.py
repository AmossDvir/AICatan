import GameSession
import Player
from typing import Callable
import GameConstants as Consts
import Dice



VP_WEIGHT = 0  # victory points heuristic weight
PREFER_RESOURCES_WEIGHT = 0


def find_sim_player(session: GameSession, player: Player) -> Player:
    # find the player's turn for the current session simulation
    for sim_player in session.players():
        if sim_player.get_id() == player.get_id():
            return sim_player

# We don't need the session for this specific heuristic, but this is the
# general form:
def vp_heuristic(session: GameSession, player: Player) -> int:
    __sim_player = find_sim_player(session, player)
    if __sim_player != None:
        return __sim_player.vp()/10 # 10 is the bound
    return 0


def harbors_heuristic(session: GameSession, player: Player):
    """
    the more harbors - the higher the score gets
    :param session: a GameSession
    :param player: a Player
    :return: Integer, the score for the given game session
    """
    __sim_player = find_sim_player(session, player)
    player.harbors()
    return len(__sim_player.harbors())


def game_won_heuristic(session: GameSession, player: Player):
    return float('inf') if session.winner() == player else 0


def relative_vp_heuristic(session: GameSession, player: Player):
    """:returns VP / (average opponent VP) ratio"""
    return relative_of(vp_heuristic, session, player)


def negative_vp_heuristic(session: GameSession, player: Player):
    return negative_of(vp_heuristic, session, player)


def negative_of(heuristic: Callable[[GameSession, Player], float], session: GameSession, player: Player) -> float:
    """:returns the negative value of given heuristic based on how good opponents values are for heuristic"""
    opp_vals = 0
    for p in session.players():
        if p != player:
            opp_vals += heuristic(session, p)

    return - opp_vals


def relative_of(heuristic: Callable[[GameSession, Player], float], session: GameSession, player: Player) -> float:
    """:returns ratio of player's heuristic value to average opponents value on given heuristic"""
    my_val = 0
    opp_vals = []
    for p in session.players():
        if p != player:
            opp_vals.append(heuristic(session, p))
        else:
            my_val += heuristic(session, p)

    return my_val / (sum(opp_vals) / len(opp_vals))


def prefer_resources_in_each_part(session: GameSession, player: Player):
    """
    heuristic that gives priority for having bricks and woods in the
    the early stages of the game and having sheep, ore and wheat in
    the advanced phase of the game.
    :param session: a GameSession
    :param player: a Player
    :return: Integer, the score for the given game session
    """

    # resources:
    __sim_player = find_sim_player(session, player)
    __num_forest = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.FOREST).size()
    __num_bricks = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.BRICK).size()
    __num_sheep = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.SHEEP).size()
    __num_wheat = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.WHEAT).size()
    __num_ore = __sim_player.resource_hand().cards_of_type(Consts.ResourceType.ORE).size()

    # buildings:
    __num_roads = __sim_player.num_roads()
    __num_cities = __sim_player.num_cities()
    __num_settles = __sim_player.num_settlements()
    __num_buildings = __num_roads + __num_settles + __num_cities

    __calc_score = (100 * (0.8 * __num_forest + 1.2 * __num_bricks + 0.3 * __num_sheep + 0.3 * __num_wheat) / (
        (__num_buildings)) + (__num_buildings) * (0.75 * __num_sheep + 0.75 * __num_wheat + 1.5 * __num_ore))
    # print("resources heuristic: " , __calc_score)
    return __calc_score / 100

def roads_heuristic(session:GameSession,player:Player):
    __sim_player = find_sim_player(session,player)
    return __sim_player.num_roads()/15 # 15 roads max per player

def settles_heuristic(session:GameSession,player:Player):
    __sim_player = find_sim_player(session,player)
    return __sim_player.num_settlements()/5 # 5 settlements max per player


def resources_diversity_heuristic(session: GameSession, player: Player):
    """
    prefer having more resources and diversity in resources
    :param session:
    :param player:
    :return:
    """
    __sim_player = find_sim_player(session, player)
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

def build_in_good_places(session: GameSession, player: Player):
    __sim_player = find_sim_player(session, player)
    __board = session.board()
    # print(__sim_player.settlement_nodes())

    nodes = []
    tiles_types = set()
    num_tiles = 0
    tiles_prob = 0
    for node in __sim_player.settlement_nodes():
        nodes.append(node)
        for tile in __board.get_adj_tile_ids_to_node(node):
            num_tiles += 1
            tiles_types.add(__board.hexes()[tile].resource())
            tiles_prob += Dice.PROBABILITIES[__board.hexes()[tile].token()]
    return (num_tiles*len(tiles_types)*tiles_prob)/227.5 # 227.5 is the bound



def probability_score_heuristic(session: GameSession, player: Player) -> float:
    for p in session.players():
        if p.get_id() == player.get_id():
            return session.board()._probability_score(p) + session.board()._expectation_score(p)


def road_len_heuristic(session: GameSession, player: Player) -> float:
    return session.board().road_len(player) / 15


def everything_heuristic(session: GameSession, player: Player) -> float:
    for p in session.players():
        if p.get_id() == player.get_id():
            return probability_score_heuristic(session, player) + \
                   vp_heuristic(session, player) + \
                   road_len_heuristic(session, player)


def relative_everything_heuristic(session: GameSession, player: Player) -> float:
    other_scores = []
    my_score = 0
    for p in session.players():
        if p.get_id() == player.get_id():
            my_score = everything_heuristic(session, p)
        else:
            other_scores.append(everything_heuristic(session, p))
    other_avg = sum(other_scores) / len(other_scores)
    if other_avg == 0:
        return float('inf')

    return my_score / other_avg




def main_heuristic(session:GameSession,player:Player):
    __vp = vp_heuristic(session,player)
    __harbours = harbors_heuristic(session,player)
    __prefer = prefer_resources_in_each_part(session,player)
    __roads = roads_heuristic(session,player)
    __settles = settles_heuristic(session,player)
    __diversity = resources_diversity_heuristic(session,player)
    __build = build_in_good_places(session,player)

    print("////////////////////")
    print(str.title(f"victory point: {__vp}\nharbours: \
{__harbours}\nroads: {__roads}\nsettlements: {__settles}\nbuild in good places: {__build}"))
    print("////////////////////")

    return __vp + __harbours + \
           __roads + \
           __settles + __build


