import GameSession
import Player
import GameConstants as Consts
import Dice
from copy import deepcopy
from itertools import combinations

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
GAME_WON_WEIGHT = 1
ENOUGH_RES_TO_BUY_WEIGHT = 1
AVOID_THROW_WEIGHT = 0.01
DEFAULT_LINEAR_COMB_SIZE = 11
DEFAULT_LINEAR_COMB = (1,) * DEFAULT_LINEAR_COMB_SIZE


class Heuristic:
    """
    a superior class, creates an Heuristic object
    """
    def __init__(self, normalization: float = 1):
        self.norm = normalization

    def _calc(self, session: GameSession, player: Player) -> float:
        raise NotImplemented

    def value(self, session: GameSession, player: Player) -> float:
        for p in session.players():
            if p == player:
                player = p
                break
        return self._calc(session, player) * self.norm


class VictoryPoints(Heuristic):
    """A Heuristic based on the number of victory Points"""

    def __init__(self, normalization: float = 1 / Consts.WINNING_VP):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        return player.vp()


class Harbors(Heuristic):
    """A Heuristic based on the number of Harbors owned"""

    def __init__(self, normalization: float = 1 / len(Consts.HARBOR_NODES.values())):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        return len(player.harbors())


class GameWon(Heuristic):
    """A Heuristic based on winner of the game"""

    def _calc(self, session: GameSession, player: Player) -> float:
        if session.winner() is not None:
            return INF if session.winner() == player else -INF
        return 0


class Roads(Heuristic):
    """A Heuristic based on the number of Harbors owned"""

    def __init__(self, normalization: float = 1 / Consts.MAX_ROADS_PER_PLAYER):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        return player.num_roads()


class Settlements(Heuristic):
    """A Heuristic based on the number of settlements owned"""

    def __init__(self, normalization: float = 1 / Consts.MAX_SETTLEMENTS_PER_PLAYER):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        return player.num_settlements()


class AvoidThrow(Heuristic):
    """A Heuristic based on avoiding large hands"""

    def __init__(self, normalization: float = 1 / (Consts.MAX_CARDS_IN_HAND + 1)):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        res_size = player.resource_hand().size()
        if res_size > Consts.MAX_CARDS_IN_HAND:
            return Consts.MAX_CARDS_IN_HAND - res_size
        return 0


class Cities(Heuristic):
    """A Heuristic based on avoiding large hands"""

    def __init__(self, normalization: float = 1 / Consts.MAX_CITIES_PER_PLAYER):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        return player.num_cities()


class DevCards(Heuristic):
    """A Heuristic based on collecting and using development cards"""

    def __init__(self, normalization: float = 1 / (Consts.NUM_DEVS + 1)):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        return player.dev_hand().size() + 2 * player.used_dev_hand().size()


class ResourceDiversity(Heuristic):
    """A Heuristic based on preferring diversified hands"""

    def __init__(self, normalization: float = 1 / len(Consts.YIELDING_RESOURCES)):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        num_types = len(set([card for card in player.resource_hand()]))
        return num_types


class BuildInGoodPlaces(Heuristic):
    """A Heuristic based on preferring building on higher probabilities"""

    def __init__(self, normalization: float = 1 / 227.5):  # 227.5 is the bound
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        board = session.board()
        tiles_types = set()
        num_tiles = 0
        tiles_prob = 0
        for node in player.settlement_nodes():
            for tile in board.get_adj_tile_ids_to_node(node):
                num_tiles += 1
                tiles_types.add(board.hexes()[tile].resource())
                tiles_prob += Dice.PROBABILITIES[board.hexes()[tile].token()]
        return num_tiles * len(tiles_types) * tiles_prob


