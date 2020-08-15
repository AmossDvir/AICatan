import GameSession
import Player
import Agent
import Heuristics

# =========== analyze random
# my_file = open("result.txt", "w")
# for i in range(100):
#     p1 = Player.Player(Agent.RandomAgent(), "p1")
#     p2 = Player.Player(Agent.RandomAgent(), "p2")
#     p3 = Player.Player(Agent.\RandomAgent(), "p3")
#     p4 = Player.Player(Agent.RandomAgent(), "p4")
#     game = GameSession.GameSession(None, p1, p2, p3, p4)
#     game.run_game()
#     my_file.write(game.winning_player.get_name() + '\n')
#
# my_file.close()

# ======== analyze Probability agent
# my_prob_file = open("prob result.txt", "w")
# for i in range(10):
#      prob = Player.Player(Agent.ProbabilityAgent(), "p1")
#      p2 = Player.Player(Agent.RandomAgent(), "p2")
#      p3 = Player.Player(Agent.RandomAgent(), "p3")
#      p4 = Player.Player(Agent.RandomAgent(), "p4")
#      game = GameSession.GameSession(None, prob, p2, p3, p4)
#      game.run_game()
#      my_prob_file.write(game.winning_player.get_name() + '\n')
#
# my_prob_file.close()
#============== depp analyze
# my_deep_file = open("deep result.txt", "w")
# for i in range(1):
#     deep = Player.Player(Agent.DeepAgent(), "D1")
#     p2 = Player.Player(Agent.RandomAgent(), "p2")
#     p3 = Player.Player(Agent.RandomAgent(), "p3")
#     p4 = Player.Player(Agent.RandomAgent(), "p4")
#     game = GameSession.GameSession(None, deep, p2, p3, p4)
#     game.run_game()
#     my_deep_file.write(game.winning_player.get_name() + '\n')
#
# my_deep_file.close()

#============== heursitic analyz analyze
# my_h_file = open("h result.txt", "w")
# for i in range(10):
#      h = Player.Player(Agent.OneMoveHeuristicAgent(Heuristics.harbors_heuristic(h, game)), "D1")
#      p2 = Player.Player(Agent.RandomAgent(), "p2")
#      p3 = Player.Player(Agent.RandomAgent(), "p3")
#      p4 = Player.Player(Agent.RandomAgent(), "p4")
#      game = GameSession.GameSession(None, h, p2, p3, p4)
#      game.run_game()
#      my_h_file.write(game.winning_player.get_name() + '\n')
#
# my_h_file.close()

# #============== expitmax analyze
# my_exp_file = open("expect result.txt", "w")
# for i in range(2):
#     E1 = Player.Player(Agent.ExpectimaxProbAgent(Heuristics.vp_heuristic, 1, 2), "E1")
#     p2 = Player.Player(Agent.RandomAgent(), "p2")
#     p3 = Player.Player(Agent.RandomAgent(), "p3")
#     p4 = Player.Player(Agent.RandomAgent(), "p4")
#     game = GameSession.GameSession(None, E1, p2, p3, p4)
#     game.run_game()
#     my_exp_file.write(game.winning_player.get_name() + '\n')
#
# my_exp_file.close()

#======================= analyze Huerstics - one move:

my_one_move = open("one_move.txt", "w")
# my_one_move.write("everything_heuristic againt prob\n")
# for i in range(10):
#     E1 = Player.Player(Agent.OneMoveHeuristicAgent(Heuristics.everything_heuristic), "E1")
#     p2 = Player.Player(Agent.OneMoveHeuristicAgent(Heuristics.probability_score_heuristic), "E2")
#     p3 = Player.Player(Agent.RandomAgent(), "p3")
#     p4 = Player.Player(Agent.RandomAgent(), "p4")
#     game = GameSession.GameSession(None, E1, p2, p3, p4)
#     game.run_game()
#     my_one_move.write(game.winning_player.get_name() + '\n')

my_one_move.write("exptimaxprob\n")
for i in range(20):
    E = Player.Player(Agent.MonteCarloAgent(Heuristics.everything_heuristic), "E")
    RE = Player.Player(Agent.MonteCarloAgent(Heuristics.relative_everything_heuristic), "RE")
    P = Player.Player(Agent.MonteCarloAgent(Heuristics.probability_score_heuristic), "P")
    R4 = Player.Player(Agent.RandomAgent(), "R4")
    game = GameSession.GameSession(None, E, RE, P, R4)
    game.run_game()
    my_one_move.write(str(game.winning_player) + '\n')

my_one_move.close()
