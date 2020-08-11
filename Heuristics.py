import GameSession
import Player


# We don't need the session for this specific heuristic, but this is the general form:
def vp_heuristic(session: GameSession, player: Player) -> float:
    for sim_player in session.players():
        if sim_player.get_id() == player.get_id():
            return sim_player.vp()
    return 0


def probability_score_heuristic(session: GameSession, player: Player) -> float:
    for p in session.players():
        if p.get_id() == player.get_id():
            return session.board()._probability_score(p) + session.board()._expectation_score(p)


def road_len_heuristic(session: GameSession, player: Player) -> float:
    return session.board().road_len(player)


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
