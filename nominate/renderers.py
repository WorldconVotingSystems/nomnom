from django_bootstrap5.renderers import FieldRenderer


class BlankSafeFieldRenderer(FieldRenderer):
    def get_server_side_validation_classes(self):
        """Return CSS classes for server-side validation."""
        if self.field_errors:
            return "is-invalid"
        elif self.field.form.is_bound:
            if self.field.value():
                return "is-valid"
        return ""
