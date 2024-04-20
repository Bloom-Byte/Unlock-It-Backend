import factory
import factory.fuzzy

from app.models import CustomUser, Story, Transaction, TransactionStatuses, TransactionTypes


class CustomUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser


class StoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Story


class TransactionFactory(factory.django.DjangoModelFactory):
    owner = factory.SubFactory(CustomUserFactory)
    story = factory.SubFactory(StoryFactory)

    email = factory.Faker("email")

    payable_amount = factory.Faker("pyint", min_value=100, max_value=5000)

    withdrawable_amount = factory.Faker("pyint", min_value=100, max_value=5000)

    payment_type = factory.fuzzy.FuzzyChoice(choices=TransactionTypes.values)
    status = factory.fuzzy.FuzzyChoice(choices=TransactionStatuses.values)

    reference = factory.Faker("name")

    class Meta:
        model = Transaction
