import csv
from io import TextIOWrapper

from django import forms
from django.contrib import admin
from django.db import models as django_models
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django_admin_action_forms import (
    AdminActionForm,
    AdminActionFormsMixin,
    action_with_form,
)

from nomnom.base.admin import PrefillSingleton

from . import models


@admin.register(models.ElectionPacket)
class ElectionPacketAdmin(admin.ModelAdmin):
    list_display = ["name", "election", "enabled"]
    list_filter = ["enabled"]
    actions = ["create_sections_from_categories"]

    def create_sections_from_categories(self, request, queryset):
        """Create hierarchical section structure from election categories."""
        from nomnom.nominate.models import Category

        for packet in queryset:
            if not packet.election:
                self.message_user(
                    request,
                    f"Skipping {packet.name}: no election associated",
                    level="warning",
                )
                continue

            categories = Category.objects.filter(election=packet.election).order_by(
                "ballot_position"
            )

            sections_created = 0
            for position, category in enumerate(categories):
                # Create top-level section for the category
                section, created = models.PacketSection.objects.get_or_create(
                    packet=packet,
                    parent=None,
                    name=category.name,
                    defaults={
                        "position": position,
                        "description": category.description,
                    },
                )

                if created:
                    sections_created += 1

            self.message_user(
                request,
                f"Created {sections_created} sections for {packet.name} from categories",
            )

    create_sections_from_categories.short_description = (
        "Create sections from election categories"
    )


@admin.register(models.PacketSection)
class PacketSectionAdmin(PrefillSingleton, admin.ModelAdmin):
    list_display = ["name", "packet", "parent", "position", "depth"]
    list_filter = ["packet"]
    list_editable = ["position"]
    ordering = ["packet", "parent", "position"]
    search_fields = ["name", "description"]
    singleton_initial_fields = ["packet"]

    def depth(self, obj):
        return obj.depth

    depth.short_description = "Level"


