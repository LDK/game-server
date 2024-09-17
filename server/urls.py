from django.urls import include, path
from rest_framework import routers

from server.portal import views

# Import the GameViewSet from each game vertical
from server.portal.games.uno import views as uno_views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'titles', views.GameTitleViewSet)

# Register the urls for each game vertical
# router.register(r'uno', uno_views.TitleViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('uno/', uno_views.TitleViewSet.as_view({'get': 'list'})),
    path('uno/games', uno_views.GameListSet.as_view()),
    path('uno/game/<int:game_id>/', uno_views.GameView.as_view()),
    path('uno/game/<int:game_id>/move', uno_views.GameMoveSet.as_view()),
    path('uno/game/new', uno_views.GameCreateSet.as_view(), name='game_create'),
    path('uno/game/<int:game_id>/join', uno_views.GameJoinSet.as_view(), name='game_join'),
    path('uno/game/<int:game_id>/start', uno_views.GameStartSet.as_view(), name='game_start'),
    path('user/login/', views.LoginView.as_view(), name='login'),
    path('user/register/', views.RegisterView.as_view(), name='register'),
    path('token/refresh/', views.RefreshTokenView.as_view(), name='token_refresh'),
]