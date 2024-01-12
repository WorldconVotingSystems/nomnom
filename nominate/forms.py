from typing import cast

from django import forms
from django.conf import settings
from django.forms.formsets import DELETION_FIELD_NAME

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

    @property
    def nominating_fields(self) -> set[str]:
        return set(self.Meta.fields[: self.category.fields])

    @property
    def is_blank(self) -> bool:
        data = [
            bf.data
            for name, bf in self._bound_items()
            if name in self.nominating_fields
        ]
        return not any(data)


class CustomBaseModelFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        # We allow empty forms, because we use that to indicate deleted
        kwargs["form_kwargs"]["empty_permitted"] = True

        self.category = kwargs["form_kwargs"]["category"]
        super().__init__(*args, **kwargs)

    def _should_delete_form(self, form: NominationForm) -> bool:
        # if the form's errors are _only_ for the text field, then we set _should_delete_form
        if set(form.errors.keys()) == form.nominating_fields and form.is_blank:
            return True

        return super()._should_delete_form(form)

    def add_fields(self, form: forms.Form, index: int) -> None:
        super().add_fields(form, index)

        # we are, for our UI, deleting the boolean deletion field; that's not how we
        # present this; we allow blank fields to delete.
        if DELETION_FIELD_NAME in form.fields:
            del form.fields[DELETION_FIELD_NAME]


NominationFormset = forms.modelformset_factory(
    Nomination,
    form=NominationForm,
    formset=CustomBaseModelFormSet,
    can_delete=True,
    extra=settings.NOMNOM_HUGO_NOMINATION_COUNT,
    max_num=settings.NOMNOM_HUGO_NOMINATION_COUNT,
)


class RankForm(forms.ModelForm):
    class Meta:
        model = Rank
        fields = ["position"]

    def __init__(self, *args, **kwargs):
        self.category = cast(Category, kwargs.pop("category"))

        super().__init__(*args, **kwargs)


RankFormset = forms.modelformset_factory(
    Rank,
    form=RankForm,
    formset=CustomBaseModelFormSet,
    extra=settings.NOMNOM_HUGO_NOMINATION_COUNT,
    max_num=settings.NOMNOM_HUGO_NOMINATION_COUNT,
)
