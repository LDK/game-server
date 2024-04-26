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
    path('uno/games/', uno_views.GameViewSet.as_view({'get': 'list'})),
]