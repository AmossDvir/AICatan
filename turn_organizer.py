PLAYERS_ORDER_SETUP = [1, 2, 3, 4, 4, 3, 2, 1]


def turn_gen():
    """
    generates the player id by it's turn
    :return: Iterable Object
    """
    turn = 1
    while True:
        if turn % 5 == 0:
            turn = 1
        yield turn
        turn += 1
