# Uno game functions

from datetime import datetime
import random
from typing import List
from server.portal.games.uno.util import cardInfo, get_game_state, getCardCode, init_deck
from server.portal.models import GameLog, Player, Game, GamePlayer
from typing import Tuple

def deal_cards(deck:List[str], players:List[Player], resetScore:bool = False) -> Tuple[List[str], List[Player]]:
    print("Dealing cards", len(deck), len(players))
    for player in players:
        player.specifics['score'] = 0 if resetScore else player.specifics['score'] if 'score' in player.specifics else 0  # Reset score if needed
        player.specifics['cards'] = []
        for i in range(7):
            card = deck.pop()
            player.specifics['cards'].append(card)
            # deck.remove(card)
        player.save()
        print("dealt", player.specifics['cards'], "to", player)

    
    return deck, players

def user_players(players:List[Player]) -> List[Player]:
    """
    Get the players that are users.
    """
    return [player for player in players if player.user is not None]

def draw_card(game:Game, player:Player) -> Game:
    """
    Draw a card from the deck.
    """

    deck = game.specifics['deck'] if 'deck' in game.specifics else []
    discardPile = game.specifics['discardPile'] if 'discardPile' in game.specifics else []

    if len(deck) == 0:
        print("Deck is empty")
        # Deck is empty, empty the discard pile (minus the top card in the discard pile) and make it the deck
        deck = discardPile[:-1]
        print(len(discardPile))
        print(len(deck))
        game.specifics['discardPile'] = [discardPile[-1]]

        # Shuffle deck
        random.shuffle(deck)
        game.specifics['deck'] = deck

    card = deck.pop()
    player.specifics['cards'].append(card)
    player.save()
    # game.save()
    return game

def play_card(game:Game, player:Player, card:str) -> Game:
    """
    Play a card.
    """
    top_card = game.specifics['discardPile'][-1]

    card_info = cardInfo(card)
    top_card_info = cardInfo(top_card)

    if card_info['group'] != top_card_info['group'] and card_info['face'] != top_card_info['face'] and card_info['group'] != 'Wild' and not (card_info['group'] == game.specifics['wildColor']):
        return game

    game.specifics['discardPile'].append(card)
    game.specifics['current'] = card

    game.specifics['wildColor'] = None
    player.specifics['cards'].remove(card)

    order = GamePlayer.objects.get(player=player).order
    
    turnFactor = 1

    if 'effect' in card_info:
      if card_info['effect'] == 'reverse':
        game.specifics['reverse'] = not game.specifics['reverse']
        if game.players.count() == 2:
          turnFactor = 2
      elif card_info['effect'] == 'draw-two':
        turnFactor = 2
      elif card_info['effect'] == 'draw-four':
        turnFactor = 2
      elif card_info['effect'] == 'skip':
        turnFactor = 2

    if game.specifics['reverse'] and game.players.count() > 2:
      turnFactor = turnFactor * -1

    nextOrder = order + turnFactor

    players = game.players.all()

    if card_info['group'] != 'Wild':
      newTurnOrder = nextOrder

      if nextOrder > len(players):
        while newTurnOrder > len(players):
          newTurnOrder = newTurnOrder - len(players)
        nextOrder = newTurnOrder
      
      if nextOrder < 1:
        while newTurnOrder < 1:
          newTurnOrder = newTurnOrder + len(players)
        nextOrder = newTurnOrder
        
      next = player_by_order(players, nextOrder)
      game.turn = next

    victim = None
    victimFactor = 1 if not game.specifics['reverse'] else -1
    victimOrder = order + victimFactor

    if victimOrder > len(players):
      victimOrder = 1
    elif victimOrder < 1:
      victimOrder = len(players)

    if 'effect' in card_info:
      if card_info['effect'] in ['draw-two', 'draw-four', 'skip']:
        victim = player_by_order(players, victimOrder)

      if victim is not None:
        if card_info['effect'] == 'draw-two':
          game = draw_card(game, victim)
          game = draw_card(game, victim)
          GameLog.objects.create(game=game, player=victim, action='d2')
        elif card_info['effect'] == 'draw-four':
          game = draw_card(game, victim)
          game = draw_card(game, victim)
          game = draw_card(game, victim)
          game = draw_card(game, victim)
          GameLog.objects.create(game=game, player=victim, action='d4')
        elif card_info['effect'] == 'skip':
          GameLog.objects.create(game=game, player=victim, action='s')

      if card_info['effect'] == 'reverse':
        GameLog.objects.create(game=game, player=player, action='r')

    if player.specifics['cards'] == []:
      # game.winner = player.user
      game.specifics['roundWinner'] = { "user_id": player.user.id if player.user is not None else None, "name": player.cpu_name if player.cpu_name is not None else player.user.get_username() }
      GameLog.objects.create(game=game, player=player, action='rw')

      game.turn = None

      points = player.specifics['score'] | 0
      roundPoints = 0

      for pl in players:
        if pl.user == player.user and player.user is not None:
          continue
        
        plPoints = 0

        for card in pl.specifics['cards']:
          cInfo = cardInfo(card)
          plPoints += cInfo['value']
          print((pl.user.get_username() if pl.user is not None else pl.cpu_name) + " has cards: ")
          print(pl.specifics['cards'])
          print("For a total of " + str(plPoints) + " points")
        # pl.specifics['cards'] = []
        pl.save()
        roundPoints += plPoints

      print("Previous points: " + str(points))
      print("Points from this round: " + str(roundPoints))
      print("Total points for" + (
        player.user.get_username() if player.user is not None else player.cpu_name
      ) + ": " + str(points + roundPoints))

      points += roundPoints
      player.specifics['score'] = points
      player.save()

      if points >= game.specifics['pointLimit']:
        if player.user is not None:
          game.winner = player.user
        else:
          game.cpu_winner = player.cpu_name
        game.specifics['roundWinner'] = None
        game.date_finished = datetime.now()
        GameLog.objects.create(game=game, player=player, action='v')

      game.save()
      return game
    else:
      game.specifics['roundWinner'] = None

    game.save()
    player.save()
    return game

