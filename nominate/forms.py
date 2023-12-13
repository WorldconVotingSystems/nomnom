from django import forms
from .models import Nomination


class NominationForm(forms.ModelForm):
    class Meta:
        model = Nomination
