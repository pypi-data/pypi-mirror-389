from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


def dbevent_url_context(request: HttpRequest):
    dbevent_event_id = request.event.settings.dbevent_event_id
    locale = "de" if request.LANGUAGE_CODE.startswith("de") else "en"
    booking_url = f"https://www.eventanreise-bahn.de/{locale}/events/{dbevent_event_id}"
    return {
        "booking_url": booking_url,
        "event_id": dbevent_event_id,
        "faq_url": "https://www.bahn.de/eventangebote-teilnehmende",
        "event": str(request.event),
        "booking_button": f'<a href="{booking_url}" class="btn btn-success">{_("Book online now")}</a>',
    }
