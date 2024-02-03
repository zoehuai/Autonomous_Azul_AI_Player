'''
This file aims to implement the AI agent to play Azul board game
and use game theory strategy to play against other teams and naive player.
Implementation: there have two parts to achieve the competition, the first part
is to select the moves by evaluating those moves' score, the second part is to predict
the best move by opponent and try to maximum our scores.
'''


from advance_model import *
from model import *
from utils import *
import time


class myPlayer(AdvancePlayer):

    # initialize
    # The following function should not be changed at all
    def __init__(self, _id):
        super().__init__(_id)

    # Each player is given 5 seconds when a new round started
    # If exceeds 5 seconds, all your code will be terminated and
    # you will receive a timeout warning

    # in case of the first step timeout
    def StartRound(self, game_state):
        moves = game_state.players[self.id].GetAvailableMoves(game_state)
        best_move = self.SelectMove(moves, game_state)
        return best_move

    # Each player is given 1 second to select next best move
    # If exceeds 5 seconds, all your code will be terminated,
    # a random action will be selected, and you will receive
    # a timeout warning

    def require_title(self, state):
        color = state.lines_tile
        number = state.lines_number
        num = []
        for i in range(5):
            num.append(i + 1 - number[i])
        return dict(zip([1, 2, 3, 4, 5],
                        [[color[0], num[0]], [color[1], num[1]], [color[2], num[2]], [color[3], num[3]],
                         [color[4], num[4]]]))

    # if there have a tile in the wall, I get the adjecent tile color, and tend to fill them to get bonus score
    def adjacent_color(self, state):
        new = numpy.zeros([7, 7])
        tile_wall = state.grid_state
        for i in range(1, 6):
            for j in range(1, 6):
                new[i, j] = tile_wall[i - 1, j - 1]
        new = new == 1
        index = []
        for i in range(1, 6):
            for j in range(1, 6):
                if not new[i][j]:
                    if new[i][j] != new[i + 1][j] or new[i][j] != new[i][j + 1] or new[i][j] != new[i - 1][j] or \
                            new[i][j] != new[i][j - 1]:
                        num = i * 10 + j
                        if num not in index:
                            index.append(num)
        temp = []
        k = 0
        adjacent_color = []
        for m in index:
            row = m // 10 - 1
            column = m % 10 - 1
            if row != k:
                k = k + 1
                adjacent_color.append(temp)
                temp = []
            if state.grid_scheme[row, column] == 0: temp_color = Tile.BLUE
            if state.grid_scheme[row, column] == 1: temp_color = Tile.YELLOW
            if state.grid_scheme[row, column] == 2: temp_color = Tile.RED
            if state.grid_scheme[row, column] == 3: temp_color = Tile.BLACK
            if state.grid_scheme[row, column] == 4: temp_color = Tile.WHITE
            temp.append(temp_color)
        adjacent_color.append(temp)
        return adjacent_color

    def choose_move(self, moves, game_state):
        centre = game_state.centre_pool
        centre_warning = centre.tiles

        # avoid > 3 appear in the centre
        accept_color = []
        for key in centre_warning:
            if centre_warning[key] < 1:
                accept_color.append(key)

        # existed color in the pattern line
        my_state = game_state.players[self.id]
        my_adjacent_color = self.adjacent_color(my_state)
        choose_move = []

        for mid, fid, tgrab in moves:
            my_to_pattern_line = tgrab.num_to_pattern_line
            my_number = tgrab.number
            grab_color = tgrab.tile_type
            my_floor = tgrab.num_to_floor_line

            if my_floor > 0:
                continue

            # using 3,4,5 tiles to fill in 3,4,5 pattern line
            if (my_to_pattern_line == 3 and my_number == 3) or (my_to_pattern_line == 4 and my_number == 4) or \
                    (my_to_pattern_line == 5 and my_number == 5):
                choose_move.append((mid, fid, tgrab))

            # if exist > 3 tiles and use it
            if my_number >= 3:
                choose_move.append((mid, fid, tgrab))

        if choose_move == []:
             for mid, fid, tgrab in moves:
                my_to_pattern_line = tgrab.num_to_pattern_line
                my_number = tgrab.number
                grab_color = tgrab.tile_type
                my_floor = tgrab.num_to_floor_line

                # no situation of >3, put first and second line at first
                if my_floor > 0:
                    continue

                if (my_to_pattern_line == 1 or my_to_pattern_line == 2) and my_number <= 2:
                    if grab_color in accept_color or grab_color in my_adjacent_color:
                       choose_move.append((mid, fid, tgrab))

        if choose_move == []:
            choose_move = moves
        return choose_move

    # select the best move
    def SelectMove(self, moves, game_state):

        best_move = None
        choose_move = self.choose_move(moves, game_state)

        max_my_score = 0
        max_opponent_score = 1000
        temp_opponent_score = 0

        next_my_move = None
        next_opponent_move = None

        for my_move in choose_move:
                my_state = copy.deepcopy(game_state)
                my_state.ExecuteMove(self.id, my_move)
                my_score = evaluate(my_state, self.id, my_move)

                opponent_score = 0
                opponent_moves = my_state.players[1 - self.id].GetAvailableMoves(my_state)
                choose_opponent_move = self.choose_move(opponent_moves, my_state)
                # predict the opponent score and move
                for opponent_move in choose_opponent_move:
                    opponent_state = copy.deepcopy(my_state)
                    opponent_state.ExecuteMove(1 - self.id, opponent_move)
                    opponent_score = evaluate(opponent_state, 1 - self.id, opponent_move)
                    if opponent_score > temp_opponent_score:
                        temp_opponent_score = opponent_score # the most likelihood score
                        next_opponent_move = opponent_move

                if my_score > max_my_score and temp_opponent_score < max_opponent_score:
                    max_my_score = my_score
                    max_opponent_score = opponent_score  # the most likelihood move for opponent
                    best_move = my_move

        if best_move is not None:
            return best_move
        else:
            return random.choice(moves)

# evaluation used to evaluate the score of a game state
def evaluate(state, id, move):
    state.players[id].ScoreRound()
    bouns = state.players[id].EndOfGameScore()
    score = state.players[id].score
    score = score + other_score(state, id) + bouns
    return score

# using the predict move to calculate the score will get
def other_score(state, id):
    situation = state.players[id].grid_state

    num_floor = state.players[id].floor
    score_floor = num_floor.count(1) * 2

    count_row = 0
    count_column = 0

    for i in range(0, 5):
        complete_row = 0
        for j in range(0, 5):
            if not situation[i][j]:
                if situation[i][j] == 1:
                    count_row = count_row + 1
                    complete_row = complete_row + 1
                    if situation[i][j] == situation[i][j+1]:
                        count_row = count_row + 1
                    if complete_row >= 2 :
                        count_row = count_row + 1*(5-i)

    for m in range(0, 5):
        complete_column = 0
        for n in range(0, 5):
             if not situation[n][m]:
                if situation[n][m] == 1:
                    count_column = count_column + 1
                    complete_column = complete_column+ 1
                    if situation[n][m] == situation[n+1][m]:
                        count_column = count_column + 1
                    if situation[i][j] == situation[i][j + 1]:
                        count_row = count_row + 1
                    if complete_column >= 3:
                        count_row = count_row + 3

    score = count_column + count_row - score_floor
    return score