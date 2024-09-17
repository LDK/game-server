from datetime import datetime
import json
import random
from rest_framework import permissions, viewsets
from server.portal.games.uno.game import cardInfo, cpu_turn, game_move, init_game_state, pass_turn
from server.portal.games.uno.serializers import GameSerializer
from server.portal.models import GamePlayer, Game, GameTitle, GamePlayerMembership
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from server.portal.serializers import GameTitleSerializer

def without_keys(d, keys):
    return {k: d[k] for k in d.keys() - keys}

class TitleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows titles to be viewed or edited.
    """
    queryset = GameTitle.objects.filter(title='Uno').order_by('id')
    serializer_class = GameTitleSerializer
    permission_classes = [permissions.IsAuthenticated]

class GameCreateSet(APIView):
    """
    API endpoint to create a new Uno game.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print(request.data)

        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        title = GameTitle.objects.get(title='Uno')

        game = Game(game_title=title)
        game.starter = request.user
        # game.game_title = title
        print("#####")
        print(game.game_title.id)

        pointLimit = request.data['pointLimit'] if 'pointLimit' in request.data else 500
        maxPlayers = request.data['maxPlayers'] if 'maxPlayers' in request.data else 4
        cpuSpeed = request.data['cpuSpeed'] if 'cpuSpeed' in request.data else 500

        game.specifics = {
            'pointLimit': pointLimit,
            'maxPlayers': maxPlayers,
            'cpuSpeed': cpuSpeed,
        }

        game.save()

        player = GamePlayer(user=request.user)
        player.specifics = {
            'cards': [],
        }
        player.save()

        membership = GamePlayerMembership(game=game, game_player=player, starter=True, order=1)
        membership.save()

        output = {
            'id': game.id,
            'starter': player.user.get_username(),
            'date_joined': membership.date_joined,
            'date_created': game.date_created,
            'player_count': 1,
            'cpu_count': 0,
            'started': False,
        }

        return Response({'success': output }, status.HTTP_200_OK)

