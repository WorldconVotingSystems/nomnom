from typing import Any, cast

from django import forms
from django.conf import settings
from django.forms.formsets import DELETION_FIELD_NAME
from django.utils.translation import gettext as _

from .models import Category, Finalist, Nomination, Rank


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


class RankForm(forms.BaseForm):
    base_fields = []

    def __init__(
        self,
        *args,
        finalists: list[Finalist],
        ranks: list[Rank] | None = None,
        **kwargs,
    ):
        self.finalists = finalists
        self.ranks = {f: None for f in finalists}
        if ranks is not None:
            for rank in ranks:
                self.ranks[rank.finalist] = rank.position

        super().__init__(*args, **kwargs)
        self.fields_grouped_by_category = {}
        self.fields = {
            self.field_key(finalist): self.field_for_finalist(finalist)
            for finalist in self.finalists
        }
        for finalist in self.finalists:
            self.fields_grouped_by_category.setdefault(finalist.category, []).append(
                self[self.field_key(finalist)]
            )

    def field_for_finalist(self, finalist: Finalist) -> forms.Field:
        field = forms.ChoiceField(
            label=finalist.description,
            initial=self.ranks[finalist],
            choices=self.ranks_from_category(finalist),
            required=False,
        )
        return field

    def field_key(self, finalist):
        return f"{finalist.category.id}_{finalist.id}"

    def ranks_from_category(self, finalist: Finalist) -> list[tuple[int, str]]:
        return [(None, _("Unranked"))] + [
            (i + 1, str(i + 1)) for i in range(finalist.category.finalist_set.count())
        ]

    def clean(self) -> dict[str, Any] | None:
        finalists_by_id = {
            self.field_key(finalist): finalist for finalist in self.finalists
        }
        votes = {}
        values = {}
        for name, bf in self._bound_items():
            field = bf.field
            value = bf.initial if field.disabled else bf.data

            values.setdefault(finalists_by_id[name].category, {}).setdefault(
                value, []
            ).append(name)

            votes[finalists_by_id[name]] = value if value else None

        # if any two fields in a category have the same value, attach an error to both of them.
        for category, value_map in values.items():
            for value, fields in value_map.items():
                if value:  # if this isn't "Unranked"
                    if len(fields) > 1:
                        for field in fields:
                            self.add_error(
                                field, "Cannot have two finalists ranked the same"
                            )
        self.cleaned_data["votes"] = votes
