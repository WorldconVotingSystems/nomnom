from typing import cast

from django import forms
from django.conf import settings

from .models import Category, Nomination, Rank


class NominationForm(forms.ModelForm):
    class Meta:
        model = Nomination
        fields = ["field_1", "field_2", "field_3"]

    def __init__(self, *args, **kwargs):
        self.category = cast(Category, kwargs.pop("category"))

        super().__init__(*args, **kwargs)

        field_descriptions = {
            "field_1": self.category.field_1_description,
            "field_2": self.category.field_2_description,
            "field_3": self.category.field_3_description,
        }

        fields_to_punt = self.Meta.fields[self.category.fields :]

        for f in fields_to_punt:
            self.fields.pop(f)

        # Update the form fields based on category.field_count
        for i, field in enumerate(self.fields, start=1):
            self.fields[field].label = field_descriptions[field]
            self.fields[field].widget.attrs["placeholder"] = field_descriptions[field]
            self.fields[field].widget.attrs["aria-label"] = field_descriptions[field]


class CustomBaseModelFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        self.category = kwargs["form_kwargs"]["category"]
        super().__init__(*args, **kwargs)


NominationFormset = forms.modelformset_factory(
    Nomination,
    form=NominationForm,
    formset=CustomBaseModelFormSet,
    extra=settings.NOMNOM_HUGO_NOMINATION_COUNT,
    max_num=settings.NOMNOM_HUGO_NOMINATION_COUNT,
)


class RankForm(forms.ModelForm):
    class Meta:
        model = Rank
        fields = ["position"]


RankFormset = forms.modelformset_factory(
    Rank,
    form=RankForm,
    formset=CustomBaseModelFormSet,
    extra=settings.NOMNOM_HUGO_NOMINATION_COUNT,
    max_num=settings.NOMNOM_HUGO_NOMINATION_COUNT,
)
