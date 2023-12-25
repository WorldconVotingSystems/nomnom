from datetime import datetime

from celery import shared_task
from celery.signals import celeryd_after_setup
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

from nominate import models, reports

logger = get_task_logger(__name__)


@celeryd_after_setup.connect
def configure_django_from_settings(sender, instance, **kwargs):
    import django
    from django.conf import settings

    settings.configure()
    django.setup()


@shared_task
def send_nomination_report(report_name, **kwargs):
    if report_name == "nominations":
        election_id = kwargs["election_id"]
        election = models.Election.objects.get(slug=election_id)
        report = reports.NominationsReport(election=election)
        recipients = models.ReportRecipient.objects.filter(report_name=report_name)
        if not recipients:
            logger.warning("No recipients configured for the nominations report")
            return

        content = report.get_report_content()

        context = {"report_date": datetime.utcnow()}

        text_content = get_template("nominate/email/nomination_report.txt").render(
            context
        )
        html_content = get_template("nominate/email/nomination_report.html").render(
            context
        )

        message = EmailMultiAlternatives(
            subject="Nominations Report - {date}",
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
