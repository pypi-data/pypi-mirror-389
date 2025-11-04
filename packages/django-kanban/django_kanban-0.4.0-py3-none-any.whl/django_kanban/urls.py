from django.contrib import admin
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
     path('kanban/<int:board_id>', views.kanban, name="kanban"),
     path('kanban/boards', views.boards, name="boards"),
     path('update-card-position/', views.update_card_position, name='update_card_position'),
     path('add-category/', views.add_category, name='add_category'),
     path('update-category-position/', views.update_category_position, name='update_category_position'),
     path('add-card/', views.add_card, name='add_card'),
     path('edit-card/', views.edit_card, name='edit_card'),
     path('edit-category/', views.edit_category, name='edit_category')
    #  path('<int:kanban_id>', views.detail_list, name="detail_list"),
    #  path('bookmarks/', kanbanapi.as_view(), name='create_kanban')s
]