class AssignSectionForm(AdminActionForm):
    """Form for bulk assigning a section to packet files."""

    section = forms.ModelChoiceField(
        required=True,
        queryset=models.PacketSection.objects.select_related("packet").order_by(
            "packet__name", "position"
        ),
        help_text="Select the section to assign to the selected packet files",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__post_init__(self.modeladmin, self.request, self.queryset)

    def __post_init__(self, modeladmin, request, queryset):
        """Customize the section queryset based on selected packet files."""
        # Get unique packets from the selected files
        packets = {pf.packet for pf in queryset if pf.packet}

        if packets:
            # Filter sections to only those belonging to the selected packets
            self.fields["section"].queryset = self.fields["section"].queryset.filter(
                packet__in=packets
            )

            # Add better labels showing packet name and section hierarchy
            def label_with_depth(obj):
                indent = "  " * obj.depth
                return f"{obj.packet.name} → {indent}{obj.name}"

            self.fields["section"].label_from_instance = label_with_depth

    class Meta:
        list_objects = True
        help_text = "Assign these packet files to a section?"


@action_with_form(AssignSectionForm, description="Assign section to packet files")
def assign_section(modeladmin, request, queryset, data):
    """Bulk action to assign a section to multiple packet files."""
    section = data.get("section")
    if section:
        count = queryset.update(section=section)
        modeladmin.message_user(
            request,
            f"Successfully assigned {count} packet file(s) to section '{section.name}'",
        )


@admin.register(models.PacketFile)
class PacketFileAdmin(AdminActionFormsMixin, PrefillSingleton, admin.ModelAdmin):
    list_display = [
        "name",
        "packet",
        "section",
        "access_type",
        "position",
        "available",
        "access_stats",
    ]
    list_filter = ["packet", "access_type", "available", "section"]
    list_editable = ["position", "available"]
    search_fields = ["name", "description"]
    readonly_fields = ["code_import_link"]
    actions = [assign_section]
    singleton_initial_fields = ["packet"]

    def access_stats(self, obj):
        count = obj.member_accesses.count()
        total_accesses = (
            obj.member_accesses.aggregate(total=django_models.Sum("access_count"))[
                "total"
            ]
            or 0
        )
        return "{} members ({} total)".format(count, total_accesses)

    access_stats.short_description = "Access Stats"

    def code_import_link(self, obj):
        if obj.pk and obj.access_type == models.PacketFile.AccessType.CODE:
            from django.urls import reverse
            from django.utils.html import format_html

            url = reverse("admin:hugopacket_distributioncode_import", args=[obj.pk])
            code_count = obj.code_pool.count()
            unassigned_count = obj.code_pool.filter(access_record__isnull=True).count()
            return format_html(
                '<a href="{}" class="button">Import Codes from CSV</a><br>'
                '<span style="color: #666; font-size: 11px;">'
                "Current pool: {} total ({} unassigned)</span>",
                url,
                code_count,
                unassigned_count,
            )
        return "(Save file first, or change access type to CODE)"

    code_import_link.short_description = "Distribution Codes"

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                None,
                {
                    "fields": (
                        "name",
                        "description",
                        "packet",
                        "section",
                        "position",
                        "available",
                        "access_type",
                    )
                },
            ),
        ]

        if obj:
            if obj.access_type == models.PacketFile.AccessType.CODE:
                fieldsets.append(
                    (
                        "Code Management",
                        {
                            "fields": ("code_display_format", "code_import_link"),
                            "description": "Manage distribution codes for this packet item. Ignored if the access type is 'file'",
                        },
                    )
                )
            elif obj.access_type == models.PacketFile.AccessType.DOWNLOAD:
                fieldsets.append(
                    (
                        "Download Configuration",
                        {
                            "fields": ("s3_object_key",),
                            "description": "Configure the S3 object key for this downloadable packet item. Ignored if the access type is 'code'",
                        },
                    )
                )
            else:
                fieldsets.append(
                    (
                        "Access Configuration",
                        {
                            "fields": (),
                            "description": "No additional configuration needed for this access type.",
                        },
                    )
                )
        else:
            fieldsets.append(
                (
                    "Download Configuration",
                    {
                        "fields": ("s3_object_key",),
                        "description": "Configure the S3 object key for this downloadable packet item. Ignored if the access type is 'code'",
                    },
                )
            )
            fieldsets.append(
                (
                    "Code Management",
                    {
                        "fields": ("code_display_format",),
                        "description": "Manage distribution codes for this packet item. Ignored if the access type is 'file'",
                    },
                )
            )

        return fieldsets


@admin.register(models.PacketItemAccess)
class PacketItemAccessAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "packet_file",
        "access_count",
        "first_accessed_at",
        "last_accessed_at",
        "has_code",
    ]
    list_filter = ["packet_file__packet", "packet_file"]
    search_fields = [
        "member__user__email",
        "member__preferred_name",
        "packet_file__name",
    ]
    readonly_fields = [
        "first_accessed_at",
        "last_accessed_at",
        "access_count",
    ]
    date_hierarchy = "last_accessed_at"

    def has_code(self, obj):
        return obj.distribution_code is not None

    has_code.boolean = True
    has_code.short_description = "Code Assigned"


class DistributionCodeImportForm(forms.Form):
    csv_file = forms.FileField(
        help_text="CSV file with 'code' and optional 'notes' columns"
    )


