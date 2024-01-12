import boto3
from django.db import models
from nominate.models import NominatingMemberProfile


class Packets(models.Model):
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

    packet = models.ForeignKey(Packets, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)

    # storage fields
    s3_object_key = models.CharField(max_length=65536)

    def __str__(self) -> str:
        return self.name if self.name else self.s3_object_key.split("/")[-1]

    def get_download_url(self) -> str:
        # TODO: probably factor this out into a strategy function somewhere that
        # constructs the S3 client for S3 providers that are not, in fact, AWS S3.
        s3 = boto3.client("s3")
        s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.packet.bucket_name, "Key": self.s3_object_key},
            ExpiresIn=3600,
        )

        return self.packet.election.get_download_url(self.s3_object_key)
