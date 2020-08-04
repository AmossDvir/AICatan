from __future__ import annotations
from typing import Set, List, Tuple
from random import choice
from Dice import PROBABILITIES
from Buildables import Buildable
from Hand import Hand
from Moves import Move
import GameConstants as Consts
from GameSession import *
from Agent import *
import hexgrid


class Player:
    def __init__(self, player_id: int, agent: Agent):
        self.__agent = agent
        self.__id = player_id
        self.__resources_hand = Hand()
        self.__devs_hand = Hand()
        self.__used_devs = Hand()
        self.__settlement_nodes = []
        self.__city_nodes = []
        self.__road_edges = []
        self.__has_longest_road = False
        self.__has_largest_army = False
        self.__longest_road_len = 0
        self.__harbors = set()

    def vp(self) -> int:
        """
        :return: current number of victory points
        """
        vp = 0
        if self.has_largest_army():
            vp += Consts.VP_LARGEST_ARMY
        if self.has_longest_road():
            vp += Consts.VP_LONGEST_ROAD
        vp += self.num_settlements() * Consts.VP_SETTLEMENT
        vp += self.num_cities() * Consts.VP_CITY
        vp += self.num_roads() * Consts.VP_ROAD    # just in case
        vp += len([dev_card for dev_card in self.__used_devs if dev_card == Consts.DevType.VP]) * Consts.VP_DEV_CARD
        return vp

    def agent(self) -> Agent:
        return self.__agent

    def remove_settlement(self, node: int) -> None:
        self.settlement_nodes().remove(node)

    def __calc_road_len(self) -> int:
        graph = {}
        for edge in self.__road_edges:
            node1, node2 = hexgrid.nodes_touching_edge(edge)
            if node1 not in graph:
                graph[node1] = set()
            if node2 not in graph:
                graph[node2] = set()
            graph[node1].add(node2)
            graph[node2].add(node1)

        max_len = 0
        for start in graph:
            curr_len = 0
            max_curr_len = 0
            visited = set()
            stack = [start]
            while stack:
                curr = stack.pop()
                curr_len += 1
                visited.add(curr)
                added = False
                for neighbor in graph[curr]:
                    if neighbor not in visited:
                        stack.append(neighbor)
                        added = True
                if not added:
                    if max_curr_len < curr_len:
                        max_curr_len = curr_len
                    curr_len -= 1
            if max_len < max_curr_len:
                max_len = max_curr_len
        return max_len - 1

    def harbor_resources(self) -> List[Consts.ResourceType]:
        resources = []
        yielding_nodes = self.settlement_nodes() + self.city_nodes()
        for resource, locations in Consts.HARBOR_NODES.items():
            if any(n in locations for n in yielding_nodes):
                resources.append(resource)
                continue
        return resources

    def settlement_nodes(self) -> List[int]:
        return self.__settlement_nodes

    def city_nodes(self) -> List[int]:
        return self.__city_nodes

    def road_edges(self) -> List[int]:
        return self.__road_edges

    def get_id(self) -> int:
        """
        :return: this player's player id
        """
        return self.__id

    def has_longest_road(self) -> bool:
        """
        :return: True iff player currently has the longest road
        """
        return self.__has_longest_road

    def has_largest_army(self) -> bool:
        """
        :return: True iff player currently has the largest army
        """
        return self.__has_largest_army

    def resource_hand(self) -> Hand:
        return self.__resources_hand

    def dev_hand(self) -> Hand:
        return self.__devs_hand

    def num_settlements(self) -> int:
        """
        :return: current number of settlements player has on the board (0-5)
        """
        num_settles = len(self.__settlement_nodes)
        assert 0 <= num_settles <= Consts.MAX_SETTLEMENTS_PER_PLAYER
        return num_settles

    def num_cities(self) -> int:
        """
        :return: current number of cities player has on the board (0-4)
        """
        num_cities = len(self.__city_nodes)
        assert 0 <= num_cities <= Consts.MAX_CITIES_PER_PLAYER
        return num_cities

    def num_roads(self) -> int:
        """
        :return: current number of roads player has on the board (0-15)
        """
        num_roads = len(self.__road_edges)
        assert 0 <= num_roads <= Consts.MAX_ROADS_PER_PLAYER
        return num_roads

    def longest_road_length(self) -> int:
        """
        :return: current max road length (for longest road evaluation)
        """
        # TODO make some smart calculation over self.__road_edges to get this number,
        #  or check / increment longest_road_len every time road is built
        return self.__calc_road_len()

    def army_size(self) -> int:
        """
        :return: number of knights played by player
        """
        return sum(1 for dev_card in self.__used_devs if dev_card == Consts.DevType.KNIGHT)

    def resource_hand_size(self) -> int:
        """
        :return: number of resource cards player is holding
        """
        return len(self.__resources_hand)

    def dev_hand_size(self) -> int:
        """
        :return: number of development cards player is holding
        """
        return len(self.__devs_hand)

    def _probability_score(self) -> float:
        """
        :return: player's probability of getting any resource/s in a given turn, based on settlements / cities
        """
        rolls = set()
        for settlement_loc in self.__settlement_nodes:
            for hex_tile in settlement_loc.adj_hexes():
                rolls.add(hex_tile.roll())
        for city_loc in self.__city_nodes:
            for hex_tile in city_loc.adj_hexes():
                rolls.add(hex_tile.roll())
        prob = sum(PROBABILITIES.get(roll, 0) for roll in rolls)
        assert 0 <= prob <= 1
        return prob

    def _expectation_score(self) -> float:
        """
        :return: player's expected resource gain in a given turn, based on settlements / cities
        """
        rolls_amounts = []
        for settlement_loc in self.__settlement_nodes:
            for hex_tile in settlement_loc.adj_hexes():
                rolls_amounts.append((hex_tile.roll(), 1))
        for city_loc in self.__city_nodes:
            for hex_tile in city_loc.adj_hexes():
                rolls_amounts.append((hex_tile.roll(), 2))
        expected = sum(PROBABILITIES.get(roll, 0) * num_resources for roll, num_resources in rolls_amounts)
        assert expected >= 0
        return expected


    def info(self) -> str:
        return f'[PLAYER] player_id = {self.get_id()}, vp = {self.vp()}, agent = {type(self.agent())}, settlements = {[hex(s) for s in self.__settlement_nodes]}, ' \
               f'cities = {[hex(c) for c in self.__city_nodes]}, roads = {[hex(r) for r in self.__road_edges]}, ' \
               f'longest road = {self.__has_longest_road}, largest army = {self.__has_largest_army}, ' \
               f'resources = {self.resource_hand()}, devs = {self.__devs_hand}, devs_used = {self.__used_devs}'

    # modifiers #
    def set_longest_road(self, val: bool) -> None:
        self.__has_longest_road = val

    def set_largest_army(self, val: bool) -> None:
        self.__has_largest_army = val

    def use_dev(self, dtype: Consts.DevType) -> None:
        if dtype not in self.__devs_hand:
            raise ValueError(f'player {self.get_id()} cannot use dev card {dtype}, no such card in hand')
        else:
            used = Hand(dtype)
            self.__devs_hand.remove(used)
            self.__used_devs.insert(used)

    def receive_cards(self, cards: Hand) -> None:
        res_cards = cards.resources()
        dev_cards = cards.devs()
        self.__resources_hand.insert(res_cards)
        self.__devs_hand.insert(dev_cards)

    def throw_cards(self, cards: Hand) -> None:
        self.__resources_hand.remove(cards)

    def add_buildable(self, buildable: Buildable) -> None:
        btype = buildable.type()
        if btype == Consts.PurchasableType.SETTLEMENT:
            buildable_coords = self.__settlement_nodes
        elif btype == Consts.PurchasableType.CITY:
            # self.__settlement_nodes.remove(buildable.coord())   # city replaces existing settlement
            buildable_coords = self.__city_nodes
        else:
            buildable_coords = self.__road_edges
        buildable_coords.append(buildable.coord())

    # agent interface #
    def choose(self, moves: List[Move], state: GameSession) -> Move:
        """new choosing interface, should be cleaner"""
        return self.__agent.choose(moves, state)

    # def play(self, state: GameSession) -> List[Move]:
    #     """:returns a list of moves to be done in this turn"""
    #     return self.__agent.play(state)

    # def choose_robber_hex(self, state: GameSession) -> int:
    #     return self.__agent.choose_robber_hex(state)

    # def choose_settlement_and_road(self, state: GameSession) -> Tuple[int, int]:
    #     return self.__agent.choose_settlement_and_road(state)

    # def take_card_from(self, state: GameSession, possible_players: Set[int]) -> int:
    #     return self.__agent.take_card_from(state, possible_players)

    # def choose_cards_to_throw(self, state: GameSession,  num_cards: int) -> Hand:
    #     assert self.resource_hand_size() >= num_cards
    #     hand_to_throw = self.__agent.choose_cards_to_throw(state, num_cards)
    #     assert hand_to_throw.size() == num_cards
    #     return hand_to_throw

    # def choose_monopoly_card(self, state: GameSession) -> Consts.ResourceType:
    #     resource = self.__agent.choose_monopoly_card(state)
    #     assert resource in Consts.YIELDING_RESOURCES
    #     return resource

    # def choose_road_building(self, state: GameSession, num_roads: int) -> List[int]:
    #     road_coords = self.__agent.choose_road_building(state, num_roads)
    #     assert len(road_coords) == num_roads
    #     return road_coords

    # def choose_yop_resources(self, state: GameSession) -> Hand:
    #     resources = self.__agent.choose_yop_resources(state)
    #     assert resources.size() == Consts.YOP_NUM_RESOURCES
    #     return resources