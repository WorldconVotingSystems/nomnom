from django.db import models
from django.http import HttpRequest
from django_svcs.apps import svcs_from
from nomnom.nominate.models import NominatingMemberProfile

from nomnom.hugopacket.apps import S3Client


class ElectionPacket(models.Model):
    class Meta:
        permissions = [
            ("preview_packet", "Has early access to the packet"),
        ]

    # class Meta:
    #     app_label = "hugopacket"

    election = models.OneToOneField(
        "nominate.Election", on_delete=models.SET_NULL, null=True
    )

    name = models.CharField(max_length=255)
    s3_bucket_name = models.CharField(max_length=255)
    enabled = models.BooleanField(
        default=False,
        help_text="When not enabled, this packet's page will show up as not found",
    )

    def available(self, nominator: NominatingMemberProfile) -> bool:
        return self.election.user_can_vote(nominator.user)

    def __str__(self) -> str:
        return self.name if self.name else f"The {self.election.name} Packet"


class PacketFileGroup(models.Model):
    """An option group for packets;

    if not provided, the packet files are assumed to be a single group.

    All ungrouped packet files are assumed to be in the default group."""

    class Meta:
        ordering = ["position"]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Allows markdown")
    position = models.PositiveSmallIntegerField()


class PacketFile(models.Model):
    class Meta:
        ordering = ["position"]

    packet = models.ForeignKey(ElectionPacket, on_delete=models.CASCADE)
    group = models.ForeignKey(PacketFileGroup, on_delete=models.SET_NULL, null=True)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Allows markdown")
    available = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    # storage fields
    s3_object_key = models.CharField(max_length=65536)

    def __str__(self) -> str:
        return self.name if self.name else self.s3_object_key.split("/")[-1]

    def get_download_url(self, request: HttpRequest) -> str:
        s3 = svcs_from(request).get(S3Client)
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.packet.s3_bucket_name, "Key": self.s3_object_key},
            ExpiresIn=3600,
        )

        return presigned_url
