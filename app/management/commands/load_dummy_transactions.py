from django.core.management.base import BaseCommand

from app.factory_models import TransactionFactory, CustomUser, Story


class Command(BaseCommand):
    help = "Management command to load dummy transaction data"

    def handle(self, *args, **kwargs):

        try:

            all_users = CustomUser.objects.all()

            for user in all_users:
                stories = Story.objects.filter(owner=user)

                for story in stories:
                    TransactionFactory.create_batch(4, story=story, owner=user)

            print("Done creating dummy transaction data")

        except Exception as error:
            print(f"Error when loading dummy transaction data: {error}")
