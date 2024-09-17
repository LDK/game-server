# Uno game functions

import random
from typing import List
from server.portal.models import GamePlayer, Game, GamePlayerMembership, GameTitle
from typing import Tuple

def faceNames() -> dict:
  return {
    's': 'Skip',
    'r': 'Reverse',
    'd': 'Draw Two',
    'd4': 'Draw Four',
    'w': 'Wild',
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
    '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
  }

def groupNames() -> dict:
  return {
    'r': 'Red',
    'g': 'Green',
    'b': 'Blue',
    'y': 'Yellow',
    'w': 'Wild'
  }

def faceValues() -> dict:
  return {
    's': 20,
    'r': 20,
    'd': 20,
    'd4': 50,
    'w': 50,
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4,
    '5': 5, '6': 6, '7': 7, '8': 8, '9': 9
  }

def getCardCode(card) -> str:
  print("card: ", card)
  # Get group code using groupNames
  group = [key for key, value in groupNames().items() if value == card['group']][0]

  if card['face'] == 'Wild':
    return 'w'
  elif card['face'] == 'Draw Four':
    return 'wd4'
  else:
    # Get face code using faceNames
    face = [key for key, value in faceNames().items() if value == card['face']][0]

    return group + face

def cardInfo(code:str) -> dict:
    """
    Get the color and number of a card.
    """

    print("code: ", code)

    group = code[0]
    face = code[1] if len(code) > 1 else code[1:]

    if (code == 'wd4'):
      face = 'd4'
    elif (code == 'w'):
      face = 'w'

    faceName = faceNames()[face]
    groupName = groupNames()[group]

    card = {
      'group': groupName,
      'face': faceName,
      'short': face.upper(),
      'value': faceValues()[face],
      'name': f'{groupName} {faceName}'
    }

    effects = ['Skip', 'Reverse', 'Draw Two', 'Draw Four', 'Wild']

    if (faceName in effects):
      card['effect'] = effects[effects.index(faceName)].lower().replace(' ', '-')    

    return card

def init_deck() -> List[str]:
    """
    Initialize the deck for the game.
    """
    deck = []
    for color in ['r', 'g', 'b', 'y']:
        for i in range(10):
            deck.append(f'{color}{i}')
            deck.append(f'{color}{i}')
        deck.append(f'{color}s')
        deck.append(f'{color}s')
        deck.append(f'{color}r')
        deck.append(f'{color}r')
        deck.append(f'{color}d')
        deck.append(f'{color}d')
    for i in range(4):
        deck.append('w')
        deck.append('wd4')
    return deck


def deal_cards(deck:List[str], players:List[GamePlayer]) -> Tuple[List[str], List[GamePlayer]]:
    for player in players:
        for i in range(7):
            card = deck.pop()
            player.specifics['cards'].append(card)
            deck.remove(card)
    return deck, players

def user_players(players:List[GamePlayer]) -> List[GamePlayer]:
    """
    Get the players that are users.
    """
    return [player for player in players if player.user is not None]

def draw_card(game:Game, player:GamePlayer) -> Game:
    """
    Draw a card from the deck.
    """

    deck = game.specifics['deck'] if 'deck' in game.specifics else []
    discardPile = game.specifics['discardPile'] if 'discardPile' in game.specifics else []

    if len(deck) == 0:
        # Deck is empty, empty the discard pile (minus the top card in the discard pile) and make it the deck
        deck = game.specifics['discardPile'][:-1]
        game.specifics['discardPile'] = [discardPile[-1]]
        print("deck: ", deck)
        print("discard pile: ", game.specifics['discardPile']) 

        # Shuffle deck
        random.shuffle(game.specifics['deck'])

    card = deck.pop()
    player.specifics['cards'].append(card)
    player.save()
    game.save()
    return game

def play_card(game:Game, player:GamePlayer, card:str) -> Game:
    """
    Play a card.
    """

    print("play card: ", card)
    print("player: ", player)

    top_card = game.specifics['discardPile'][-1]

    print("top card: ", top_card)

    card_info = cardInfo(card)
    top_card_info = cardInfo(top_card)

    if card_info['group'] != top_card_info['group'] and card_info['face'] != top_card_info['face'] and card_info['group'] != 'Wild':
        return game

    game.specifics['discardPile'].append(card)
    game.specifics['current'] = card
    player.specifics['cards'].remove(card)

    print("player specifics: ", player.specifics)
    print('game specifics: ', game.specifics)

    game.save()
    player.save()
    return game

def player_by_order(players:List[GamePlayer], order:int) -> GamePlayer:
    """
    Get a player by order.
    """

    if order > len(players):
        order = 1

    if order < 1:
        order = len(players)

    return [player for player in players if player]

def pass_turn(game:Game, player:GamePlayer) -> Game:
    """
    Pass the turn to the next player.
    """

    print("Passing turn for player: ", player)

    players = GamePlayer.objects.filter(game=game)
    player = game.turn
    membership = GamePlayerMembership.objects.get(game=game, game_player=player)
    order = membership.order
    turnFactor = 1 if not game.specifics['reverse'] else -1
    nextOrder = order + turnFactor

    if nextOrder > len(players):
        nextOrder = 1
    
    if nextOrder < 1:
        nextOrder = len(players)

    next = player_by_order(players, nextOrder)

    game = draw_card(game, player)
    game.turn = next
    game.save()

    return game

def cpu_turn(game:Game, player:GamePlayer) -> Game:
    """
    Make a move for the CPU player.
    """
    # Get the top card from the discard pile
    discardPile = game.specifics['discardPile']
    top_card = discardPile[-1]

    # Check if the CPU has a valid move
    valid_moves = []

    playerCards = player.specifics['cards']

    topCard = cardInfo(top_card)

    for card in playerCards:
        heldCard = cardInfo(card)

        if heldCard['group'] == topCard['group'] or heldCard['face'] == topCard['face']:
            valid_moves.append(card)

    if len(valid_moves) == 0:
      for card in playerCards:
        heldCard = cardInfo(card)
        if heldCard['group'] == 'Wild':
          valid_moves.append(card)

    if len(valid_moves) == 0:
      game = pass_turn(game, player)
      return game

    # The CPU has a valid move, make a random move
    card = random.choice(valid_moves)

    print("Valid moves: ", valid_moves)

    game = play_card(game, player, card)
    return game

def init_game_state(players:List[GamePlayer], specifics:(dict | None) = None) -> dict:
    """
    Initialize a game state.
    """
    gameState = {}
    gameState['specifics'] = {}
    deck = init_deck()
    random.shuffle(deck)
    current = deck.pop()

    gameState['specifics']['current'] = current
    gameState['specifics']['discardPile'] = [current]
    gameState['specifics']['reverse'] = False
    gameState['specifics']['pointLimit'] = specifics['pointLimit'] if 'pointLimit' in specifics else 500
    gameState['specifics']['cpuSpeed'] = specifics['cpuSpeed'] if 'cpuSpeed' in specifics else 500
    deck, players = deal_cards(deck, players)
    gameState['specifics']['deck'] = deck
    gameState['players'] = players
    gameState['turn'] = random.choice(user_players(players))
    return gameState


def game_move(player:GamePlayer, action:str, card:(dict | None)) -> Game:
    """
    Make a move in the game.
    """
    
    game = Game.objects.get(id=player.game.id)

    if action == 'pass':
        game = pass_turn(game, player)
        print("passing turn", game, player)
    elif action == 'play':
        if (card is None):
          return game
        
        game = play_card(game, player, getCardCode(card))
    else:
        return game

    return game