import GameSession
import Player
from typing import Callable
import GameConstants as Consts
import Dice



VP_WEIGHT = 1  # victory points heuristic weight
PREFER_RESOURCES_WEIGHT = 0.2
HARBOURS_WEIGHT = 0.8
DIVERSITY_WEIGHT = 0.5
BUILD_IN_GOOD_PLACES_WEIGHT = 5
ROADS_WEIGHT = 0.6
SETTLES_WEIGHT = 0.7
CITIES_WEIGHT = 2.5
DEV_CARDS_WEIGHT = 2
ENOUGH_RES_TO_BUY = 1

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
    return len(__sim_player.harbors())/9


def game_won_heuristic(session: GameSession, player: Player):
    return float('inf') if session.winning_player == player else 0


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
    return __calc_score / 150

def roads_heuristic(session:GameSession,player:Player):
    __sim_player = find_sim_player(session,player)
    return __sim_player.num_roads()/15 # 15 roads max per player

def settles_heuristic(session:GameSession,player:Player):
    __sim_player = find_sim_player(session,player)
    __settles = __sim_player.num_settlements()
    if __settles >= 5:
        return 0
    return __settles/5 # 5 settlements max per player

def cities_heuristic(session:GameSession,player:Player):
    __sim_player = find_sim_player(session,player)
    return __sim_player.num_cities()/4 # 5 settlements max per player

def dev_cards_heuristic(session:GameSession,player:Player):
    __sim_player = find_sim_player(session,player)
    return __sim_player.dev_hand().size()/25



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
    for res in __resources[0:5]:
        if res:
            __num_types += 1
    return __num_types/5

def build_in_good_places(session: GameSession, player: Player):
    """
    prefer building in more attractive places
    :param session:
    :param player:
    :return: the number of tiles the player has
    multiply by the token's probability
    """
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

def enough_res_to_buy(session: GameSession, player: Player):
    __sim_player = find_sim_player(session, player)
    __hand = __sim_player.resource_hand()
    __road_score = 0
    __settle_score = 0
    __city_score = 0
    __dev_card_score = 0

    if __hand.contains(Consts.COSTS[Consts.PurchasableType.ROAD]):
        __road_score += 0.5
    if __hand.contains(Consts.COSTS[Consts.PurchasableType.SETTLEMENT]):
        __settle_score += 1
    if __hand.contains(Consts.COSTS[Consts.PurchasableType.CITY]):
        __city_score += 1.5
    if __hand.contains(Consts.COSTS[Consts.PurchasableType.DEV_CARD]):
        __dev_card_score += 1
    # print(__hand)
    return (__road_score + __settle_score + __city_score + __dev_card_score)/3



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
    __vp = vp_heuristic(session,player) * VP_WEIGHT
    __harbours = harbors_heuristic(session,player) * HARBOURS_WEIGHT
    __prefer = prefer_resources_in_each_part(session,player) * PREFER_RESOURCES_WEIGHT # todo: not good at all
    __roads = roads_heuristic(session,player)*ROADS_WEIGHT
    __settles = settles_heuristic(session,player) * SETTLES_WEIGHT
    __cities = cities_heuristic(session,player) * CITIES_WEIGHT
    __diversity = resources_diversity_heuristic(session,player)*DIVERSITY_WEIGHT
    __build = build_in_good_places(session,player)*BUILD_IN_GOOD_PLACES_WEIGHT
    __dev = dev_cards_heuristic(session,player) * DEV_CARDS_WEIGHT
    __won_game = game_won_heuristic(session,player)
    __enough_res_to_buy = enough_res_to_buy(session,player)*ENOUGH_RES_TO_BUY

    #
    #     print("////////////////////")
    #     print(session.board())
    #     print("Heuristics' Scores: ")
    #     print("prefer: ",__prefer)
    #     print(str.title(f"victory point: {__vp}\nharbours: \
    # {__harbours}\nroads: {__roads}\nsettlements: {__settles}\ndev cards: \
    # {__dev}\ncities: {__cities}\nbuild in good places: {__build}\ndiversity: \
    # {__diversity}\nenough res to buy: {__enough_res_to_buy}"))
    #     print("sum score: ",__sum_score)
    #     print("////////////////////")

    # todo: altogether, needs tuning...
    __sum_score = __vp + __harbours + \
           __roads + \
           __settles+ __cities + __build + __dev +\
                  __won_game + __diversity + __enough_res_to_buy + __prefer

    __builder_characteristic = __build + __roads+ __cities + __won_game # todo: pretty good combination


    return __enough_res_to_buy + __build + __settles + __roads
    # return __diversity + __build + __won_game + __dev
