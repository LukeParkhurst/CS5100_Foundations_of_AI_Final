import random
import eval_cards
from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.poker_constants import PokerConstants
import pypokerengine.engine.action_checker
from pypokerengine.utils.card_utils import _pick_unused_card, _fill_community_card, gen_cards, evaluate_hand
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.engine.game_evaluator import GameEvaluator
from pypokerengine.engine import action_checker
from pypokerengine.engine import dealer
from pypokerengine.engine import player
from pypokerengine.utils import action_utils
from pypokerengine.engine.table import Table
from pypokerengine.engine.seats import Seats
from pypokerengine.engine.player import Player
from pypokerengine.utils import card_utils
import unittest

class PokerBot(BasePokerPlayer):
    def __init__(self, startingAlg=-1):
        super().__init__()
        # Initialize bot using a random implemented algorithm if user does not select one.
        self.algID = startingAlg
        if startingAlg == -1:
            self.algID = random.randint(0, 3)

        #self.valid_actions = {'call':1, 'raise':2, 'fold':3}
        self.game_info = {}
        self.hole_card = gen_cards(['C2', 'S2'])
        self.community_card = gen_cards(['SK','H2','H6','CQ','D4'])
        self.round_state = {}
        self.round_count = 0
        self.opponent_state = {}
        self.street = ""
        self.new_action = {} # new action is the same as a valid action with a user id in front position
        self.winners = {} # similar to an entry in opponent_state but with bot itself as a possiblity
        self.opponent_hand = []
        self.score = 0
        self.tb = Table()
        self.game_eval = GameEvaluator()
        self.player1 = Player(1, 1000, "Andy")
        self.player2 = Player(2, 1000, "Rowbie")
        self.player3 = Player(3, 1000, "Luke")
        self.tb.seats.sitdown(self.player1)
        self.tb.seats.sitdown(self.player2)
        self.tb.seats.sitdown(self.player3)
        self.pot = GameEvaluator.create_pot(self.tb.seats.players)[0]

    def set_algorithm(self, algID):
        # A debug function allowing someone to set the bot's algorithm at any time.
        self.algID = algID



    '''
    def run_algorithm(self, info_to_pass):
        if self.algID == 0:
            play_suggestion, util = self.minimax(info_to_pass)
        elif self.algID == 1:
            play_suggestion, util = self.expectimax(info_to_pass)
        elif self.algID == 2:
            play_suggestion, util = self.mdp(info_to_pass)
        elif self.algID == 3:
            play_suggestion, util = self.alphaBeta(info_to_pass)

        #self.bluff(play_suggestion, util)
    '''

    def evaluation(self, player):
        total = 0
        paid_sum = player.paid_sum()
        initial_stack = player.stack
        current_money = initial_stack - paid_sum

        for i in self.tb.seats.players:
            current = i.stack-i.paid_sum()
            total+=current
        opponent_money = total/len(self.tb.seats.players)
        print(self.pot['amount'])

        ''''
        money_state
        opponents_money
        scared = 0
        if initial_stack-paid_sum-money_state<0:
            return -999
        if opponents_money>current_money:
            scared = current_money-opponents_money
        else:
            scared = current_money-opponents_money
        getMainPot, getPayInfo
        '''
        sum = current_money-0.8*opponent_money+self.pot['amount']
        return sum

    # def minimax(self, info_to_pass):
    def minimax(self, player, player_pos, depth, current_depth, numberOfPlayers, valid_actions, sb_amount=0 ):
        community = self.round_state['community_card']
        hole = self.hole_card
        current_depth += 1
        score = 0
        if depth * numberOfPlayers == current_depth:
            # return self.bluff(score, hole, community), score
            score = self.evaluation(self.tb.seats.players[player_pos])
            print(score)
            return self.bluff(score, hole, community, valid_actions)
        if current_depth % numberOfPlayers == 0:
            score = float('-Inf')
            for action in valid_actions:
                max_move, result = self.minimax(player, self.tb.next_active_player_pos(player_pos), depth,
                                                current_depth, numberOfPlayers, valid_actions, sb_amount)
                if result > score:
                    score = result
                    move = action

            # move = self.bluff(score, hole, community)
            return move, score

        else:
            score = float('Inf')
            for action in valid_actions:
                min_move, result = self.minimax(player, self.tb.next_active_player_pos(player_pos), depth,
                                                current_depth, numberOfPlayers, valid_actions, sb_amount)
                if result < score:
                    score = result
                    move = action
            # move = self.bluff(score, hole, community)
            return move, score
    
    def expectimax(self, info_to_pass):
        play_suggestion = None; util = 0
        return play_suggestion, util
    def mdp(self, info_to_pass):
        play_suggestion = None; util = 0
        return play_suggestion, util
    def alpha_beta_pruning(self, players, player_pos, depth, current_depth, numberOfPlayers, sb_amount = 0, alpha = 99999, beta = -99999,index = 0):
        community = self.round_state['community_card']
        hole = self.hole_card
        current_depth += 1
        score = 0
        if depth * numberOfPlayers == current_depth:
            return self.bluff(score, hole, community), score

        if current_depth == numberOfPlayers or current_depth == 0:
            max_value = float('-Inf')
            movement = ""
            for action in self.valid_actions:
                result, value = self.alpha_beta_pruning(players, self.tb.next_active_player_pos(player_pos), depth, current_depth, numberOfPlayers, sb_amount, alpha,beta,(index + 1) % numberOfPlayers)
                if result > max_value:
                    max_value = result
                    movement = action
                    if max_value > beta:
                        return max_value, movement
                    if max_value > alpha:
                        alpha = max_value
            return max_value, movement
        else:
            current_depth += 1

            min_value = float('Inf')
            for action in self.valid_actions:
                result, value = self.alpha_beta_pruning(players, self.tb.next_active_player_pos(player_pos), depth, current_depth, numberOfPlayers, sb_amount, alpha,beta,(index + 1) % numberOfPlayers)
                if result < min_value:
                    min_value = result
                    movement = action
                    if min_value < alpha:
                        return min_value, movement
                    if min_value < beta:
                        beta = min_value
            return min_value, "Stop"

    def estimate_win_rate(self,nb_simulation, nb_player, hole_card, community_card=None):
        if not community_card: community_card = []

        # Make lists of Card objects out of the list of cards
        community_card = gen_cards(community_card)
        hole_card = gen_cards(hole_card)

        # Estimate the win count by doing a Monte Carlo simulation
        win_count = sum([card_utils._montecarlo_simulation(nb_player, hole_card, community_card) for _ in range(nb_simulation)])
        return 1.0 * win_count / nb_simulation

    def montecarlo_simulation(nb_player, hole_card, community_card):
        # Do a Monte Carlo simulation given the current state of the game by evaluating the hands
        community_card = _fill_community_card(community_card, used_card=hole_card + community_card)
        unused_cards = _pick_unused_card((nb_player - 1) * 2, hole_card + community_card)
        opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(nb_player - 1)]
        opponents_score = [HandEvaluator.eval_hand(hole, community_card) for hole in opponents_hole]
        my_score = HandEvaluator.eval_hand(hole_card, community_card)
        return 1 if my_score >= max(opponents_score) else 0




    def bluff(self,score, hole, community, valid_actions):

        win_rate = self.estimate_win_rate(100, 3, hole, community)
        cards = hole + community
        #raise_discount = .9; all_in_discount = .2
        next_action = 'call'; amount = None

        multiplier = eval_cards.eval_cards(cards)
        if multiplier==None:
            multiplier = 1
        print(multiplier)
        score_helper = score*multiplier

        # Check whether it is possible to call
        can_call = len([item for item in valid_actions if item['action'] == 'call']) > 0
        if can_call:
            # If so, compute the amount that needs to be called
            call_amount = [item for item in valid_actions if item['action'] == 'call'][0]['amount']
        else:
            call_amount = 0

        if score_helper * win_rate > 250:
            raise_amount_options = [item for item in valid_actions if item['action'] == 'raise'][0]['amount']
            if score_helper > 450:
                next_action = 'raise'
                amount = raise_amount_options['max']
            elif score_helper > 350:
                next_action = 'raise'
                amount = raise_amount_options['min']
            else:
                next_action = 'call'
        else:
            if can_call and call_amount == 0:
                next_action = 'call'
            else:
                next_action = 'fold'

        if amount is None:
            items = [item for item in valid_actions if item['action'] == next_action]
            amount = items[0]['amount']

        return next_action, amount

    
    def declare_action(self, valid_actions, hole_card, round_state):
        # a valid action is a dictionary (tuple?) of the form {'action': 'fold', 'amount': 2}
        # needs both action name (fold, call, raise) and an amount

        # hole card is a length 2 list of the two cards (strings like 'DA', 'SK')
        
        # valid_actions format => [raise_action_info, call_action_info, fold_action_info]
        call_action_info = valid_actions[1]
        #action, amount = call_action_info["action"], call_action_info["amount"]
        return self.minimax(self.opponent_state, 0, 2, -1, len(self.opponent_state),valid_actions, 100)  # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        self.game_info = game_info
        # choose an algorithm??

    def receive_round_start_message(self, round_count, hole_card, opponent_state):
        # changed name of seats to opponent state. May need to change back if this causes an issue
        self.round_count = round_count
        self.hole_card = hole_card
        self.opponent_state = opponent_state

    def receive_street_start_message(self, street, round_state):
        self.street = street
        self.round_state = round_state

    def receive_game_update_message(self, new_action, round_state):
        self.new_action = new_action
        self.round_state = round_state

    def receive_round_result_message(self, winners, hand_info, round_state):
        self.winners = winners
        self.opponent_hand = hand_info
        self.round_state = round_state

        is_winner = self.uuid in [item['uuid'] for item in winners]
        self.wins += int(is_winner)
        self.losses += int(not is_winner)
        

        