class EnoughResources(Heuristic):
    """A Heuristic based on preferring hands that can buy many Purchasables"""

    def __init__(self, normalization: float = 1 / 3):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        hand = player.resource_hand()
        road_score = 0.5
        settle_score = 1
        city_score = 1.5
        dev_card_score = 1
        score = 0

        if hand.contains(Consts.COSTS[Consts.PurchasableType.ROAD]):
            score += road_score
        if hand.contains(Consts.COSTS[Consts.PurchasableType.SETTLEMENT]):
            score += settle_score
        if hand.contains(Consts.COSTS[Consts.PurchasableType.CITY]):
            score += city_score
        if hand.contains(Consts.COSTS[Consts.PurchasableType.DEV_CARD]):
            score += dev_card_score

        return score


class PreferResourcesPerStage(Heuristic):
    """A Heuristic that gives priority for having bricks and woods in the
    the early stages of the game and having sheep, ore and wheat in
    the advanced phase of the game."""

    def __init__(self, normalization: float = 1 / 150):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
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

        __calc_score = (100 * (0.8 * __num_forest +
                               1.2 * __num_bricks +
                               0.3 * __num_sheep +
                               0.3 * __num_wheat) /
                        (__num_buildings * (1 +
                                            0.75 * __num_sheep +
                                            0.75 * __num_wheat +
                                            1.5 * __num_ore)))
        return __calc_score


class Probability(Heuristic):
    """A Heuristic based on board probabilities and buildable placements"""

    def _calc(self, session: GameSession, player: Player) -> float:
        return sum((session.board().probability_score(player),
                    session.board().expectation_score(player),
                    session.potential_probability_score(player)))


class LongestRoad(Heuristic):
    """A Heuristic based on longest road length"""

    def __init__(self, normalization: float = 1 / Consts.MAX_ROADS_PER_PLAYER):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        return session.board().road_len(player)


class OpponentScore(Heuristic):
    """A Heuristic based on max opponent score"""

    def __init__(self, normalization=1):
        super().__init__(normalization)
        self.vp = VictoryPoints()
        self.hand_size = ...
        self.road = LongestRoad()

    def _calc(self, session: GameSession, player: Player) -> float:
        max_vp_player = max([p for p in session.players() if p != player], key=lambda p: p.vp())
        opp_score = (hand_size_heuristic(session, max_vp_player) +
                     10 * self.vp.value(session, max_vp_player) +
                     1.5 * self.road.value(session, max_vp_player))
        return (1 / opp_score) if opp_score != 0 else 0


class CanBuy(Heuristic):
    """A Heuristic based on Purchasable buying power"""

    def __init__(self, normalization: float = 1 / 15):
        super().__init__(normalization)
        self.vp = VictoryPoints()
        self.hand_size = ...
        self.road = LongestRoad()

    def _calc(self, session: GameSession, player: Player) -> float:
        num_affordable = 0
        my_hand = player.resource_hand()
        contained = False
        for purchasable, cost in Consts.COSTS.items():
            if my_hand.contains(cost):
                num_affordable += 1
                contained = True
            cost_copy = deepcopy(cost)
            cost_copy.insert(cost)
            if my_hand.contains(cost_copy):
                num_affordable += 2

        if contained:
            contained = False
            for purch1, purch2 in combinations(Consts.PurchasableType, 2):
                tot_cost = deepcopy(Consts.COSTS[purch1])
                tot_cost.insert(Consts.COSTS[purch2])
                if my_hand.contains(tot_cost):
                    contained = True
                    num_affordable += 2
        if contained:
            for purch1, purch2, purch3 in combinations(Consts.PurchasableType, 3):
                tot_cost = deepcopy(Consts.COSTS[purch1])
                tot_cost.insert(Consts.COSTS[purch2])
                tot_cost.insert(Consts.COSTS[purch3])
                if my_hand.contains(tot_cost):
                    num_affordable += 3
        return num_affordable


class HandSize(Heuristic):
    """A Heuristic based on preferring large hands up to threshold"""

    def __init__(self, normalization: float = 1 / Consts.MAX_CARDS_IN_HAND):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        return min(player.resource_hand_size(), Consts.MAX_CARDS_IN_HAND)


