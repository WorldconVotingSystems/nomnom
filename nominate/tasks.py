from datetime import datetime
from itertools import groupby
from operator import attrgetter

from celery import shared_task, states
from celery.app.task import Ignore
from celery.signals import celeryd_after_setup
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils.formats import localize

from nominate import models, reports

logger = get_task_logger(__name__)


@celeryd_after_setup.connect
def configure_django_from_settings(sender, instance, **kwargs):
    import django
    from django.conf import settings

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

        context = {"report_date": localize(report_date)}

        text_content = get_template("nominate/email/nomination_report.txt").render(
            context
        )
        html_content = get_template("nominate/email/nomination_report.html").render(
            context
        )

        message = EmailMultiAlternatives(
            subject=f"Nominations Report - {localize(report_date)}",
            from_email=None,  # use the default
            body=text_content,
            to=[settings.DEFAULT_FROM_EMAIL],
            bcc=[r.recipient_email for r in recipients],
            attachments=[
                (report.get_filename(), content, report.get_content_type()),
            ],
        )
        message.attach_alternative(html_content, "text/html")

        message.send()

    else:
        raise ValueError(f"Invalid report name: {report_name}")


@shared_task(bind=True)
def send_ballot(self, election_id, nominating_member_id):
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

    logger.info(f"Sending nominations for {election=} {member=}")

    member_nominations = models.Nomination.objects.filter(nominator=member).order_by(
        "category__ballot_position"
    )
    nominations = [
        (category, list(noms))
        for category, noms in groupby(member_nominations, attrgetter("category"))
    ]

    report_date = datetime.utcnow()
    context = {
        "report_date": localize(report_date),
        "member": member,
        "election": election,
        "nominations": nominations,
    }
    text_content = get_template("nominate/email/nominations_for_user.txt").render(
        context
    )
    html_content = get_template("nominate/email/nominations_for_user.html").render(
        context
    )
    message = EmailMultiAlternatives(
        subject=f"Your {election} - {localize(report_date)}",
        from_email=None,  # use the default
        body=text_content,
        to=[member.user.email],
    )
    message.attach_alternative(html_content, "text/html")

    message.send()
