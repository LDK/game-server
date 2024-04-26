from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.
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
    
class Game(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.ForeignKey(GameTitle, on_delete=models.CASCADE)
    starter = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)
    date_started = models.DateField(blank=True, null=True)
    date_finished = models.DateField(blank=True, null=True)
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='winner', blank=True, null=True)
    cpu_winner = models.TextField(blank=True, null=True)
    last_move = models.JSONField(blank=True, null=True)
    last_move_ts = models.DateTimeField(blank=True, null=True)
    turn = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turn', blank=True, null=True)
    specifics = models.JSONField(blank=True, null=True) # Holds additional info specific to the game that may not apply to all titles
    def __str__(self):
        return self.title + ' - Game #' + str(self.id)
  
class GamePlayer(models.Model):
    title = models.ForeignKey(GameTitle, on_delete=models.CASCADE)
    gameId = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    starter = models.BooleanField(default=False)
    order = models.SmallIntegerField()
    date_joined = models.DateField(auto_now_add=True)
    date_left = models.DateField(blank=True, null=True)
    cpu_name = models.CharField(max_length=100, blank=True, null=True)
    specifics = models.JSONField(blank=True, null=True)

    class Meta:
        unique_together = ('gameId', 'order')

    def __str__(self):
        return self.username