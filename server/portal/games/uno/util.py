# Uno game utility functions
from typing import List
from server.portal.models import Game, GameLog, GamePlayer, User
from server.portal.util import without_keys
from django.contrib.auth.models import AbstractUser

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

def player_list(players:List[GamePlayer], game:Game, user:(AbstractUser | None)) -> List[dict]:
    playersOut = []

    for player in players:
        gamePlayer = GamePlayer.objects.get(game=game, player=player)
        # Make a copy of the player object that will allow item assignment

        playerOut = {
            'name': player.user.get_username() if player.user is not None else player.cpu_name,
            'order': gamePlayer.order,
            'score': player.specifics['score'] if 'score' in player.specifics else 0,
            'user_id': player.user.id if player.user is not None else None,
            'cpu': player.user is None,
        }
        
        if player.specifics is not None and user is not None and user == player.user:
            cards = player.specifics['cards'] if 'cards' in player.specifics else {}
            playerOut['cards'] = cards
        elif player.specifics is not None:
            playerOut['card_count'] = len(player.specifics['cards']) if 'cards' in player.specifics else 0

        playersOut.append(playerOut)

    return playersOut

def get_game_state(game:Game, user:(AbstractUser | None)) -> dict:
    players = game.players.all().order_by('gameplayer__order')
    playersOut = player_list(players, game, user)

    gamePlayers = GamePlayer.objects.filter(game=game).all().order_by('order')

    turnGP = None if game.turn is None else gamePlayers.get(player=game.turn)
    turnOrder = None if turnGP is None else turnGP.order

    gameLog = GameLog.objects.filter(game=game).all().order_by('timestamp')
    gameLogOut = []

    for entry in gameLog:
        entryOut = None
        gamePlayer = gamePlayers.get(player=entry.player)

        if entry.action == 'to':
            entryOut = {
                'player': entry.player.user.get_username() if entry.player.user is not None else entry.player.cpu_name,
                'action': 'to',
                'card': entry.specifics['card'],
                'timestamp': entry.timestamp,
                'turnOrder': gamePlayer.order,
            }
        elif entry.action == 'p':
            entryOut = {
                'player': entry.player.user.get_username() if entry.player.user is not None else entry.player.cpu_name,
                'action': 'p',
                'card': entry.specifics['card'],
                'timestamp': entry.timestamp,
                'turnOrder': gamePlayer.order,
            }
        elif entry.action == 'w':
            entryOut = {
                'player': entry.player.user.get_username() if entry.player.user is not None else entry.player.cpu_name,
                'action': 'w',
                'color': entry.specifics['color'],
                'timestamp': entry.timestamp,
                'turnOrder': gamePlayer.order,
            }
        else:
            if entry.action is None:
                continue
            
            entryOut = {
                'player': entry.player.user.get_username() if entry.player.user is not None else entry.player.cpu_name,
                'action': entry.action,
                'timestamp': entry.timestamp,
                'turnOrder': gamePlayer.order,
            }
        
        gameLogOut.append(entryOut)

    winner = None

    if game.winner is not None:
        winner = { "user_id": game.winner.id, "name": game.winner.get_username() }
    elif game.cpu_winner is not None:
        winner = { "name": game.cpu_winner }

    output = {
        'id': game.id,
        'starter': { "user_id": game.starter.id, "name": game.starter.get_username() },
        'date_created': game.date_created,
        'date_started': game.date_started,
        'date_finished': game.date_finished,
        'winner': winner,
        'cpu_winner': None if game.cpu_winner is None else { "name": game.cpu_winner },
        'last_move': game.last_move,
        'last_move_ts': game.last_move_ts,
        'players': playersOut,
        'game_log': gameLogOut,
    }

    if turnOrder:
        output['turn_order'] = turnOrder

    return output | without_keys(game.specifics, ['deck', 'discardPile'])


def find_card(card, cards):
    cardFound = False

    for c in cards:
        if cardFound:
            break
        cInfo = cardInfo(c)
        if cInfo['group'] == card['group'] and cInfo['face'] == card['face']:
            cardFound = True
            break

    return cInfo if cardFound else None
