from rest_framework import permissions, viewsets

from server.portal.models import GameTitle, Game, GamePlayer
from server.portal.serializers import GameSerializer, GameTitleSerializer, GroupSerializer, UserSerializer

class TitleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows titles to be viewed or edited.
    """
    queryset = GameTitle.objects.filter(title='Uno').order_by('id')
    serializer_class = GameTitleSerializer
    permission_classes = [permissions.IsAuthenticated]

class GameViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows games to be viewed or edited if they are games of Uno.
    """
    queryset = Game.objects.filter(title__title='Uno').order_by('id')
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated]


