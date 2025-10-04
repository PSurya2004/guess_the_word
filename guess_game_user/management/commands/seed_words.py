from django.core.management.base import BaseCommand
from guess_game_user.models import GameWord

class Command(BaseCommand):
    help = 'Seed database with 20 uppercase 5-letter words'

    def handle(self, *args, **options):
        words = [
            'APPLE','BRAVE','CHIEF','DELTA','EAGER',
            'FAITH','GHOST','HOUSE','INPUT','JUICE',
            'KNIFE','LIGHT','MIGHT','NIGHT','OCEAN',
            'PLANT','QUICK','RIVER','STONE','TRUST'
        ]
        created = 0
        for w in words:
            obj, was_created = GameWord.objects.get_or_create(word=w)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Seeded {created} new words.'))