def player_by_order(players:List[Player], order:int) -> (Player | None):
    # Find player in list whose order is equal to the given order
    
    correctPlayer = None

    for player in players:
        gamePlayer = GamePlayer.objects.get(player=player)
        if gamePlayer.order == order:
            correctPlayer = player
            break

    return correctPlayer

def advance_turn(game:Game, order:int, factor:int = 1) -> Game:
  players = game.players.all()
  turnFactor = factor if not game.specifics['reverse'] else factor * -1
  nextOrder = order + turnFactor
  newTurnOrder = nextOrder

  if nextOrder > len(players):
    while newTurnOrder > len(players):
      newTurnOrder = newTurnOrder - len(players)
    nextOrder = newTurnOrder
  
  if nextOrder < 1:
    while newTurnOrder < 1:
      newTurnOrder = newTurnOrder + len(players)
    nextOrder = newTurnOrder

  next = player_by_order(players, nextOrder)
  game.turn = next
  return game

def pass_turn(game:Game, player:Player) -> Game:
    """
    Pass the turn to the next player.
    """

    players = game.players.all()
    player = game.turn
    gamePlayer = GamePlayer.objects.get(game=game, player=player)
    order = gamePlayer.order
    turnFactor = 1 if not game.specifics['reverse'] else -1
    nextOrder = order + turnFactor

    if nextOrder > len(players):
        nextOrder = 1
    
    if nextOrder < 1:
        nextOrder = len(players)

    next = player_by_order(players, nextOrder)

    game = draw_card(game, player)
    game.turn = next

    return game

def init_game_state(players:List[Player], specifics:(dict | None) = None) -> dict:
    """
    Initialize a game state.
    """
    gameState = {}
    gameState['specifics'] = {}
    deck = init_deck()
    random.shuffle(deck)
    current = deck.pop()

    # If the first card is a Draw Four, put it back in the deck and reshuffle
    while (current == 'wd4'):
      deck.insert(0, current)
      random.shuffle(deck)
      current = deck.pop()

    cInfo = cardInfo(current)

    gameState['specifics']['current'] = current
    gameState['specifics']['discardPile'] = [current]
    gameState['specifics']['reverse'] = False if 'effect' not in cInfo else (cInfo['effect'] == 'reverse')
    gameState['specifics']['pointLimit'] = specifics['pointLimit'] if 'pointLimit' in specifics else 500
    gameState['specifics']['cpuSpeed'] = specifics['cpuSpeed'] if 'cpuSpeed' in specifics else 500
    gameState['specifics']['roundWinner'] = None
    gameState['specifics']['wildColor'] = None
    gameState['specifics']['maxPlayers'] = specifics['maxPlayers'] if 'maxPlayers' in specifics else 4
    deck, players = deal_cards(deck, players, True)
    gameState['specifics']['deck'] = deck
    gameState['players'] = players
    gameState['turn'] = random.choice(user_players(players))
    return gameState

# Return a new deck, discard pile, and current card
def init_cards(game:Game, player:Player) -> Tuple[List[str], List[str], str]:
    deck = init_deck()
    random.shuffle(deck)
    current = deck.pop()

    # If the first card is a Draw Four, put it back in the deck and reshuffle
    while (current == 'wd4'):
      deck.insert(0, current)
      random.shuffle(deck)
      current = deck.pop()

    discardPile = [current]

    GameLog.objects.create(game=game, player=player, action='to', specifics={'card': cardInfo(current)})

    return deck, discardPile, current

def next_round(game:Game) -> Game:
    """
    Start the next round.
    """
    players = game.players.all()
    starterPlayer = players.get(user=game.starter)

    GameLog.objects.create(game=game, player=starterPlayer, action='nr')

    newTurn = random.choice(players)
    
    deck, discardPile, current = init_cards(game, newTurn)
    currentInfo = cardInfo(current)

    game.specifics['current'] = current
    game.specifics['discardPile'] = discardPile
    game.specifics['reverse'] = currentInfo['effect'] == 'reverse' if 'effect' in currentInfo else False
    game.specifics['roundWinner'] = None
    game.specifics['wildColor'] = None
    
    deck, players = deal_cards(deck, players)

    game.specifics['deck'] = deck
    game.turn = newTurn

    return game, players

def game_move(game:Game, player:Player, action:str, card:(dict | None)) -> Game:
    """
    Make a move in the game.
    """

    if action == 'pass':
        game = pass_turn(game, player)
        GameLog.objects.create(game=game, player=player, action='d')

    elif action == 'play':
        if (card is None):
          return game
        
        GameLog.objects.create(game=game, player=player, action='p', specifics={'card': card})
        game = play_card(game, player, getCardCode(card))

    elif action == 'color':
        print("color: " + card['group'])
        gamePlayer = GamePlayer.objects.get(game=game, player=player)
        turnFactor = 1 if not game.specifics['current'] == 'wd4' else 2
        mostRecentLog = GameLog.objects.filter(game=game).order_by('-timestamp').first()
        if mostRecentLog is None:
          return game
        if mostRecentLog.action == 'to':
          turnFactor = 0
        game.specifics['wildColor'] = card['group']
        game = advance_turn(game, gamePlayer.order, turnFactor)
        GameLog.objects.create(game=game, player=player, action='w', specifics={'color': card['group']})

    elif action == 'next-round':
        game = next_round(game)
    else:
        return game

    return game


