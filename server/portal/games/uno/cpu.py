# Uno game functions

from server.portal.games.uno.game import game_move, pass_turn, play_card
from server.portal.games.uno.util import cardInfo
from server.portal.models import GameLog, Player, Game
from typing import Tuple

def color_info(player:Player) -> Tuple[dict, list]:
  playerCards = player.specifics['cards']
  print("playerCards", playerCards)

  colorPoints = {
    "Green": 0,
    "Red": 0,
    "Blue": 0,
    "Yellow": 0
  }

  # Figure out which color groups have the most combined value
  for c in playerCards:
    ci = cardInfo(c)
    if ci['group'] == 'Wild':
      continue
    colorPoints[ci['group']] += ci['value']

  # Build a list of color groups in order of highest value
  colorRanks = []

  for color in colorPoints:
    if len(colorRanks) == 0:
      colorRanks.append(color)
    else:
      for i in range(len(colorRanks)):
        if colorPoints[color] > colorPoints[colorRanks[i]]:
          colorRanks.insert(i, color)
          break
        elif i == len(colorRanks) - 1:
          colorRanks.append(color)
  
  return colorPoints, colorRanks

def cpu_turn(game:Game, player:Player) -> Game:
    """
    Make a move for the CPU player.
    """

    print("CPU turn", player)

    # Get the top card from the discard pile
    discardPile = game.specifics['discardPile']
    top_card = discardPile[-1]

    # Check if the CPU has a valid move
    valid_moves = []

    playerCards = player.specifics['cards']
    print("player cards", playerCards)

    topCard = cardInfo(top_card)

    card:(str | None) = None

    print("Wild color", game.specifics['wildColor'])


    # Build list of valid moves
    for c in playerCards:
      heldCard = cardInfo(c)
      print("Held card", heldCard)

      if heldCard['group'] == topCard['group'] or heldCard['face'] == topCard['face'] and heldCard['group'] != 'Wild':
          valid_moves.append(c)
      elif topCard['group'] == 'Wild' and heldCard['group'] == game.specifics['wildColor']:
          valid_moves.append(c)

    # Add wild cards to the list of valid moves if no other moves are available
    if len(valid_moves) == 0:
      for c in playerCards:
        heldCard = cardInfo(c)
        if heldCard['group'] == 'Wild':
          valid_moves.append(c)

    print("Top card", top_card)
    print("Valid moves", valid_moves)
    print("card", card)

    colorPoints, colorRanks = color_info(player)
 
    # Build a list of moves that would change the color
    colorChangeMoves = []

    for color in colorRanks:
      for move in valid_moves:
        if cardInfo(move)['group'] != 'Wild' and cardInfo(move)['group'] != color:
          colorChangeMoves.append(move)

    # See if color can be changed to a higher ranked color
    if cardInfo(top_card)['group'] != colorRanks[0] and len(colorChangeMoves) > 0:
      for move in colorChangeMoves:
        ci = cardInfo(move)
        j = 0

        while j < len(colorRanks):
          if ci['group'] == colorRanks[j]:
            # GameLog.objects.create(game=game, player=player, action='p', specifics={'card': ci})
            # game = play_card(game, player, move)
            # return game
            card = move
          j += 1
        
    # Otherwise, play the highest value card
    moveValue = 0

    for move in valid_moves:
       if cardInfo(move)['value'] > moveValue:
         card = move
         break

    if card is None:
      print("No valid moves")
      if topCard['group'] == 'Wild' and game.specifics['wildColor'] is None:
        print("WILD Changing color to ", colorRanks[0])
        game = game_move(game, player, 'color', {'group': colorRanks[0]})
      else:
        game = pass_turn(game, player)
        GameLog.objects.create(game=game, player=player, action='d')
    else:
      cInfo = cardInfo(card)
      print("cInfo: ", cInfo)

      # If the top card is a wild card, change the color to the most common color
      if topCard['group'] == 'Wild' and game.specifics['wildColor'] is None:
        for color in colorPoints:
          if colorPoints[color] == max(colorPoints.values()):
            print("1 Changing color to ", color)
            return game_move(game, player, 'color', {'group': color})

      # # If the card is a wild card, change the color to the most common color
      # if cInfo['group'] == 'Wild':
      #   for color in colorPoints:
      #     if colorPoints[color] == max(colorPoints.values()):
      #       GameLog.objects.create(game=game, player=player, action='p', specifics={'card': cInfo})
      #       game = play_card(game, player, card)
      #       # game.specifics['wildColor'] = color
      #       return game

      # Pass the turn if no valid moves are available
      GameLog.objects.create(game=game, player=player, action='p', specifics={'card': cInfo})
      game = play_card(game, player, card)

      if cInfo['group'] == 'Wild':
        print("3 Changing color to ", colorRanks[0])
        game = game_move(game, player, 'color', {'group': colorRanks[0]})

    return game
