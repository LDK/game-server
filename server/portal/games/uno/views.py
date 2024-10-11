from datetime import datetime
from rest_framework import permissions, viewsets
from server.portal.games.uno.cpu import cpu_turn
from server.portal.games.uno.game import game_move, init_game_state, next_round, pass_turn
from server.portal.games.uno.util import cardInfo, get_game_state, find_card
from server.portal.models import GameInvite, Player, Game, GameTitle, GamePlayer, GameLog, User
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from server.portal.serializers import GameTitleSerializer
from django.db.models import Count, F, IntegerField, Value
from django.db.models.functions import Cast, Coalesce

from server.portal.util import get_cpu_name

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
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        title = GameTitle.objects.get(title='Uno')
        game = Game(game_title=title)
        game.starter = request.user

        pointLimit = request.data['pointLimit'] if 'pointLimit' in request.data else 500
        maxPlayers = request.data['maxPlayers'] if 'maxPlayers' in request.data else 4
        cpuSpeed = request.data['cpuSpeed'] if 'cpuSpeed' in request.data else 500
        inviteMode = request.data['inviteMode'] if 'inviteMode' in request.data else 'public'

        game.specifics = {
            'pointLimit': pointLimit,
            'maxPlayers': maxPlayers,
            'cpuSpeed': cpuSpeed,
            'inviteMode': inviteMode,
        }

        game.save()

        player = Player(user=request.user)
        player.specifics = {
            'cards': [],
        }
        player.save()

        gamePlayer = GamePlayer(game=game, player=player, starter=True, order=1)
        gamePlayer.save()

        output = get_game_state(game, request.user)

        return Response(output)

class GameListSet(APIView):
    """
    API endpoint to list all open Uno games that have not started and are not at the player limit.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        uno_games = Game.objects.filter(
            game_title_id=1,  # Assuming 'Uno' has title_id = 1
            date_started__isnull=True,
        ).distinct().order_by('id')

        # Annotate each game with the player count
        output = []

        for game in uno_games:
            output.append(get_game_state(game, request.user))
        
        return Response(output)

class GameInviteSet(APIView):
    """
    API endpoint to invite a user to a game.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        game = Game.objects.get(id=game_id)

        if game.date_started is not None:
            return Response({'error': 'Game already started'}, status=status.HTTP_400_BAD_REQUEST)

        if game.starter != request.user:
            return Response({'error': 'Not the game starter'}, status=status.HTTP_400_BAD_REQUEST)

        if 'username' not in request.data:
            return Response({'error': 'No username specified'}, status=status.HTTP_400_BAD_REQUEST)

        recipient = User.objects.get(username=request.data['username'])

        if game.players.filter(user=recipient).exists():
            return Response({'error': 'User already in game'}, status=status.HTTP_400_BAD_REQUEST)

        gameInvite = GameInvite(game=game, sender=request.user, recipient=recipient)
        gameInvite.save()

        return Response({'success': 'Invite sent'}, status=status.HTTP_200_OK)

class GameListOpenSet(APIView):
    """
    API endpoint to list all open Uno games that have not started and are not at the player limit.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        uno_games = Game.objects.filter(
            game_title_id=1,  # Assuming 'Uno' has title_id = 1
            date_started__isnull=True,
            specifics__inviteMode='public'
        ).distinct().order_by('id')

        # Annotate each game with the player count
        uno_games = uno_games.annotate(
            player_count=Count('players', distinct=True)
        )

        # Extract 'maxPlayers' from the 'specifics' JSONField using ORM lookups
        uno_games = uno_games.annotate(
            max_players=Cast(
                Coalesce(
                    F('specifics__maxPlayers'),
                    Value(0)
                ),
                IntegerField()
            )
        )

        # Filter games where player count is less than 'maxPlayers'
        uno_games = uno_games.filter(
            player_count__lt=F('max_players')
        )

        # Filter out games where the current user is already a player
        uno_games = uno_games.exclude(
            players__user=request.user
        )

        output = []

        for game in uno_games:
            output.append(get_game_state(game, request.user))
        
        return Response(output)

class GameListUserSet(APIView):
    """
    API endpoint to list all open Uno games that have not started and are not at the player limit.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # Fetch GamePlayer entries for the current user
        gamePlayers = GamePlayer.objects.filter(
            player__user=request.user,
            game__date_finished__isnull=True
        ).order_by('game__id')

        output = []

        # Get the game state for each game from gamePlayers
        for gamePlayer in gamePlayers:
            output.append(get_game_state(gamePlayer.game, request.user))

        return Response(output)

