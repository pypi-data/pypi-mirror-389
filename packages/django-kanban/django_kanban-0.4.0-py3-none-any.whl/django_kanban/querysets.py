from django.db import models
from django.db.models import Q

class BoardQuerySet(models.QuerySet):
    def search(self, query=None):
        result = self.none()

        if query.lower() == "boards":
            result = self.all()
        else:
            result = self.filter(
                Q(name__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()

        return result
    