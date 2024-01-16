from itertools import groupby
from operator import attrgetter
from typing import Any

from django import forms
from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

from .models import Category, Finalist, Nomination, Rank


class NominationForm(forms.BaseForm):
    base_fields = []

    def __init__(
        self,
        *args,
        categories: list[Category],
        queryset: models.QuerySet | None = None,
        **kwargs,
    ):
        self.categories = categories
        if "initial" not in kwargs:
            if queryset is not None:
                kwargs["initial"] = self._data_from_queryset(queryset)

        super().__init__(*args, **kwargs)

        category_field_definitions: dict[str, models.CharField] = {
            f.name: f
            for f in Nomination._meta.get_fields()
            if f.name.startswith("field_")
        }

        fieldsets: dict[Category, list[list[forms.BoundField]]] = {}
        self.fieldsets_grouped_by_category = fieldsets

        self.fields = {}
        for category in self.categories:
            field_descriptions = {
                "field_1": category.field_1_description,
                "field_2": category.field_2_description,
                "field_3": category.field_3_description,
            }
            fieldset_list = fieldsets.setdefault(category, [])
            for nomination_entry in range(settings.NOMNOM_HUGO_NOMINATION_COUNT):
                fieldset = []
                fieldset_list.append(fieldset)

                for field_id in ["field_1", "field_2", "field_3"][0 : category.fields]:
                    form_field_id = f"{category.id}-{nomination_entry}-{field_id}"
                    kwargs = {
                        "label": field_descriptions[field_id],
                    }
                    field = category_field_definitions[field_id].formfield(**kwargs)
                    field.required = False
                    self.fields[form_field_id] = field

                    # we go into the __getitem__ here because this is how the fields are bound.
                    # We could hack around this, but this way we're following the Django API.
                    fieldset.append(self[form_field_id])

    def _data_from_queryset(self, queryset: models.QuerySet) -> dict[str, Any]:
        initial = {}
        for category, nominations in groupby(
            queryset.select_related("category").order_by("category"),
            attrgetter("category"),
        ):
            for i, nomination in enumerate(nominations):
                for field_id in ["field_1", "field_2", "field_3"][0 : category.fields]:
                    field_name = f"{category.id}-{i}-{field_id}"
                    initial[field_name] = getattr(nomination, field_id)

        return initial

    def clean(self) -> dict[str, Any]:
        nominations: list[Nomination] = []
        for category in self.categories:
            fieldset_list = self.fieldsets_grouped_by_category[category]
            for fieldset in fieldset_list:
                # for each fieldset, either all fields are blank or none are blank
                set_values = [bf.value() for bf in fieldset]
                if all(set_values):
                    # this is a valid nomination; add it to the set
                    nomination_field_names = [bf.name.split("-")[-1] for bf in fieldset]
                    nomination_values = [bf.value() for bf in fieldset]
                    nomination_kwargs = dict(
                        zip(nomination_field_names, nomination_values)
                    )
                    nominations.append(
                        Nomination(category=category, **nomination_kwargs)
                    )
                    continue

                if not any(set_values):
                    # this is blank; no error here!
                    continue

                for bound_field in fieldset:
                    if not bound_field.value():
                        self.add_error(
                            bound_field.name,
                            forms.ValidationError(
                                _("This field is required."),
                                code="required",
                                params={"required": True},
                            ),
                        )

        self.cleaned_data["nominations"] = nominations


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
        self.fields_grouped_by_category: dict[Category, list[forms.BoundField]] = {}
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