class HandDiversity(Heuristic):
    """A Heuristic based on preferring diverse hands"""

    def __init__(self, normalization: float = 1 / len(Consts.YIELDING_RESOURCES)):
        super().__init__(normalization)

    def _calc(self, session: GameSession, player: Player) -> float:
        num_unique_resources = 0
        for resource in Consts.ResourceType:
            if player.resource_hand().cards_of_type(resource).size() > 0:
                num_unique_resources += 1
        return num_unique_resources


class Everything(Heuristic):
    """A Heuristic based on multiple sub-heuristics"""

    def __init__(self, normalization=1, weights=(1, 30, 1.5, 1, 0.1, 0.1, 2.5, 1, 0.1, 1)):
        super().__init__(normalization)
        self.heuristics = (Probability(),
                           VictoryPoints(),
                           LongestRoad(),
                           GameWon(),
                           HandSize(),
                           HandDiversity(),
                           DevCards(),
                           CanBuy(),
                           OpponentScore())
        self.weights = weights

    def _calc(self, session: GameSession, player: Player) -> float:
        return sum(h.value(session, player) * w for h, w in zip(self.heuristics, self.weights))


class Main(Heuristic):
    """A Heuristic based on multiple sub-heuristics"""
    VP_WEIGHT = 2  # victory points heuristic weight
    PREFER_RESOURCES_WEIGHT = 0.2
    HARBOURS_WEIGHT = 0.8
    DIVERSITY_WEIGHT = 0.5
    BUILD_IN_GOOD_PLACES_WEIGHT = 5
    ROADS_WEIGHT = 0.6
    SETTLES_WEIGHT = 0.7
    CITIES_WEIGHT = 2.5
    DEV_CARDS_WEIGHT = 2
    GAME_WON_WEIGHT = 1
    ENOUGH_RES_TO_BUY_WEIGHT = 1
    AVOID_THROW_WEIGHT = 0.01

    def __init__(self, normalization=1, weights=(VP_WEIGHT,
                                                 HARBOURS_WEIGHT,
                                                 PREFER_RESOURCES_WEIGHT,
                                                 ROADS_WEIGHT,
                                                 SETTLES_WEIGHT,
                                                 CITIES_WEIGHT,
                                                 DIVERSITY_WEIGHT,
                                                 BUILD_IN_GOOD_PLACES_WEIGHT,
                                                 DEV_CARDS_WEIGHT,
                                                 GAME_WON_WEIGHT,
                                                 ENOUGH_RES_TO_BUY_WEIGHT,
                                                 AVOID_THROW_WEIGHT)):
        super().__init__(normalization)
        self.heuristics = (VictoryPoints(),
                           Harbors(),
                           PreferResourcesPerStage(),
                           Roads(),
                           Settlements(),
                           Cities(),
                           ResourceDiversity(),
                           BuildInGoodPlaces(),
                           DevCards(),
                           GameWon(),
                           EnoughResources(),
                           AvoidThrow())
        self.weights = weights

    def _calc(self, session: GameSession, player: Player) -> float:
        return sum(h.value(session, player) * w for h, w in zip(self.heuristics, self.weights))


class BuilderCharacteristic(Main):
    BUILDER_WEIGHTS = (1, 0.01, 0.01, 1, 0.01, 1, 0.01, 1, 0.01, 1, 0.01, 0.01)

    def __init__(self, normalization=1, weights=BUILDER_WEIGHTS):
        super().__init__(normalization, weights)


class AmossComb1(Main):
    COMB1_WEIGHTS = (Main.VP_WEIGHT,
                     0.01,
                     0.01,
                     Main.ROADS_WEIGHT,
                     0.01,
                     Main.CITIES_WEIGHT,
                     0.01,
                     Main.BUILD_IN_GOOD_PLACES_WEIGHT,
                     Main.DEV_CARDS_WEIGHT,
                     Main.GAME_WON_WEIGHT,
                     0.01,
                     Main.AVOID_THROW_WEIGHT)

    def __init__(self, normalization=1, weights=COMB1_WEIGHTS):
        super().__init__(normalization, weights)


