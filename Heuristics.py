import GameSession
import Player
import GameConstants as Consts
import Dice
from copy import deepcopy
from itertools import combinations
import Moves


INF = 100000
VP_WEIGHT = 2  # victory points heuristic weight
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
    """
    :return: The number of victory points divided by 10 (so between 0 to 1)
    """

    if player != None:
        return player.vp()/10 # 10 is the bound
    return 0


def harbors_heuristic(session: GameSession, player: Player):
    """
    the more harbors - the higher the score gets
    :param session: a GameSession
    :param player: a Player
    :return: Integer, the score for the given game session
    """
    return len(player.harbors())/9

def keep_res_you_cant_achieve(session: GameSession, player: Player,move:Moves):
    """
    prefer keeping the resources you can't achieve from dice
    :return:
    """
    if move.get_type() == Moves.MoveType.TRADE:
        __board = session.board()
        types_res = __board.resources_player_can_get(player)
        print(types_res.pop(),move.gives(),move.gets())


        # todo: continue writing
    return 0

def game_won_heuristic(session: GameSession, player: Player):
    """
    :return: infinity if the player won the game, else: 0
    """
    if session.winner() is not None:
        return INF if session.winner() == player else -INF
    return 0

def relative_vp_heuristic(session: GameSession, player: Player):
    """:returns VP / (average opponent VP) ratio"""
    return relative_of(vp_heuristic, session, player)


def negative_vp_heuristic(session: GameSession, player: Player):
    return negative_of(vp_heuristic, session, player)


def negative_of(heuristic, session: GameSession, player: Player) -> float:
    """:returns the negative value of given heuristic based on how good opponents values are for heuristic"""
    opp_vals = 0
    for p in session.players():
        if p != player:
            opp_vals += heuristic(session, p)

    return - opp_vals


def relative_of(heuristic, session: GameSession, player: Player) -> float:
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
    __num_forest = player.resource_hand().cards_of_type(Consts.ResourceType.FOREST).size()
    __num_bricks = player.resource_hand().cards_of_type(Consts.ResourceType.BRICK).size()
    __num_sheep = player.resource_hand().cards_of_type(Consts.ResourceType.SHEEP).size()
    __num_wheat = player.resource_hand().cards_of_type(Consts.ResourceType.WHEAT).size()
    __num_ore = player.resource_hand().cards_of_type(Consts.ResourceType.ORE).size()

    # buildings:
    __num_roads = player.num_roads()
    __num_cities = player.num_cities()
    __num_settles = player.num_settlements()
    __num_buildings = __num_roads + __num_settles + __num_cities

    __calc_score = (100 * (0.8 * __num_forest + 1.2 * __num_bricks + 0.3 * __num_sheep + 0.3 * __num_wheat) / (
        (__num_buildings)) + (__num_buildings) * (0.75 * __num_sheep + 0.75 * __num_wheat + 1.5 * __num_ore))
    # print("resources heuristic: " , __calc_score)
    return __calc_score / 150

def roads_heuristic(session:GameSession,player:Player):
    """
    :return: the number of roads the player has, divided by 15 (so between 0 to 1)
    """
    return player.num_roads()/15 # 15 roads max per player

def settles_heuristic(session:GameSession,player:Player):
    """
    :return: the number of settlements the player has, divided by 5 (so between 0 to 1)
    and if the player has more that 5, the function returns 0
    """
    __settles = player.num_settlements()
    if __settles >= 5:
        return 0
    return __settles/5 # 5 settlements max per player

def cities_heuristic(session:GameSession,player:Player):
    """
    :return: the number of cities the player has, divided by 4 (so between 0 to 1)
    """
    return player.num_cities()/4 # 4 cities max per player

def dev_cards_heuristic(session:GameSession,player:Player):
    """
    :return: the number of development cards the player has, divided by the
    size if the stack on the deck (so between 0 to 1)
    """
    return player.dev_hand().size()/26



def resources_diversity_heuristic(session: GameSession, player: Player):
    """
    prefer having more resources and diversity in resources
    :return:
    """
    __resources = [player.resource_hand().cards_of_type(resource) for resource in Consts.ResourceType]
    __num_types = 0
    for res in __resources[0:5]:
        if res:
            __num_types += 1
    return __num_types/5

def build_in_good_places(session: GameSession, player: Player):
    """
    prefer building in more attractive places
    :return: the number of tiles the player has
    multiply by the token's probability
    """
    __board = session.board()
    nodes = []
    tiles_types = set()
    num_tiles = 0
    tiles_prob = 0
    for node in player.settlement_nodes():
        nodes.append(node)
        for tile in __board.get_adj_tile_ids_to_node(node):
            num_tiles += 1
            tiles_types.add(__board.hexes()[tile].resource())
            tiles_prob += Dice.PROBABILITIES[__board.hexes()[tile].token()]
    return (num_tiles*len(tiles_types)*tiles_prob)/227.5 # 227.5 is the bound


def enough_res_to_buy(session: GameSession, player: Player):
    """
    checks if the player has enough resources to buy things.
    :return:
    """
    __hand = player.resource_hand()
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
    return (__road_score + __settle_score + __city_score + __dev_card_score)/3


def probability_score_heuristic(session: GameSession, player: Player) -> float:
    for p in session.players():
        if p.get_id() == player.get_id():
            return session.board()._probability_score(p) + session.board()._expectation_score(p)


