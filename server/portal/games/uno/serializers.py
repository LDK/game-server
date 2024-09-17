from django.contrib.auth.models import Group, User
from rest_framework import serializers

from server.portal.models import Game, GamePlayer, GameTitle

# Only return games where title is Uno
class GameSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'title', 'starter', 'date_created', 'date_started', 'date_finished', 'winner', 'cpu_winner', 'last_move', 'last_move_ts', 'turn', 'specifics']
        def get_queryset(self):
            data = Game.objects.filter(title__title='Uno').order_by('last_move_ts', 'id')

            return data