class AmossComb2(Main):
    COMB2_WEIGHTS = (Main.VP_WEIGHT,
                     0.01,
                     0.01,
                     0.01,
                     0.01,
                     0.01,
                     0.01,
                     Main.BUILD_IN_GOOD_PLACES_WEIGHT,
                     Main.DEV_CARDS_WEIGHT,
                     Main.GAME_WON_WEIGHT,
                     0.01,
                     0.01)

    def __init__(self, normalization=1, weights=COMB2_WEIGHTS):
        super().__init__(normalization, weights)


class AmossComb3(Main):
    COMB3_WEIGHTS = (Main.VP_WEIGHT,
                     0.01,
                     0.01,
                     0.01,
                     0.01,
                     0.01,
                     Main.DIVERSITY_WEIGHT,
                     Main.BUILD_IN_GOOD_PLACES_WEIGHT,
                     0.01,
                     Main.GAME_WON_WEIGHT,
                     0.01,
                     Main.AVOID_THROW_WEIGHT)

    def __init__(self, normalization=1, weights=COMB3_WEIGHTS):
        super().__init__(normalization, weights)


class AmossComb4(Main):
    COMB4_WEIGHTS = (Main.VP_WEIGHT,
                     0.01,
                     Main.PREFER_RESOURCES_WEIGHT,
                     0.01,
                     0.01,
                     0.01,
                     0.01,
                     Main.BUILD_IN_GOOD_PLACES_WEIGHT,
                     Main.DEV_CARDS_WEIGHT,
                     Main.GAME_WON_WEIGHT,
                     0.01,
                     Main.AVOID_THROW_WEIGHT)

    def __init__(self, normalization=1, weights=COMB4_WEIGHTS):
        super().__init__(normalization, weights)


def vp_heuristic(session, player):
    return player.vp() / 10


def harbors_heuristic(session: GameSession, player: Player):
    """
    the more harbors - the higher the score gets
    :param session: a GameSession
    :param player: a Player
    :return: Integer, the score for the given game session
    """
    return len(player.harbors()) / 9


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
    avg_opp = sum(opp_vals) / len(opp_vals)
    if avg_opp == 0:
        return INF
    else:
        return my_val / avg_opp


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

    __calc_score = (100 * (0.8 * __num_forest +
                           1.2 * __num_bricks +
                           0.3 * __num_sheep +
                           0.3 * __num_wheat) /
                    (__num_buildings * (1 +
                                        0.75 * __num_sheep +
                                        0.75 * __num_wheat +
                                        1.5 * __num_ore)))
    return __calc_score / 150


def roads_heuristic(session: GameSession, player: Player):
    """
    :return: the number of roads the player has, divided by 15 (so between 0 to 1)
    """
    return player.num_roads() / 15  # 15 roads max per player


def settles_heuristic(session: GameSession, player: Player):
    """
    :return: the number of settlements the player has, divided by 5 (so between 0 to 1)
    and if the player has more that 5, the function returns 0
    """
    __settles = player.num_settlements()
    if __settles >= 5:
        return 0
    return __settles / 5  # 5 settlements max per player


def avoid_throwing_cards(session: GameSession, player: Player):
    """
    prefer use cards if the player has more than 7 and not keeping them in hand
    :return: a negative number decreasing
     relatively to the number of cards the player has
    """
    res_size = player.resource_hand().size()
    max_cards = Consts.MAX_CARDS_IN_HAND
    if res_size > max_cards:
        return -((res_size - max_cards) / (max_cards + 1))

    return 0


def cities_heuristic(session: GameSession, player: Player):
    """
    :return: the number of cities the player has, divided by 4 (so between 0 to 1)
    """
    return player.num_cities() / 4  # 4 cities max per player


