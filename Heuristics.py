import GameSession
import Player

# We don't need the session for this specific heuristic, but this is the general form:
def vp_heuristic(session:GameSession, player:Player) -> int:
    for sim_player in session.players():
        if sim_player.get_id() == player.get_id():
            return sim_player.vp()
    return 0