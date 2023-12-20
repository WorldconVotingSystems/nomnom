from typing import cast
from django import forms
from .models import Nomination, Category


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


def nomination_formset_factory_for_category(category: Category):
    fields = ["field_1", "field_2", "field_3"][: category.fields]
    factory = forms.modelformset_factory(Nomination, extra=5, max_num=5, fields=fields)
    return factory


NominationFormset = forms.modelformset_factory(
    Nomination,
    form=NominationForm,
    formset=CustomBaseModelFormSet,
    extra=5,
    max_num=5,
    # fields=["field_1", "field_2", "field_3"],
)