def dev_cards_heuristic(session: GameSession, player: Player):
    """
    :return: the number of development cards the player has, divided by the
    size if the stack on the deck (so between 0 to 1)
    """
    return (player.dev_hand().size() + player.used_dev_hand().size() * 2) / 26


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
    return __num_types / 5


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
    return (num_tiles * len(tiles_types) * tiles_prob) / 227.5  # 227.5 is the bound


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
    # print(__hand)
    return (__road_score + __settle_score + __city_score + __dev_card_score) / 3


def probability_score_heuristic(session: GameSession, player: Player) -> float:
    return session.board().probability_score(player) + \
           session.board().expectation_score(player) + \
           session.potential_probability_score(player)


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
    optimal_hand_size = 7
    return min(player.resource_hand_size(), optimal_hand_size) / optimal_hand_size


def hand_diversity_heuristic(session, player):
    """
    prefer having more diversity in the player's hand
    :return:
    """
    max_resource_types = len(Consts.YIELDING_RESOURCES)
    num_unique_resources = 0
    for resource in Consts.ResourceType:
        if player.resource_hand().cards_of_type(resource).size() > 0:
            num_unique_resources += 1
    return num_unique_resources / max_resource_types


def everything_heuristic(session: GameSession, player: Player) -> float:
    for p in session.players():
        if p.get_id() == player.get_id():
            player = p
    prob = 1 * probability_score_heuristic(session, player)
    vp = 30 * vp_heuristic(session, player)
    road = 1.5 * road_len_heuristic(session, player)
    won = game_won_heuristic(session, player)
    hsize = 0  # hand_size_heuristic(session, player)
    hdiverse = 0  # hand_diversity_heuristic(session, player)
    devs = 2.5 * dev_cards_heuristic(session, player)
    purchases = affordable_purchasables_heuristic(session, player)
    legal_hand = 0  # legal_hand_heuristic(session, player)
    opp_score = opp_score_heuristic(session, player)
    s = sum([prob, vp, road, won, hsize, hdiverse, devs, purchases, legal_hand, opp_score])
    # print('player', player, 'prob', round(prob,3), 'vp', round(vp,3), 'road', round(road,3),
    #       'won', round(won,3), 'hsize', round(hsize,3), 'hdiverse', round(hdiverse,3), 'devs', round(devs,3),
    #       'purchasables', round(purchases,3), 'legal hand', legal_hand, 'sum =', s)
    return s


def opp_score_heuristic(session, player):
    max_vp_player = max([p for p in session.players() if p != player], key=lambda p: p.vp())
    opp_score = (hand_size_heuristic(session, max_vp_player) +
                 10 * vp_heuristic(session, max_vp_player) +
                 1.5 * road_len_heuristic(session, max_vp_player))
    return (1 / opp_score) if opp_score != 0 else 0


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
        if my_hand.contains(cost):
            num_affordable += 1
            contained = True
        cost_copy = deepcopy(cost)
        cost_copy.insert(cost)
        if my_hand.contains(cost_copy):
            num_affordable += 2

    if contained:
        contained = False
        for purch1, purch2 in combinations(Consts.PurchasableType, 2):
            tot_cost = deepcopy(Consts.COSTS[purch1])
            tot_cost.insert(Consts.COSTS[purch2])
            if my_hand.contains(tot_cost):
                contained = True
                num_affordable += 2
    if contained:
        for purch1, purch2, purch3 in combinations(Consts.PurchasableType, 3):
            tot_cost = deepcopy(Consts.COSTS[purch1])
            tot_cost.insert(Consts.COSTS[purch2])
            tot_cost.insert(Consts.COSTS[purch3])
            if my_hand.contains(tot_cost):
                num_affordable += 3
    return num_affordable / 15


