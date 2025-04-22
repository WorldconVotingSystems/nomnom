from dataclasses import dataclass
from typing import Annotated
from urllib.parse import urlparse

import boto3
import botocore.client
from botocore.exceptions import BotoCoreError
from django.apps import AppConfig
from django.conf import settings
from django.http import Http404
from django_svcs.apps import get_registry, svcs_from

from nomnom.convention import ConventionConfiguration

S3Client = Annotated[botocore.client.BaseClient, "s3"]


@dataclass
class PacketItemResolver:
    s3_client: S3Client
    bucket_name: str
    file_key: str
    expiry: int = 60 * 60  # 1 hour

    def get_url(self) -> str:
        """Get a presigned URL for the file key in the bucket."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": self.file_key},
                ExpiresIn=self.expiry,
            )
        except BotoCoreError:
            raise Http404("Unable to resolve the packet item")
        return url


class DigitalOceanCDNResolver(PacketItemResolver):
    def get_url(self) -> str:
        """Get a presigned URL for the file key in the bucket."""
        base_url = super().get_url()
        parsed_url = urlparse(base_url)
        region_name = getattr(settings, "HUGOPACKET_AWS_REGION", "nyc3")
        cdn_url = getattr(
            settings,
            "HUGOPACKET_AWS_CDN_HOSTNAME",
            f"{self.bucket_name}.{region_name}.cdn.digitaloceanspaces.com",
        )

        # replace only the hostname in the URL with the CDN URL
        replaced = parsed_url._replace(netloc=cdn_url)
        replaced_url = replaced.geturl()
        return replaced_url


@dataclass
class PacketAccess:
    client: S3Client
    resolver_type: type[PacketItemResolver]

    def resolver(self, bucket_name: str, file_key: str) -> PacketItemResolver:
        return self.resolver_type(
            s3_client=self.client,
            bucket_name=bucket_name,
            file_key=file_key,
        )


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

        registry = get_registry()
        if self.backend == "digitalocean":
            registry.register_factory(S3Client, self.make_digitalocean_client)
            registry.register_factory(
                PacketAccess, self.make_digitalocean_packet_access
            )

        else:
            registry.register_factory(S3Client, self.make_s3_client)
            registry.register_factory(PacketAccess, self.make_s3_packet_access)

    def make_s3_client(self) -> botocore.client.BaseClient:
        # assume the region and credentials are set up in the environment
        return boto3.client(
            "s3",
        )

    def make_s3_packet_access(self) -> PacketAccess:
        client = self.make_s3_client()
        return PacketAccess(
            client=client,
            resolver_type=PacketItemResolver,
        )

    def make_digitalocean_client(self):
        region_name = getattr(settings, "HUGOPACKET_AWS_REGION", "nyc3")
        endpoint_url = getattr(
            settings,
            "HUGOPACKET_AWS_ENDPOINT",
            f"https://{region_name}.digitaloceanspaces.com",
        )
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            config=boto3.session.Config(s3={"addressing_style": "virtual"}),
        )

    def make_digitalocean_packet_access(self) -> PacketAccess:
        client = self.make_digitalocean_client()
        use_cdn = (
            getattr(settings, "HUGOPACKET_AWS_USE_CDN", False)
            or getattr(settings, "HUGOPACKET_AWS_CDN_HOSTNAME", None) is not None
        )
        if use_cdn:
            return PacketAccess(
                client=client,
                resolver_type=DigitalOceanCDNResolver,
            )
        else:
            return PacketAccess(
                client=client,
                resolver_type=PacketItemResolver,
            )
