from django import forms
from django_kanban.models import Board
from django.forms import modelformset_factory, BaseModelFormSet
from django.conf import settings


class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        if "bookmarks" in settings.INSTALLED_APPS:
            fields = ["name", "tags", "image", "color", "use_progress_template"]
        else:
            fields = ["name", "image", "color", "use_progress_template"]
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def update_form(self):
        if self.is_valid():
            return self.save()
        return None

    @classmethod
    def get_formset(cls, extra=0):
        return modelformset_factory(
            Board, formset=BoardFormSet, form=cls, extra=extra, can_delete=True
        )

class BoardFormSet(BaseModelFormSet):
    def update_formset(self):
        if self.is_valid():
            self.save()
            return True
        return False
    
    def update_formset_helper(self, add_board):
        if self.update_formset():
            new_board_form = self.forms[-1]
            if new_board_form.cleaned_data:
                add_board(new_board_form.instance)

