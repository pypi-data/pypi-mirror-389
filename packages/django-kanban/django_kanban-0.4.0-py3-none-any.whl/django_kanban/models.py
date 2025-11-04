from django.db import models
from django.conf import settings
from django.db.models import Max
from django.core.validators import RegexValidator
from django.db import transaction
from django_kanban.querysets import BoardQuerySet


class Board(models.Model):
    name = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="images/", blank=True)
    color = models.CharField(
        max_length=7,
        validators=[RegexValidator(regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$")],
        default="#67a7c0",
        blank=True,
        null=True,
    )
    use_progress_template = models.BooleanField(default=False)
    objects = BoardQuerySet.as_manager()
    if "bookmarks" in settings.INSTALLED_APPS:
        tags = models.ManyToManyField("bookmarks.Tag", blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.use_progress_template:
            self.create_progress_template()


    @property
    def model_name(self):
        return "Board"

    def __str__(self):
        return self.name

    def create_progress_template(self):
        progress_names = ["To Implement", "On Hold", "To Do", "In Progress", "Complete"]
        for index, category_name in enumerate(progress_names):
            Category.objects.get_or_create(
                name=category_name, board=self, defaults={"position": index}
            )

    @transaction.atomic
    def update_positions(self):
        with transaction.atomic():
            categories = self.categories.order_by("position", "id")
            for i, category in enumerate(categories, start=0):
                if category.position != i:
                    category.position = i
                    category.save(update_fields=["position"])

                cards = category.cards.order_by("position", "id")
                for j, card in enumerate(cards, start=0):
                    if card.position != j:
                        card.position = j
                        card.save(update_fields=["position"])


class Category(models.Model):
    name = models.CharField(max_length=255)
    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name="categories"
    )
    position = models.PositiveIntegerField()
    color = models.CharField(
        max_length=7,
        validators=[RegexValidator(regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$")],
        help_text="Hex color code",
        default="#dde7f3",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.name

    def get_highest_category_position():
        result = Category.objects.aggregate(highest_position=Max("position"))
        return result["highest_position"] or 0

    def update_position(self, new_position):
        if new_position == self.position:
            return

        with transaction.atomic():
            categories = Category.objects.filter(board=self.board)

            if new_position < self.position:
                categories.filter(
                    position__gte=new_position, position__lt=self.position
                ).update(position=models.F("position") + 1)

            else:
                categories.filter(
                    position__gt=self.position, position__lte=new_position
                ).update(position=models.F("position") - 1)

            self.position = new_position
            self.save(update_fields=["position"])


class Card(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="images/", blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="cards"
    )
    position = models.PositiveIntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.title

    def get_highest_card_position():
        result = Card.objects.aggregate(highest_position=Max("position"))
        return result["highest_position"] or 0

    def update_position(self, new_position):
        if self.pk and Card.objects.get(pk=self.pk).category_id != self.category_id:
            self.save(update_fields=["category"])

        if new_position == self.position:
            return

        with transaction.atomic():
            cards = Card.objects.filter(category=self.category)

            if new_position < self.position:
                cards.filter(
                    position__gte=new_position, position__lt=self.position
                ).update(position=models.F("position") + 1)
            else:
                cards.filter(
                    position__gt=self.position, position__lte=new_position
                ).update(position=models.F("position") - 1)

            self.position = new_position
            self.save()