def main_heuristic(session: GameSession, player: Player):
    """
    calculates of score of each and every heuristic
    and returns a linear combination of them
    :param session:
    :param player:
    :return:
    """

    __sim_player = find_sim_player(session, player)
    __vp = vp_heuristic(session, __sim_player) * VP_WEIGHT
    __harbours = harbors_heuristic(session, __sim_player) * HARBOURS_WEIGHT
    __prefer = prefer_resources_in_each_part(session, __sim_player) * PREFER_RESOURCES_WEIGHT
    __roads = roads_heuristic(session, __sim_player) * ROADS_WEIGHT
    __settles = settles_heuristic(session, __sim_player) * SETTLES_WEIGHT
    __cities = cities_heuristic(session, __sim_player) * CITIES_WEIGHT
    __diversity = resources_diversity_heuristic(session, __sim_player) * DIVERSITY_WEIGHT
    __build = build_in_good_places(session, __sim_player) * BUILD_IN_GOOD_PLACES_WEIGHT
    __dev = dev_cards_heuristic(session, __sim_player) * DEV_CARDS_WEIGHT
    __won_game = game_won_heuristic(session, __sim_player)
    __enough_res_to_buy = enough_res_to_buy(session, __sim_player) * ENOUGH_RES_TO_BUY_WEIGHT

    __sum_score = sum((__vp,
                       __harbours,
                       __roads,
                       __settles,
                       __cities,
                       __build,
                       __dev,
                       __won_game,
                       __diversity,
                       __enough_res_to_buy,
                       __prefer))

    __builder_characteristic = sum((__vp,
                                    __build,
                                    __roads,
                                    __cities,
                                    __won_game))

    return __builder_characteristic


def linear_heuristic(session: GameSession, player: Player, weights=DEFAULT_LINEAR_COMB):
    """
    calculates of score of each and every heuristic
    and returns a linear combination of them based of vector, which is 11 places long
    :return: The evaluated value
    """
    __sim_player = find_sim_player(session, player)
    heuristics = (vp_heuristic(session, __sim_player),
                  harbors_heuristic(session, __sim_player),
                  prefer_resources_in_each_part(session, __sim_player),
                  roads_heuristic(session, __sim_player),
                  settles_heuristic(session, __sim_player),
                  cities_heuristic(session, __sim_player),
                  resources_diversity_heuristic(session, __sim_player),
                  build_in_good_places(session, __sim_player),
                  dev_cards_heuristic(session, __sim_player),
                  game_won_heuristic(session, __sim_player),
                  enough_res_to_buy(session, __sim_player))

    lin = sum(heuristic * weight for heuristic, weight in zip(heuristics, weights))
    return lin


def heuristic_comb1(session: GameSession, player: Player):
    __sim_player = find_sim_player(session, player)
    __vp = vp_heuristic(session, __sim_player) * VP_WEIGHT
    # __harbours = harbors_heuristic(session, __sim_player) * HARBOURS_WEIGHT
    # __prefer = prefer_resources_in_each_part(session, __sim_player) * PREFER_RESOURCES_WEIGHT
    __roads = roads_heuristic(session, __sim_player) * ROADS_WEIGHT
    # __settles = settles_heuristic(session, __sim_player) * SETTLES_WEIGHT
    __cities = cities_heuristic(session, __sim_player) * CITIES_WEIGHT
    # __diversity = resources_diversity_heuristic(session, __sim_player) * DIVERSITY_WEIGHT
    __build = build_in_good_places(session, __sim_player) * BUILD_IN_GOOD_PLACES_WEIGHT
    __dev = dev_cards_heuristic(session, __sim_player) * DEV_CARDS_WEIGHT
    __won_game = game_won_heuristic(session, __sim_player)
    # __enough_res_to_buy = enough_res_to_buy(session, __sim_player) * ENOUGH_RES_TO_BUY
    __avoid_throw = avoid_throwing_cards(session, __sim_player)

    return __vp + __build + __roads + __cities + __won_game + __dev + __avoid_throw


