import decimal
import urllib.parse
import uuid
from django.core.management.base import BaseCommand
from django.conf import settings
from requests import Request, Session


def _get_login_credentials(self, use_live=False):

    if PFP_CREDS := getattr(settings, "PFP_CREDS", None):
        # Use the test creds unless overridden
        DJANGO_PAYFLOW = PFP_CREDS["LIVE"] if use_live else PFP_CREDS["TEST"]
        return dict(
            PARTNER=settings.DJANGO_PAYFLOW['PARTNER'],
            VENDOR=settings.DJANGO_PAYFLOW['MERCHANT_LOGIN'],
            USER=settings.DJANGO_PAYFLOW['USER'],
            PWD=settings.DJANGO_PAYFLOW['PASSWORD']
        )
    else:
        print("Warning: Payflow Pro credentials not found in settings")
        return dict()

"""
This script assumes that in your settings, Payflow credentials are handled like this:

    PFP_CREDS = {
        "TEST": {
            "PARTNER": 'PayPal',
            "MERCHANGT_LOGIN": 'imaginaryosf',
            "USER": 'webtransactions',
            "PASSWORD": 'F0st3r95'
        },
        "LIVE": {
            "PARTNER" = 'PayPal',
            "MERCHANT_LOGIN": 'osfecommerce',
            "USER": 'website',
            "PASSWORD": 'vw9ZLgDZnuSGA'
        }
    }

If they are not, individual values can be passed as parameters to the command.
"""
class Command(BaseCommand):
    help = 'Test connection to PayPal using test credentials'

    def add_arguments(self, parser):
        parser.add_argument('--live', action='store_true', dest='live', default=False, help='Use live credentials instead of test credentials')
        parser.add_argument('--partner', type=str, default="")
        parser.add_argument('--vendor', type=str, default="")
        parser.add_argument('--user', type=str, default="")
        parser.add_argument('--pwd', type=str, default="")

    def handle(self, *args, **options):
        if options['live']:
            endpoint_url = 'https://payflowpro.paypal.com/'
        else:
            endpoint_url = 'https://pilot-payflowpro.paypal.com/'

        creds = _get_login_credentials(options['live'])
        if partner := options['partner']:
            creds["PARTNER"] = partner
        if vendor := options['vendor']:
            creds["MERCHANT_LOGIN"] = vendor
        if user := options['user']:
            creds["USER"] = user
        if pwd := options['pwd']:
            creds["PWD"] = pwd

        params = dict (
            TRXTYPE="A",
            AMT=decimal.Decimal("1.00"),
            CREATESECURETOKEN="Y",
            SECURETOKENID=uuid.uuid4().hex
        )

        payload = creds
        payload.update(params)
        payload_str = '&'.join("%s=%s" % (k, v) for k, v in payload.items())
        payload_str = payload_str.replace('"',"'")
        request = Request('POST', endpoint_url, data=payload_str)
        prepared_request = request.prepare()
        session = Session()
        response = session.send(prepared_request,)

        if response.status_code >= 300:
            raise Exception("Unable to connect to processor - http code {}".format(
                response.status_code))

        response_dict = urllib.parse.parse_qs(response.text)
        if "SECURETOKEN" in response_dict:
            print("Test successful")
        else:
            print("Test failed")