class GameListSet(APIView):
    """
    API endpoint to list Uno games for the current user that are not finished.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # Filtering games based on GamePlayer entries for the logged-in user and games not finished
        uno_games = Game.objects.filter(
            gameplayer__user=request.user,
            gameplayer__title_id=1,  # Assuming 'Uno' has title_id = 1
            date_finished__isnull=True
        ).distinct().order_by('id')

        for game in uno_games:
            players = GamePlayer.objects.filter(game=game)
            player = players.get(user=request.user)
            output = [
                {
                    'id': game.id,
                    'starter': player.starter,
                    'date_joined': player.date_joined,
                    'date_created': game.date_created,
                    'player_count': len(players),
                    'cpu_count': len([p for p in players if p.user is None]),
                }
            ]

        return Response(output)

class GameMoveSet(APIView):
    """
    API endpoint to make a move in a game.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        game = Game.objects.get(id=game_id)

        result: Response = None

        turnUser = game.turn.user if game.turn is not None else None
        print("game")
        print(game.turn.__dict__)

        print("turnUser:")
        print(turnUser)

        if game.turn is None or turnUser != request.user:
            return Response({'error': 'Not your turn'}, status=status.HTTP_400_BAD_REQUEST)

        player = GamePlayer.objects.get(game=game, user=request.user)

        if 'action' not in request.data:
            return Response({'error': 'No action specified'}, status=status.HTTP_400_BAD_REQUEST)

        if request.data['action'] == 'play':
            if 'card' not in request.data:
                return Response({'error': 'No card specified'}, status=status.HTTP_400_BAD_REQUEST)

            card = request.data['card']

            cardFound = False

            print("card: ", card)
            for c in player.specifics['cards']:
                print(c)
                cInfo = cardInfo(c)
                print("cInfo: ", cInfo)
                if cInfo['group'] == card['group'] and cInfo['face'] == card['face']:
                    cardFound = True
                    break

            if not cardFound:
                print(player.specifics['cards'])
                print(card)
                return Response({'error': 'Card not in your hand'}, status=status.HTTP_400_BAD_REQUEST)

            gameState = game_move(player, 'play', card)

            if gameState is None:
                return Response({'error': 'Invalid move'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = gameState

        elif request.data['action'] == 'pass':
            gameState = pass_turn(game, player)

            if gameState is None:
                return Response({'error': 'Invalid move'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = gameState

        # Save the game
        game.save()

        while game.turn.user is None:
            game = cpu_turn(game, game.turn)
            game.save()

        output = {
            'id': game.id,
            'starter': game.starter.get_username(),
            'date_created': game.date_created,
            'date_started': game.date_started,
            'date_finished': game.date_finished,
            'winner': game.winner if game.winner is None else game.winner.get_username(),
            'cpu_winner': game.cpu_winner if (game.cpu_winner is not None and len(game.cpu_winner) > 0) else None,
            'last_move': game.last_move,
            'last_move_ts': game.last_move_ts,
            'turn_order': game.turn if game.turn is None else game.turn.order,
        }

        return Response({'success': output }, status.HTTP_200_OK)

class GameStartSet(APIView):
    """
    API endpoint to start a game.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        game = Game.objects.get(id=game_id)

        if game.starter != request.user:
            return Response({'error': 'Not the game starter'}, status=status.HTTP_400_BAD_REQUEST)

        if game.date_started is not None:
            return Response({'error': 'Game already started'}, status=status.HTTP_400_BAD_REQUEST)

        players = game.players.all().order_by('gameplayermembership__order')

        if len(players) < 2:
            return Response({'error': 'Not enough players'}, status=status.HTTP_400_BAD_REQUEST)

        gameState = init_game_state(players, game.specifics)

        game.date_started = datetime.now()
        game.turn = gameState['turn']
        game.specifics = gameState['specifics']
        game.players.set(gameState['players'])

        game.save()

        return Response({'success': 'Game started'}, status.HTTP_200_OK)

class GameJoinSet(APIView):
    """
    API endpoint to join a game.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        game = Game.objects.get(id=game_id)

        if game.date_started is not None:
            return Response({'error': 'Game already started'}, status=status.HTTP_400_BAD_REQUEST)

        if game.players.filter(user=request.user).exists():
            return Response({'error': 'Already joined'}, status=status.HTTP_400_BAD_REQUEST)

        players = game.players.all().order_by('gameplayermembership__order')

        if len(players) >= game.specifics['maxPlayers']:
            return Response({'error': 'Game full'}, status=status.HTTP_400_BAD_REQUEST)

        player = GamePlayer(user=request.user)
        player.specifics = {
            'cards': [],
        }
        player.save()

        membership = GamePlayerMembership(game=game, game_player=player, starter=False, order=len(players) + 1)
        membership.save()

        return Response({'success': 'Joined game'}, status.HTTP_200_OK)

class GameView(APIView):
    """
    API endpoint that allows games to be viewed or edited.
    """
    def get(self, request, game_id):
        # Check authentication
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        game = Game.objects.get(id=game_id)

        players = game.players.all().order_by('gameplayermembership__order')
        cards = {}

        playersOut = []

        for player in players:
            membership = GamePlayerMembership.objects.get(game=game, game_player=player)
            # Make a copy of the player object that will allow item assignment
            playerOut = {
                'name': player.user.get_username() if player.user is not None else player.cpu_name,
                'order': membership.order,
                'user_id': player.user.id if player.user is not None else None,
                'cpu': player.user is None,
            }
            
            if player.specifics is not None and request.user == player.user:
                cards = player.specifics['cards'] if 'cards' in player.specifics else {}
                playerOut['cards'] = cards
            elif player.specifics is not None:
                playerOut['card_count'] = len(player.specifics['cards']) if 'cards' in player.specifics else 0

            playersOut.append(playerOut)

        turnMember = GamePlayerMembership.objects.get(game=game, game_player=game.turn)
        turnOrder = turnMember.order if game.turn is not None else None

        output = {
            'id': game.id,
            'starter': game.starter.get_username(),
            'date_created': game.date_created,
            'date_started': game.date_started,
            'date_finished': game.date_finished,
            'winner': game.winner if game.winner is None else game.winner.get_username(),
            'cpu_winner': game.cpu_winner if (game.cpu_winner is not None and len(game.cpu_winner) > 0) else None,
            'last_move': game.last_move,
            'last_move_ts': game.last_move_ts,
            'players': playersOut,
        }

        if turnOrder:
            output['turn_order'] = turnOrder

        return Response(output | without_keys(game.specifics, ['deck', 'discardPile']))