def heuristic_comb2(session: GameSession, player: Player):
    __sim_player = find_sim_player(session, player)
    __vp = vp_heuristic(session, __sim_player) * VP_WEIGHT
    # __harbours = harbors_heuristic(session, __sim_player) * HARBOURS_WEIGHT
    # __prefer = prefer_resources_in_each_part(session, __sim_player) * PREFER_RESOURCES_WEIGHT
    # __roads = roads_heuristic(session, __sim_player) * ROADS_WEIGHT
    # __settles = settles_heuristic(session, __sim_player) * SETTLES_WEIGHT
    # __cities = cities_heuristic(session, __sim_player) * CITIES_WEIGHT
    # __diversity = resources_diversity_heuristic(session, __sim_player) * DIVERSITY_WEIGHT
    __build = build_in_good_places(session, __sim_player) * BUILD_IN_GOOD_PLACES_WEIGHT
    __dev = dev_cards_heuristic(session, __sim_player) * DEV_CARDS_WEIGHT
    __won_game = game_won_heuristic(session, __sim_player)
    # __enough_res_to_buy = enough_res_to_buy(session, __sim_player) * ENOUGH_RES_TO_BUY
    # __avoid_throw = avoid_throwing_cards(session, __sim_player)

    return __vp + __build + __won_game + __dev


def heuristic_comb3(session: GameSession, player: Player):
    __sim_player = find_sim_player(session, player)
    __vp = vp_heuristic(session, __sim_player) * VP_WEIGHT
    # __harbours = harbors_heuristic(session, __sim_player) * HARBOURS_WEIGHT
    # __prefer = prefer_resources_in_each_part(session, __sim_player) * PREFER_RESOURCES_WEIGHT
    # __roads = roads_heuristic(session, __sim_player) * ROADS_WEIGHT
    # __settles = settles_heuristic(session, __sim_player) * SETTLES_WEIGHT
    # __cities = cities_heuristic(session, __sim_player) * CITIES_WEIGHT
    __diversity = resources_diversity_heuristic(session, __sim_player) * DIVERSITY_WEIGHT
    __build = build_in_good_places(session, __sim_player) * BUILD_IN_GOOD_PLACES_WEIGHT
    # __dev = dev_cards_heuristic(session, __sim_player) * DEV_CARDS_WEIGHT
    __won_game = game_won_heuristic(session, __sim_player)
    # __enough_res_to_buy = enough_res_to_buy(session, __sim_player) * ENOUGH_RES_TO_BUY
    __avoid_throw = avoid_throwing_cards(session, __sim_player)

    return __vp + __avoid_throw + __won_game + __build + __diversity


def heuristic_comb4(session: GameSession, player: Player):
    __sim_player = find_sim_player(session, player)
    __vp = vp_heuristic(session, __sim_player) * VP_WEIGHT
    # __harbours = harbors_heuristic(session, __sim_player) * HARBOURS_WEIGHT
    __prefer = prefer_resources_in_each_part(session, __sim_player) * PREFER_RESOURCES_WEIGHT
    # __roads = roads_heuristic(session, __sim_player) * ROADS_WEIGHT
    __settles = settles_heuristic(session, __sim_player) * SETTLES_WEIGHT
    # __cities = cities_heuristic(session, __sim_player) * CITIES_WEIGHT
    # __diversity = resources_diversity_heuristic(session, __sim_player) * DIVERSITY_WEIGHT
    __build = build_in_good_places(session, __sim_player) * BUILD_IN_GOOD_PLACES_WEIGHT
    __dev = dev_cards_heuristic(session, __sim_player) * DEV_CARDS_WEIGHT
    __won_game = game_won_heuristic(session, __sim_player)
    # __enough_res_to_buy = enough_res_to_buy(session, __sim_player) * ENOUGH_RES_TO_BUY
    __avoid_throw = avoid_throwing_cards(session, __sim_player)

    return __prefer + __build + __won_game + __vp + __dev + __avoid_throw


def find_sim_player(session: GameSession, player: Player) -> Player:
    # find the player's turn for the current session simulation
    for sim_player in session.players():
        if sim_player.get_id() == player.get_id():
            return sim_player
