from django.contrib.auth.models import Group, User
from rest_framework import serializers

from server.portal.models import Game, GameTitle


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class GameTitleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GameTitle
        fields = ['url', 'title', 'release_date', 'category', 'description', 'cover_art']

class GameSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'title', 'starter', 'date_created', 'date_started', 'date_finished', 'winner', 'cpu_winner', 'last_move', 'last_move_ts', 'turn', 'specifics']