@admin.register(models.DistributionCode)
class DistributionCodeAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "packet_file",
        "member_display",
        "assigned_at",
        "assigned_by",
    ]
    list_filter = ["packet_file", "assigned_at"]
    search_fields = ["code", "notes"]
    readonly_fields = ["assigned_at", "member_display"]

    def member_display(self, obj):
        return obj.member.display_name if obj.member else "(unassigned)"

    member_display.short_description = "Assigned To"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:packet_file_id>/import-codes/",
                self.admin_site.admin_view(self.import_codes_view),
                name="hugopacket_distributioncode_import",
            ),
        ]
        return custom_urls + urls

    def import_codes_view(self, request, packet_file_id):
        from django.contrib import messages
        from django.db import IntegrityError

        packet_file = models.PacketFile.objects.get(pk=packet_file_id)

        if request.method == "POST":
            form = DistributionCodeImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = TextIOWrapper(
                    request.FILES["csv_file"].file, encoding="utf-8"
                )

                # Read entire file to detect format
                content = csv_file.read()
                csv_file.seek(0)

                # Try to detect if there's a header
                lines = content.strip().split("\n")
                first_line = lines[0] if lines else ""
                has_header = "," in first_line and "code" in first_line.lower()

                codes_created = 0
                codes_updated = 0
                duplicates = []
                seen_codes = set()

                if has_header:
                    # CSV with headers
                    reader = csv.DictReader(csv_file)
                    for row_num, row in enumerate(
                        reader, start=2
                    ):  # Start at 2 since header is line 1
                        code = row.get("code", "").strip()
                        notes = row.get("notes", "").strip()

                        if not code:
                            continue

                        # Check for duplicates within file
                        if code in seen_codes:
                            duplicates.append(f"Line {row_num}: {code}")
                            continue
                        seen_codes.add(code)

                        try:
                            models.DistributionCode.objects.create(
                                packet_file=packet_file,
                                code=code,
                                notes=notes,
                            )
                            codes_created += 1
                        except IntegrityError:
                            # Code exists - check if we need to update notes
                            existing = models.DistributionCode.objects.filter(
                                packet_file=packet_file, code=code
                            ).first()
                            if existing and notes and existing.notes != notes:
                                existing.notes = notes
                                existing.save()
                                codes_updated += 1
                else:
                    # Simple format: one code per line (no notes to update)
                    for row_num, line in enumerate(lines, start=1):
                        code = line.strip()

                        if not code:
                            continue

                        # Check for duplicates within file
                        if code in seen_codes:
                            duplicates.append(f"Line {row_num}: {code}")
                            continue
                        seen_codes.add(code)

                        try:
                            models.DistributionCode.objects.create(
                                packet_file=packet_file,
                                code=code,
                            )
                            codes_created += 1
                        except IntegrityError:
                            # Code exists - simple format has no notes to update
                            pass

                # Show results
                if codes_created > 0 or codes_updated > 0:
                    msg_parts = []
                    if codes_created > 0:
                        msg_parts.append(f"imported {codes_created} new codes")
                    if codes_updated > 0:
                        msg_parts.append(f"updated {codes_updated} existing codes")
                    messages.success(
                        request,
                        f"Successfully {' and '.join(msg_parts)} for {packet_file.name}",
                    )

                if duplicates:
                    messages.warning(
                        request,
                        f"Skipped {len(duplicates)} duplicate codes within file: "
                        + ", ".join(duplicates[:5])
                        + (
                            f" (and {len(duplicates) - 5} more)"
                            if len(duplicates) > 5
                            else ""
                        ),
                    )

                return redirect("admin:hugopacket_packetfile_change", packet_file_id)
        else:
            form = DistributionCodeImportForm()

        context = {
            "form": form,
            "packet_file": packet_file,
            "opts": self.model._meta,
        }
        return render(request, "admin/hugopacket/import_codes.html", context)

    actions = ["export_codes"]

    def export_codes(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="distribution_codes.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(["Code", "Packet File", "Member", "Assigned At", "Notes"])

        for code in queryset:
            writer.writerow(
                [
                    code.code,
                    str(code.packet_file),
                    code.member.display_name if code.member else "",
                    code.assigned_at.isoformat() if code.assigned_at else "",
                    code.notes,
                ]
            )

        return response

    export_codes.short_description = "Export selected codes to CSV"
