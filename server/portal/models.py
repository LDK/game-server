from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class GameTitle(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    release_date = models.DateField()
    category = models.CharField(max_length=20)
    description = models.TextField()
    cover_art = models.ImageField(upload_to='game_covers/', blank=True)

    def __str__(self):
        return self.title
    
class GamePlayer(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    cpu_name = models.CharField(max_length=100, blank=True, null=True)
    specifics = models.JSONField(default=dict)  # Player-specific data

    def __str__(self):
        return self.user.username if self.user is not None else self.cpu_name

class Game(models.Model):
    game_title = models.ForeignKey(GameTitle, on_delete=models.CASCADE)
    starter = models.ForeignKey(User, on_delete=models.CASCADE)
    players = models.ManyToManyField(
        GamePlayer,
        through='GamePlayerMembership',
        related_name='games'
    )
    date_created = models.DateField(auto_now_add=True)
    date_started = models.DateField(blank=True, null=True)
    date_finished = models.DateField(blank=True, null=True)
    winner = models.ForeignKey(User, on_delete=models.PROTECT, related_name='winner', blank=True, null=True)
    cpu_winner = models.CharField(max_length=100, blank=True, null=True)
    last_move = models.JSONField(blank=True, null=True)
    last_move_ts = models.DateTimeField(blank=True, null=True)
    turn = models.ForeignKey(
        GamePlayer,
        on_delete=models.SET_NULL,
        related_name='turn_in_games',
        blank=True,
        null=True
    )
    specifics = models.JSONField(blank=True, null=True)
    join_mode = models.CharField(max_length=20, default='invite')  # 'invite', 'open', 'friends'

    def __str__(self):
        return f'{self.game_title.title} - Game #{self.id}'

  
class GamePlayerMembership(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    game_player = models.ForeignKey(GamePlayer, on_delete=models.CASCADE)
    starter = models.BooleanField(default=False)
    order = models.SmallIntegerField()
    date_joined = models.DateField(auto_now_add=True)
    date_left = models.DateField(blank=True, null=True)
    specifics = models.JSONField(default=dict)  # Participation-specific data

    class Meta:
        unique_together = ('game', 'order')
        verbose_name = 'Game Player Membership'
        verbose_name_plural = 'Game Player Memberships'

    def __str__(self):
        return f'{self.game_player} in Game #{self.game.id}'
