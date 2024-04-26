from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets

from server.portal.models import GameTitle
from server.portal.serializers import GameTitleSerializer, GroupSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class GameTitleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows titles to be viewed or edited.
    """
    queryset = GameTitle.objects.all().order_by('title')
    serializer_class = GameTitleSerializer
    permission_classes = [permissions.IsAuthenticated]