import smtplib
from datetime import UTC, datetime
from itertools import groupby
from operator import attrgetter

import sentry_sdk
from celery import shared_task, states
from celery.app.task import Ignore
from celery.signals import celeryd_after_setup
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.urls import reverse
from django.utils.formats import localize
from django_svcs.apps import svcs_from

from nomnom.convention import ConventionConfiguration, HugoAwards
from nomnom.nominate import hugo_awards, models, reports
from nomnom.nominate.forms import RankForm

logger = get_task_logger(__name__)


@celeryd_after_setup.connect
def configure_django_from_settings(sender, instance, **kwargs):
    import django

    if not settings.configured:
        settings.configure()
        django.setup()


@shared_task
def send_nomination_report(report_name, **kwargs):
    if report_name == "nominations":
        election_id = kwargs["election_id"]
        election = models.Election.objects.get(slug=election_id)
        report = reports.NominationsReport(election=election)
        recipients = models.ReportRecipient.objects.filter(report_name=report_name)
        report_date = datetime.utcnow()

        if not recipients:
            logger.warning("No recipients configured for the nominations report")
            return

        content = report.get_report_content()

        context = {
            "report_date": localize(report_date),
            "election": election,
            "ballot_url": reverse(
                "election:nominate", kwargs={"election_id": election_id}
            ),
        }

        text_content = get_template("nominate/email/nomination_report.txt").render(
            context
        )
        html_content = get_template("nominate/email/nomination_report.html").render(
            context
        )

        convention_configuration = svcs_from().get(ConventionConfiguration)

        for recipient in recipients:
            message = EmailMultiAlternatives(
                subject=f"Nominations Report - {localize(report_date)}",
                from_email=convention_configuration.get_hugo_admin_email(),  # use the default
                body=text_content,
                to=[recipient.recipient_email],
                attachments=[
                    (report.get_filename(), content, report.get_content_type()),
                ],
            )
            message.attach_alternative(html_content, "text/html")

            message.send()

    else:
        raise ValueError(f"Invalid report name: {report_name}")


@shared_task
def send_rank_report(**kwargs):
    election_id = kwargs["election_id"]
    election = models.Election.objects.get(slug=election_id)
    report = reports.RanksReport(election=election)
    recipients = models.ReportRecipient.objects.filter(report_name="ranks")
    explicit_recipients = kwargs.get("recipients", "")
    if explicit_recipients:
        explicit_recipient_addresses = explicit_recipients.split(",")
    else:
        explicit_recipient_addresses = []

    exclude_configured_recipients = kwargs.get("exclude_configured_recipients", False)

    recipient_addresses = explicit_recipient_addresses[:]
    if not exclude_configured_recipients:
        configured_recipient_addresses = [
            recipient.recipient_email for recipient in recipients
        ]
        recipient_addresses.extend(configured_recipient_addresses)

    report_date = datetime.now(UTC)

    if not recipient_addresses:
        logger.warning("No recipients configured for the ranks report")
        return

    content = report.get_report_content()

    rules = svcs_from().get(HugoAwards)

    context = {
        "report_date": localize(report_date),
        "election": election,
        "ballot_url": reverse("election:vote", kwargs={"election_id": election_id}),
        "categories": models.Category.objects.filter(election=election),
        "category_results": hugo_awards.get_winners_for_election(rules, election),
    }

    text_content = get_template("nominate/email/ranks_report.txt").render(context)
    html_content = get_template("nominate/email/ranks_report.html").render(context)

    convention_configuration = svcs_from().get(ConventionConfiguration)

    for recipient in recipient_addresses:
        message = EmailMultiAlternatives(
            subject=f"Ranks Report - {localize(report_date)}",
            from_email=convention_configuration.get_hugo_admin_email(),  # use the default
            body=text_content,
            to=[recipient],
            attachments=[
                (report.get_filename(), content, report.get_content_type()),
            ],
        )
        message.attach_alternative(html_content, "text/html")

        message.send()