class GameListRecentSet(APIView):
    """
    API endpoint to list all open Uno games that have not started and are not at the player limit.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # Fetch GamePlayer entries for the current user, maximum 5
        gamePlayers = GamePlayer.objects.filter(
            player__user=request.user,
            game__date_finished__isnull=False
        ).order_by('-game__date_finished')[:5]

        output = []

        # Get the game state for each game from gamePlayers
        for gamePlayer in gamePlayers:
            output.append(get_game_state(gamePlayer.game, request.user))

        return Response(output)

class PlayerListSet(APIView):
    """
    API endpoint to list Uno games for the current user that are not finished.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # Filtering games based on Player entries for the logged-in user and games not finished
        uno_games = Game.objects.filter(
            player__user=request.user,
            player__title_id=1,  # Assuming 'Uno' has title_id = 1
            date_finished__isnull=True
        ).distinct().order_by('id')

        for game in uno_games:
            players = Player.objects.filter(game=game)
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

        if 'action' not in request.data:
            return Response({'error': 'No action specified'}, status=status.HTTP_400_BAD_REQUEST)

        game = Game.objects.get(id=game_id)

        turnUser = game.turn.user if game.turn is not None else None

        if (game.turn is None or turnUser != request.user) and request.data['action'] != 'next-round':
            return Response({'error': 'Not your turn'}, status=status.HTTP_400_BAD_REQUEST)

        player = game.turn

        logSpecifics = {}
        logAction = None

        if request.data['action'] == 'play':
            if 'card' not in request.data:
                return Response({'error': 'No card specified'}, status=status.HTTP_400_BAD_REQUEST)

            logAction = 'p'

            cardFound = find_card(request.data['card'], player.specifics['cards'])
            logSpecifics['card'] = cardFound

            if not cardFound:
                return Response({'error': 'Card not in your hand'}, status=status.HTTP_400_BAD_REQUEST)

            gameState = game_move(game, player, 'play', request.data['card'])

            if gameState is None:
                return Response({'error': 'Invalid move'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = gameState

        elif request.data['action'] == 'pass':
            logAction = 'd'

            gameState = game_move(game, player, 'pass', None)

            if gameState is None:
                return Response({'error': 'Invalid move'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = gameState

        elif request.data['action'] == 'next-round':
            print("Next round")
            if game.specifics['roundWinner'] is None:
                return Response({'error': 'Round not finished'}, status=status.HTTP_400_BAD_REQUEST)
            if game.starter != request.user:
                return Response({'error': 'Not the game starter'}, status=status.HTTP_400_BAD_REQUEST)

            gameState, players = next_round(game)

            if (game.turn.user is None and 'current' in game.specifics and cardInfo(game.specifics['current'])['group'] == 'Wild'):
                game = cpu_turn(game, game.turn)

            for player in players:
                player.save()

            game = gameState

        elif request.data['action'] == 'color':
            if 'color' not in request.data:
                return Response({'error': 'No color specified'}, status=status.HTTP_400_BAD_REQUEST)

            if not game.specifics['current'].startswith('w'):
                return Response({'error': 'Not a Wild card'}, status=status.HTTP_400_BAD_REQUEST)

            color = request.data['color']
            # logAction = 'w'

            if color not in ['Red', 'Yellow', 'Green', 'Blue']:
                return Response({'error': 'Invalid color'}, status=status.HTTP_400_BAD_REQUEST)

            dummyCard = cardInfo(game.specifics['current'])
            dummyCard['group'] = color
            gameState = game_move(game, player, 'color', dummyCard)

            if gameState is None:
                return Response({'error': 'Invalid move'}, status=status.HTTP_400_BAD_REQUEST)
            
            # logSpecifics['color'] = color
            # GameLog.objects.create(game=game, player=player, action=logAction, specifics=logSpecifics)

            game = gameState
            game.specifics['wildColor'] = color

        # Save the game
        game.save()

        # if logAction is not None:
        #     log = GameLog(game=game, player=player, action=logAction, specifics=logSpecifics)
        #     log.save()


        safety = 0
        while game.turn is not None and game.turn.user is None and safety < 10:
            safety += 1
            game = cpu_turn(game, game.turn)
            game.save()

        output = get_game_state(game, request.user)
        return Response(output)

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

        players = game.players.all().order_by('gameplayer__order')

        if len(players) < 2:
            return Response({'error': 'Not enough players'}, status=status.HTTP_400_BAD_REQUEST)

        playerStarter = game.players.get(user=request.user)

        GameLog.objects.create(game=game, player=playerStarter, action='g', specifics={})
        gameState = init_game_state(players, game.specifics)

        for player in gameState['players']:
            player.save()

        game.date_started = datetime.now()
        game.turn = gameState['turn']
        game.specifics = gameState['specifics']

        card = cardInfo(game.specifics['current'])
    
        log = GameLog(game=game, player=game.turn, action='to', specifics={ 'card': card })
        log.save()

        invites = GameInvite.objects.filter(game=game)

        for invite in invites:
            if not invite.accepted and not invite.declined and not invite.expired:
                invite.expired = True
                invite.save()

        game.save()
        output = get_game_state(game, request.user)

        return Response(output)

class GameLeaveSet(APIView):
    """
    API endpoint to leave a game.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        game = Game.objects.get(id=game_id)

        if game.date_started is not None:
            return Response({'error': 'Game already started'}, status=status.HTTP_400_BAD_REQUEST)

        player = game.players.get(user=request.user)

        if player is None:
            return Response({'error': 'Not in game'}, status=status.HTTP_400_BAD_REQUEST)

        gamePlayer = GamePlayer.objects.get(game=game, player=player)

        if gamePlayer.starter:
            return Response({'error': 'Cannot leave as starter'}, status=status.HTTP_400_BAD_REQUEST)

        gamePlayer.delete()
        player.delete()

        output = get_game_state(game, request.user)
        GameLog.objects.create(game=game, player=player, action='l', specifics={})

        return Response(output)

class GameDeleteSet(APIView):
    """
    API endpoint to delete a game.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        game = Game.objects.get(id=game_id)

        if game.starter != request.user:
            return Response({'error': 'Not the game starter'}, status=status.HTTP_400_BAD_REQUEST)

        if game.winner is not None:
            return Response({'error': 'Game already finished'}, status=status.HTTP_400_BAD_REQUEST)

        game.delete()

        return Response({'success': 'Game deleted'}, status=status.HTTP_200_OK)

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

        players = game.players.all().order_by('gameplayer__order')

        if len(players) >= game.specifics['maxPlayers']:
            return Response({'error': 'Game full'}, status=status.HTTP_400_BAD_REQUEST)

        player = Player(user=request.user)
        player.specifics = {
            'cards': [],
        }
        player.save()

        gamePlayer = GamePlayer(game=game, player=player, starter=False, order=len(players) + 1)
        gamePlayer.save()

        output = get_game_state(game, request.user)
        GameLog.objects.create(game=game, player=player, action='j', specifics={})

        return Response(output)

class GameView(APIView):
    """
    API endpoint that allows games to be viewed or edited.
    """
    def get(self, request, game_id):
        # Check authentication
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        game = Game.objects.get(id=game_id)

        safety = 0
        while game.turn is not None and game.turn.user is None and safety < 10:
            safety += 1
            game = cpu_turn(game, game.turn)
            game.save()

        output = get_game_state(game, request.user)
        return Response(output)

class GameAddCpuSet(APIView):
    """
    API endpoint that allows game-starter to add a CPU player to a game of Uno.
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

        players = game.players.all().order_by('gameplayer__order')

        usedNames = []

        for player in players:
            if player.user is not None:
                usedNames.append(player.user.username)
            elif player.cpu_name is not None:
                usedNames.append(player.cpu_name)

        if len(players) >= game.specifics['maxPlayers']:
            return Response({'error': 'Game full'}, status=status.HTTP_400_BAD_REQUEST)

        player = Player(user=None, cpu_name=get_cpu_name(usedNames))
        player.specifics = {
            'cards': [],
        }
        player.save()

        gamePlayer = GamePlayer(game=game, player=player, starter=False, order=len(players) + 1)
        gamePlayer.save()

        GameLog.objects.create(game=game, player=player, action='c', specifics={})

        output = get_game_state(game, request.user)

        return Response(output)