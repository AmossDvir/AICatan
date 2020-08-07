import GameSession
import Player

# We don't need the session for this specific heuristic, but this is the general form:
def vp_heuristic(session:GameSession, player:Player) -> int:
    return player.vp()