import GameSession
import Player
import Agent

# =========== analyze random
# my_file = open("result.txt", "w")
# for i in range(100):
#     p1 = Player.Player(Agent.RandomAgent(), "p1")
#     p2 = Player.Player(Agent.RandomAgent(), "p2")
#     p3 = Player.Player(Agent.RandomAgent(), "p3")
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
my_deep_file = open("prob result.txt", "w")
for i in range(10):
     deep = Player.Player(Agent.DeepAgent(), "D1")
     p2 = Player.Player(Agent.RandomAgent(), "p2")
     p3 = Player.Player(Agent.RandomAgent(), "p3")
     p4 = Player.Player(Agent.RandomAgent(), "p4")
     game = GameSession.GameSession(None, deep, p2, p3, p4)
     game.run_game()
     my_deep_file.write(game.winning_player.get_name() + '\n')

my_deep_file.close()
