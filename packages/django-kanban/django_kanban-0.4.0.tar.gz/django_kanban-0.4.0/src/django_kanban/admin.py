from django.contrib import admin

from .models import Board, Category, Card

admin.site.register(Board)
admin.site.register(Category)
admin.site.register(Card)