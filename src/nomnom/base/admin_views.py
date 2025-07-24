from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from passkeys.models import UserPasskey


@method_decorator([login_required, staff_member_required], name="dispatch")
class AdminPasskeyManagementView(TemplateView):
    """Admin view for managing passkeys associated with the current user's account."""

    template_name = "admin/passkey_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Manage Your Passkeys",
                "passkeys": UserPasskey.objects.filter(user=self.request.user).order_by(
                    "-last_used"
                ),
                "has_passkeys": UserPasskey.objects.filter(
                    user=self.request.user
                ).exists(),
                "enroll_url": reverse("admin:passkey_enroll"),
            }
        )
        return context

    def post(self, request: HttpRequest) -> HttpResponse:
        """Handle passkey deletion."""
        passkey_id = request.POST.get("delete_passkey")
        if passkey_id:
            try:
                passkey = UserPasskey.objects.get(id=passkey_id, user=request.user)
                passkey_name = passkey.name
                passkey.delete()
                messages.success(request, f'Passkey "{passkey_name}" has been removed.')
            except UserPasskey.DoesNotExist:
                messages.error(request, "Passkey not found.")

        return redirect("admin:passkey_management")


@method_decorator([login_required, staff_member_required], name="dispatch")
class AdminPasskeyEnrollView(TemplateView):
    """Admin view for enrolling a new passkey."""

    template_name = "admin/passkey_enroll.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Add New Passkey",
                "management_url": reverse("admin:passkey_management"),
            }
        )
        return context