def road_len_heuristic(session: GameSession, player: Player) -> float:
    """
    :return: the road length of the current player divided by 15
    """
    return session.board().road_len(player) / 15

def rel_max_everything(session, player):
    return relative_to_max_opp_of(everything_heuristic, session, player)


def relative_to_max_opp_of(heuristic, session, player):
    my_player = find_sim_player(session, player)
    my_score = heuristic(session, my_player)
    max_opp_score = 0
    for p in session.players():
        if p != my_player:
            opp_score = heuristic(session, p)
            max_opp_score = max(max_opp_score, opp_score)
    if max_opp_score == 0:
        return INF if my_score > 0 else 0

    return my_score / max_opp_score


def hand_size_heuristic(session, player):
    OPTIMAL_HAND_SIZE = 7
    if player.resource_hand_size() >= OPTIMAL_HAND_SIZE:
        return 1
    else:
        return player.resource_hand_size() / OPTIMAL_HAND_SIZE

def hand_diversity_heuristic(session, player):
    MAX_RESOURCE_TYPES = len(Consts.YIELDING_RESOURCES)
    num_unique_resources = 0
    for resource in Consts.ResourceType:
        if player.resource_hand().cards_of_type(resource).size() > 0:
            num_unique_resources += 1
    return num_unique_resources / MAX_RESOURCE_TYPES

def everything_heuristic(session: GameSession, player: Player) -> float:
    for p in session.players():
        if p.get_id() == player.get_id():
            player = p
    prob = probability_score_heuristic(session, player)
    vp = vp_heuristic(session, player)
    road = road_len_heuristic(session, player)
    won = game_won_heuristic(session, player)
    hsize = hand_size_heuristic(session, player)
    hdiverse = hand_diversity_heuristic(session, player)
    devs = dev_cards_heuristic(session, player)
    purchases = affordable_purchasables_heuristic(session, player)
    legal_hand = legal_hand_heuristic(session, player)
    s = sum([prob, vp, road, won, hsize, hdiverse, devs, purchases, legal_hand])
    # print('player', player, 'prob', round(prob,3), 'vp', round(vp,3), 'road', round(road,3),
    #       'won', round(won,3), 'hsize', round(hsize,3), 'hdiverse', round(hdiverse,3), 'devs', round(devs,3),
    #       'purchasables', round(purchases,3), 'legal hand', legal_hand, 'sum =', s)
    return s


def legal_hand_heuristic(session, player):
    if player.resource_hand_size() < Consts.MAX_CARDS_IN_HAND:
        return 0.0001
    else:
        return 0

def relative_everything_heuristic(session: GameSession, player: Player) -> float:
    return relative_of(everything_heuristic, session, player)


def affordable_purchasables_heuristic(session, player):

    num_affordable = 0
    my_hand = player.resource_hand()
    contained = False
    for purchasable, cost in Consts.COSTS.items():
        # print(1)
        if my_hand.contains(cost):
            num_affordable += 1
            contained = True
        cost_copy = deepcopy(cost)
        cost_copy.insert(cost)
        if my_hand.contains(cost_copy):
            num_affordable += 2

    if contained:
        contained = False
        for purchasable1, purch2 in combinations(Consts.PurchasableType, 2):
            # print(2)
            tot_cost = deepcopy(Consts.COSTS[purchasable1])
            tot_cost.insert(Consts.COSTS[purch2])
            if my_hand.contains(tot_cost):
                contained = True
                num_affordable += 2
    if contained:
        for purchasable1, purch2, p3 in combinations(Consts.PurchasableType, 3):
            # print(3)
            tot_cost = deepcopy(Consts.COSTS[purchasable1])
            tot_cost.insert(Consts.COSTS[purch2])
            tot_cost.insert(Consts.COSTS[p3])
            if my_hand.contains(tot_cost):
                num_affordable += 3
    # print('END')
    return num_affordable / 15


def main_heuristic(session:GameSession,player:Player,move:Moves):
    """
    calculates of score of each and every heuristic
    and returns a linear combination of them
    :param session:
    :param player:
    :return:
    """

    __sim_player = find_sim_player(session,player)
    __vp = vp_heuristic(session,__sim_player) * VP_WEIGHT
    __harbours = harbors_heuristic(session,__sim_player) * HARBOURS_WEIGHT
    __prefer = prefer_resources_in_each_part(session,__sim_player) * PREFER_RESOURCES_WEIGHT # todo: not good at all
    __roads = roads_heuristic(session,__sim_player)*ROADS_WEIGHT
    __settles = settles_heuristic(session,__sim_player) * SETTLES_WEIGHT
    __cities = cities_heuristic(session,__sim_player) * CITIES_WEIGHT
    __diversity = resources_diversity_heuristic(session,__sim_player)*DIVERSITY_WEIGHT
    __build = build_in_good_places(session,__sim_player)*BUILD_IN_GOOD_PLACES_WEIGHT
    __dev = dev_cards_heuristic(session,__sim_player) * DEV_CARDS_WEIGHT
    __won_game = game_won_heuristic(session,__sim_player)
    __enough_res_to_buy = enough_res_to_buy(session,__sim_player)*ENOUGH_RES_TO_BUY

    keep_res_you_cant_achieve(session,__sim_player,move)

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

    __builder_characteristic = __vp + __build + __roads+ __cities + __won_game # todo: pretty good combination

    return __builder_characteristic
    # return __diversity + __build + __won_game + __dev
