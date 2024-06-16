from django import forms

from . import models


class VoteForm(forms.ModelForm):
    class Meta:
        model = models.Vote
        fields = ["selection"]
        widgets = {
            "selection": forms.HiddenInput,
        }
