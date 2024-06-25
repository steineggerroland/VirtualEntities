import base64
import re
import uuid
from datetime import datetime
from urllib import parse, request
from urllib.request import Request


class CaldavTestClient:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    def create_calendar(self, person_name: str, name: str):
        url = parse.urlunsplit(
            ('http', f'{self.host}:{self.port}',
             f'/{self.user}/{person_name.replace(" ", "-").lower()}--{name.replace(" ", "-").lower()}', '', ''))
        encoded_auth = base64.b64encode(('%s:%s' % (self.user, self.password)).encode('ascii')).decode('utf-8')
        request.urlopen(Request(url=url, method='MKCOL', headers={'Authorization': f'Basic {encoded_auth}'}),
                        data=(create_calendar_data % name).encode('utf-8'), timeout=1)

    def create_event(self, person_name: str, calendar_name: str, summary: str, start: datetime, end: datetime,
                     description: str):
        uid = str(uuid.uuid4())
        dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        dtstart = start.strftime("%Y%m%dT%H%M%SZ")
        dtend = end.strftime("%Y%m%dT%H%M%SZ")
        event_data = create_event_data % (uid, dtstamp, dtstart, dtend, summary, description)

        url = parse.urlunsplit(
            ('http', f'{self.host}:{self.port}',
             f'/{self.user}/{person_name.replace(" ", "-").lower()}--{calendar_name.replace(" ", "-").lower()}/{uid}.ics',
             '', ''))
        encoded_auth = base64.b64encode(('%s:%s' % (self.user, self.password)).encode('ascii')).decode('utf-8')

        request.urlopen(Request(url=url, method='PUT',
                                headers={'Authorization': f'Basic {encoded_auth}', 'Content-Type': 'text/calendar'}),
                        data=event_data.encode('utf-8'), timeout=1)

    def create_appointment(self, person_name, calendar_name, appointment_summary):
        url = parse.urlunsplit(
            ('http', f'{self.host}:{self.port}',
             f'/{self.user}/{person_name.replace(" ", "-").lower()}--{calendar_name.replace(" ", "-").lower()}', '',
             ''))
        encoded_auth = base64.b64encode(('%s:%s' % (self.user, self.password)).encode('ascii')).decode('utf-8')
        request.urlopen(Request(url=url, method='PUT', headers={'Authorization': f'Basic {encoded_auth}'}),
                        data=(create_appointment_data.format(id=str(uuid.uuid4()), summary=appointment_summary,
                                                             created_at=f'{re.sub(r'\D', '', datetime.now().isoformat())}Z',
                                                             start_at=f'{re.sub(r'\D', '', datetime.today().isoformat())}Z',
                                                             end_at=f'{re.sub(r'\D', '', datetime.now().isoformat())}Z',
                                                             description='This is a new appointment')).encode('utf-8'),
                        timeout=1)


create_calendar_data = '''<?xml version="1.0" encoding="UTF-8" ?>
<create xmlns="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav" xmlns:I="http://apple.com/ns/ical/">
<set>
<prop>
<resourcetype>
<collection />
<C:calendar />
</resourcetype>
<C:supported-calendar-component-set>
<C:comp name="VEVENT" />
<C:comp name="VJOURNAL" />
<C:comp name="VTODO" />
</C:supported-calendar-component-set>
<displayname>%s</displayname>
<C:calendar-description>Keep shit secret!</C:calendar-description>
<I:calendar-color>#42E9A8ff</I:calendar-color>
</prop>
</set>
</create>'''

create_appointment_data = \
    '''        BEGIN:VCALENDAR
            VERSION:2.0
            BEGIN:VEVENT
            CREATED:{created_at}
            UID:{id}
            SUMMARY:$SUMMARY
            LOCATION:$LOCATION
            DTSTART:{start_at}
            DTSTAMP:{start_at}
            DTEND:{end_at}
            DESCRIPTION:{description}
            END:VEVENT
            END:VCALENDAR'''

create_event_data = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Your Organization//Your Calendar//EN
BEGIN:VEVENT
UID:%s
DTSTAMP:%s
DTSTART:%s
DTEND:%s
SUMMARY:%s
DESCRIPTION:%s
END:VEVENT
END:VCALENDAR'''
