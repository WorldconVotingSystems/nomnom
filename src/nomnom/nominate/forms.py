from collections.abc import Iterable
from dataclasses import dataclass
from itertools import groupby
from operator import attrgetter
from typing import Any, cast

from django import forms
from django.db import models
from django.utils.translation import gettext as _
from django_svcs.apps import svcs_from
from markdownify.templatetags.markdownify import markdownify

from nomnom.convention import HugoAwards

from .models import Category, Finalist, Nomination, Rank


@dataclass
class RankedFinalist:
    rank: int
    finalist: Finalist


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

        category_field_definitions: dict[str, models.Field] = {
            f.name: f
            for f in Nomination._meta.get_fields()
            if f.name.startswith("field_")
        }

        fieldsets: dict[Category, list[list[forms.BoundField]]] = {}
        self.fieldsets_grouped_by_category = fieldsets

        constitution = svcs_from().get(HugoAwards)

        self.fields = {}
        for category in self.categories:
            field_descriptions = {
                "field_1": category.field_1_description,
                "field_2": category.field_2_description,
                "field_3": category.field_3_description,
            }
            fieldset_list = fieldsets.setdefault(category, [])
            for nomination_entry in range(constitution.hugo_nominations_per_member):
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

        # autofocus all error fields; the browser will jump to the first one
        for field in self.errors:
            self[field].field.widget.attrs.update({"autofocus": ""})

    def _data_from_queryset(self, queryset: models.QuerySet) -> dict[str, Any]:
        initial = {}
        for category, nominations in groupby(
            queryset.select_related("category").order_by("category", "id"),
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
                required = [
                    category.field_required(i + 1) for i, _ in enumerate(fieldset)
                ]
                set_required_values = [
                    value for value, required in zip(set_values, required) if required
                ]

                if all(set_required_values):
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
        return self.cleaned_data


class RankForm(forms.BaseForm):
    base_fields = []

    def __init__(
        self,
        *args,
        finalists: Iterable[Finalist],
        ranks: Iterable[Rank] | None = None,
        **kwargs,
    ):
        self.finalists = finalists
        self.ranks = {f: None for f in finalists}
        if ranks is not None:
            for rank in ranks:
                self.ranks[rank.finalist] = rank.position

        super().__init__(*args, **kwargs)
        self.fields_grouped_by_category: list[
            tuple[Category, list[forms.BoundField]]
        ] = []
        self.fields = {
            self.field_key(finalist): self.field_for_finalist(finalist)
            for finalist in self.finalists
        }

        unordered_fields: dict[Category, list[forms.BoundField]] = {}
        for finalist in self.finalists:
            unordered_fields.setdefault(finalist.category, []).append(
                self[self.field_key(finalist)]
            )

        self.fields_grouped_by_category = [
            (category, unordered_fields[category])
            for category in sorted(unordered_fields, key=attrgetter("ballot_position"))
        ]

        # autofocus all error fields; the browser will jump to the first one
        for field in self.errors:
            self[field].field.widget.attrs.update({"autofocus": ""})

    def field_for_finalist(self, finalist: Finalist) -> forms.Field:
        label = markdownify(finalist.name, custom_settings="admin-label")
        field = forms.ChoiceField(
            label=label,
            initial=self.ranks[finalist],
            choices=self.ranks_from_category(finalist),
            required=False,
        )
        return field

    def field_key(self, finalist):
        return f"{finalist.category.id}_{finalist.id}"

    def ranks_from_category(
        self, finalist: Finalist
    ) -> list[tuple[int, str] | tuple[None, str]]:
        return [(None, _("Unranked"))] + [
            (i + 1, str(i + 1)) for i in range(finalist.category.finalist_set.count())
        ]

    def clean(self) -> dict[str, Any] | None:
        # A lookup table for finalists by their field key.
        finalists_by_id = {
            self.field_key(finalist): finalist for finalist in self.finalists
        }
        # this view of the votes is used for saving purposes.
        finalist_ranks = {}

        # This view of the votes is shaped specifically to identify duplicates, and associate
        # them with the fields that are duplicates.
        category_rank_field_map = {}

        for name, bf in self._bound_items():
            name = cast(str, name)
            bf = cast(forms.BoundField, bf)

            field = bf.field
            rank = bf.initial if field.disabled else bf.data

            fields_grouped_by_rank = category_rank_field_map.setdefault(
                finalists_by_id[name].category, {}
            )

            fields_grouped_by_rank.setdefault(rank, []).append(name)

            finalist_ranks[finalists_by_id[name]] = rank if rank else None

        # if any two fields in a category have the same value, attach an error to both of them.
        for fields_grouped_by_rank in category_rank_field_map.values():
            for rank, fields in fields_grouped_by_rank.items():
                if rank:  # if this isn't "Unranked"
                    if len(fields) > 1:
                        for field in fields:
                            self.add_error(
                                field, "Cannot have two finalists ranked the same"
                            )

        # This is a view of the ranks by category excluding unranked. This is used to check for gaps.
        ranks_by_category: dict[Category, list[RankedFinalist]] = {}
        for finalist, rank in finalist_ranks.items():
            # only try this for actual ranks; invalid data in the rank field
            # will be caught by the ChoiceField validation, but that happens
            # after this step, regrettably.
            if rank and str(rank).isdigit():
                ranks_by_category.setdefault(finalist.category, []).append(
                    RankedFinalist(int(rank), finalist)
                )

        for ranks in ranks_by_category.values():
            sorted_ranks = sorted(ranks, key=attrgetter("rank"))

            # if the first rank that isn't "Unranked" isn't "1", attach an error to the lowest-ranked finalist
            if sorted_ranks and sorted_ranks[0].rank != 1:
                self.add_error(
                    self.field_key(sorted_ranks[0].finalist),
                    "Must start with 1",
                )

            # if there is a gap in the rankings, attach an error to the first field in the gap
            for i, (rank, next_rank) in enumerate(zip(sorted_ranks, sorted_ranks[1:])):
                if next_rank.rank - rank.rank != 1:
                    self.add_error(
                        self.field_key(next_rank.finalist),
                        "Cannot have gaps in rankings",
                    )

        self.cleaned_data["votes"] = finalist_ranks

    @property
    def fields_grouped_by_category_sorted_by_rank(
        self,
    ) -> list[tuple[Category, list[forms.BoundField]]]:
        if not hasattr(self, "fields_grouped_by_category"):
            # we haven't run clean yet, don't panic, just return nothing.
            return []

        def rank_sort(i: forms.BoundField) -> int:
            if i.value() is None:
                # Unranked finalists should be sorted to the end. Convert the label
                # into a number that reflects its alphabetical order, and use that.
                return 1000 + ord(i.label[0].lower())
            return int(i.value())

        # This view of the fields is for use in emailing members; it has each
        # ranked finalist ordered by rank.
        return [
            (category, sorted(fieldsets, key=rank_sort))
            for category, fieldsets in self.fields_grouped_by_category
        ]
