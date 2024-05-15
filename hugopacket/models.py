from django.db import models
from django.http import HttpRequest
from django_svcs.apps import svcs_from
from nominate.models import NominatingMemberProfile

from hugopacket.apps import S3Client


class ElectionPacket(models.Model):
    # class Meta:
    #     app_label = "hugopacket"

    election = models.OneToOneField(
        "nominate.Election", on_delete=models.SET_NULL, null=True
    )

    name = models.CharField(max_length=255)
    s3_bucket_name = models.CharField(max_length=255)

    def available(self, nominator: NominatingMemberProfile) -> bool:
        return self.election.user_can_vote(nominator.user)

    def __str__(self) -> str:
        return self.name if self.name else f"The {self.election.name} Packet"


class PacketFile(models.Model):
    # class Meta:
    #     app_label = "hugopacket"

    packet = models.ForeignKey(ElectionPacket, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)

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