@shared_task(bind=True)
def send_ballot(self, election_id, nominating_member_id, message=None):
    try:
        election = models.Election.objects.get(id=election_id)
        member = models.NominatingMemberProfile.objects.get(id=nominating_member_id)
    except Exception as e:
        logger.exception(
            f"Failed to find nominations for {election_id=} {nominating_member_id=}"
        )
        self.update_state(
            state=states.FAILURE, meta=f"Unable to find the election or member: {e}"
        )
        raise Ignore()

    # Associate the recipient with this task as the user. Note that this
    # might not be the user who requested the send, in the case of admin
    # operations on the ballot. However, it is the user who will or won't
    # receive the email sent by this process.
    sentry_sdk.set_user(user_info_from_user(member.user))

    logger.info(f"Sending nominations for {election=} {member=}")

    member_nominations = member.nomination_set.filter(
        category__election=election
    ).order_by("category__ballot_position")
    nominations = [
        (category, list(noms))
        for category, noms in groupby(member_nominations, attrgetter("category"))
    ]

    report_date = datetime.now(UTC)
    site_url = Site.objects.get_current().domain
    ballot_path = reverse("election:nominate", kwargs={"election_id": election.slug})
    ballot_url = f"https://{site_url}{ballot_path}"

    context = {
        "report_date": localize(report_date),
        "member": member,
        "election": election,
        "nominations": nominations,
        "ballot_url": ballot_url,
        "message": message,
    }
    text_content = get_template("nominate/email/nominations_for_user.txt").render(
        context
    )
    html_content = get_template("nominate/email/nominations_for_user.html").render(
        context
    )

    convention_configuration = svcs_from().get(ConventionConfiguration)

    email = EmailMultiAlternatives(
        subject=f"Your {election} Nominations - {localize(report_date)}",
        from_email=convention_configuration.get_hugo_help_email(),  # use the default
        body=text_content,
        to=[member.user.email],
    )
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
    except smtplib.SMTPRecipientsRefused as e:
        sentry_sdk.capture_exception(e)


@shared_task(bind=True)
def send_voting_ballot(self, election_id, voting_member_id, message=None):
    try:
        election = models.Election.objects.get(id=election_id)
        member = models.NominatingMemberProfile.objects.get(id=voting_member_id)
    except Exception as e:
        logger.exception(
            f"Failed to find nominations for {election_id=} {voting_member_id=}"
        )
        self.update_state(
            state=states.FAILURE, meta=f"Unable to find the election or member: {e}"
        )
        raise Ignore()

    # Associate the recipient with this task as the user. Note that this
    # might not be the user who requested the send, in the case of admin
    # operations on the ballot. However, it is the user who will or won't
    # receive the email sent by this process.
    sentry_sdk.set_user(user_info_from_user(member.user))

    logger.info(f"Sending votes for {election=} {member=}")

    finalists = models.Finalist.objects.filter(category__election=election)
    ranks = models.Rank.objects.filter(finalist__in=finalists, membership=member)

    report_date = datetime.utcnow()
    site_url = Site.objects.get_current().domain
    ballot_path = reverse("election:vote", kwargs={"election_id": election.slug})
    ballot_url = f"https://{site_url}{ballot_path}"

    form = RankForm(finalists=finalists, ranks=ranks)
    # run "clean" to populate the form with the existing data and
    # group the finalists by category into display-oriented structures.
    # We're doing a bit of a hack here, because full_clean requires posted
    # data that we don't have, and we're not really validating the form.
    form.cleaned_data = {}
    form.clean()

    context = {
        "report_date": localize(report_date),
        "member": member,
        "election": election,
        "form": form,
        "ballot_url": ballot_url,
        "message": message,
    }
    text_content = get_template("nominate/email/votes_for_user.txt").render(context)
    html_content = get_template("nominate/email/votes_for_user.html").render(context)

    convention_configuration = svcs_from().get(ConventionConfiguration)

    email = EmailMultiAlternatives(
        subject=f"Your {election} Votes - {localize(report_date)}",
        from_email=convention_configuration.get_hugo_help_email(),  # use the default
        body=text_content,
        to=[member.user.email],
    )
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
    except smtplib.SMTPRecipientsRefused as e:
        sentry_sdk.capture_exception(e)


def user_info_from_user(user: AbstractUser):
    return {
        "id": str(user.pk),
        "email": user.email,
        "username": user.username,
    }
