from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from server.portal.models import GameTitle
from server.portal.serializers import GameTitleSerializer, GroupSerializer, UserSerializer

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.views import TokenRefreshView

class RefreshTokenView(TokenRefreshView):
    permission_classes = (permissions.AllowAny,)
    print("RefreshTokenView")

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

class GameTitleViewSet(APIView):
    permission_classes = (AllowAny,)
    def get(self, request, format=None):
        print("GameTitleViewSet")
        """
        API endpoint that allows titles to be viewed or edited.
        """
        queryset = GameTitle.objects.all().order_by('title')
        serializer_class = GameTitleSerializer
        serializer = GameTitleSerializer(queryset, many=True)
        return Response(serializer.data)

class LoginView(APIView):
  permission_classes = (AllowAny,)

  def post(self, request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)

    if user is not None:
      refresh = RefreshToken.for_user(user)
      return Response({
         'username': user.username,
         'id': user.id,
         'email': user.email,
         'token': {
          'refresh': str(refresh),
          'access': str(refresh.access_token),
         }
      })
  
# view for registering users
class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        print(request.data)
        serializer = UserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # Return the user just like LoginView

            user = authenticate(username=request.data['username'], password=request.data['password'])
            refresh = RefreshToken.for_user(user)
            return Response({
              'username': user.username,
              'id': user.id,
              'email': user.email,
              'token': {
                 'refresh': str(refresh),
                 'access': str(refresh.access_token),
              }
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
