from typing import Annotated

import boto3
import botocore.client
from django.apps import AppConfig
from django.conf import settings
from django_svcs.apps import get_registry, svcs_from

from nomnom.convention import ConventionConfiguration

S3Client = Annotated[botocore.client.BaseClient, "s3"]


class HugopacketConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nomnom.hugopacket"
    verbose_name = "Hugo Packet"
    label = "hugopacket"

    def ready(self) -> None:
        # TODO register different services here once I know what they are.
        self.backend = svcs_from().get(ConventionConfiguration).hugo_packet_backend

        # we assume an S3-like backend for now; if this needs to change, we'll need model
        # changes and configuration changes.

        if self.backend == "digitalocean":
            get_registry().register_factory(S3Client, self.make_digitalocean_client)
        else:
            get_registry().register_factory(S3Client, self.make_s3_client)

    def make_s3_client(self) -> botocore.client.BaseClient:
        # assume the region and credentials are set up in the environment
        return boto3.client(
            "s3",
        )

    def make_digitalocean_client(self):
        region_name = getattr(settings, "HUGOPACKET_AWS_REGION", "nyc3")
        endpoint_url = getattr(
            settings,
            "HUGOPACKET_AWS_ENDPOINT",
            f"https://{region_name}.digitaloceanspaces.com",
        )
        return boto3.client("s3", endpoint_url=endpoint_url, region_name=region_name)
