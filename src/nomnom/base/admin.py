from django.core.exceptions import FieldDoesNotExist


class PrefillSingleton:
    def get_changeform_initial_data(self, request):
        data = super().get_changeform_initial_data(request)
        if fields := self.get_singleton_initial_fields(request):
            for maybe_field_tuple in fields:
                match maybe_field_tuple:
                    case (field_name, field_value_queryset, field_count_queryset):
                        ...
                    case (field_name, field_queryset):
                        field_count_queryset = field_queryset
                        field_value_queryset = field_queryset
                    case str(field_name):
                        field_queryset = self.infer_queryset(request, field_name)
                        field_count_queryset = field_queryset
                        field_value_queryset = field_queryset

                    case _:
                        raise ValueError("Invalid field format, must be one of...")

                if field_count_queryset is None:
                    continue

                if field_count_queryset.count() == 1:
                    data[field_name] = field_value_queryset.first()

        return data

    def infer_queryset(self, request, field_name):
        try:
            field_model = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return None

        if not field_model.is_relation:
            return None

        return field_model.related_model._default_manager.all()

    def get_singleton_initial_fields(self, request):
        return getattr(self, "singleton_initial_fields", [])
