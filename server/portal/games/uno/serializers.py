from rest_framework import serializers

from server.portal.models import Game

# Only return games where title is Uno
class GameSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'game_title', 'starter', 'date_created', 'date_started', 'date_finished', 'winner', 'cpu_winner', 'last_move', 'last_move_ts', 'turn', 'specifics']
