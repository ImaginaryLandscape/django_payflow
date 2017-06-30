import logging

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
import uuid

from requests import Request, Session

from django.conf import settings

logger = logging.getLogger(__name__)


"""A PayflowPayment object provides methods used to make various calls to the Payflow API.

For more details, see the Payflow Pro developers' guide at
https://www.paypalobjects.com/webstatic/en_US/developer/docs/pdf/pp_payflowpro_guide.pdf

and also details of paramaters that can be passed to the API at
https://developer.paypal.com/docs/classic/payflow/integration-guide/#core-credit-card-parameters

"""


class PayflowPayment(object):

    def __init__(self):
        self.partner = settings.DJANGO_PAYFLOW['PARTNER']
        self.merchant_login = settings.DJANGO_PAYFLOW['MERCHANT_LOGIN']
        self.user = settings.DJANGO_PAYFLOW['USER']
        self.password = settings.DJANGO_PAYFLOW['PASSWORD']

        if settings.DJANGO_PAYFLOW['TEST_MODE'] == True:
            self.endpoint_url = 'https://pilot-payflowpro.paypal.com/'
        else:
            self.endpoint_url = 'https://payflowpro.paypal.com/'

    def _generate_secure_token_id(self):
        """Generate secure token with uuid

        Returns: token: The 'SECURETOKENID' parameter that will be
            sent to the paypal api endpoint

        """

        uid = uuid.uuid4()
        token = uid.hex
        return token

    def _get_login_credentials(self):
        return dict(
            PARTNER=self.partner,
            VENDOR=self.merchant_login,
            USER=self.user,
            PWD=self.password
        )

    def _get_response_dict(self, custom_params):

        """Send a request to the Payflow API and return the response.

        """
        payload = self._get_login_credentials()
        payload.update(custom_params)

        payload_str = '&'.join("%s=%s" % (k, v) for k, v in payload.items())

        # PayPal doesn't allow double quotes in parameter values
        # because double quotes should surround the PARMLIST. So
        # replace any double quotes with single quotes.
        # https://www.paypalobjects.com/webstatic/en_US/developer/docs/pdf/pp_payflowpro_guide.pdf
        # under "connection parameters -> PARMLIST syntax guidelines"
        payload_str = payload_str.replace('"', "'")

        # Now surround with double quotes
        # According to their documentation you are supposed to
        # surround the parameter string with double quotes;
        # However the transaction does not go through if you do.
        # payload_str = "\"%s\"" % payload_str

        request = Request('POST', self.endpoint_url, data=payload_str)
        prepared_request = request.prepare()

        session = Session()
        response = session.send(prepared_request,)

        if response.status_code >= 300:
            raise Exception("Unable to connect to processor - http code {}".format(
                response.status_code))

        response_dict = urlparse.parse_qs(response.text)
        return response_dict

    def get_secure_token_and_secure_token_id(self, amount, **kwargs):
        """Create the SECURETOKEN and SECURETOKENID parameters need for a
        valid payflow transaction.

        Arguments:
            amount: the total amount the charge the credit card

        Returns:
            secure_token: the SECURETOKEN parameter that will be returned
                          in the response from PayPal
            secure_token_id: the SECURETOKENID paramter that will be sent
                             in the payflow request

        """
        secure_token_id = self._generate_secure_token_id()
        params = dict(
            TRXTYPE=kwargs.pop("TRXTYPE", "S"),  # Default is "S" for "sale", can be
                                                 # overridden as "A" for authorization only.
            AMT=amount,
            CREATESECURETOKEN="Y",
            SECURETOKENID=secure_token_id
        )
        params.update(kwargs)
        response_dict = self._get_response_dict(params)
        secure_token = response_dict.get('SECURETOKEN', None)
        if secure_token is None:  # raise an exception if there is no token in the response
            raise Exception(
                "`SECURETOKEN` not returned in response: {0}".format(response_dict['RESPMSG']))
        return secure_token[0], secure_token_id

    def capture_payment(self, pnref, **kwargs):
        """Capture a previously authorized PayPal transaction

        """
        params = dict(
            TRXTYPE="D",
            TENDER="C",
            ORIGID=pnref
        )
        params.update(kwargs)
        response_dict = self._get_response_dict(params)
        return response_dict

    def refund_payment(self, pnref, **kwargs):
        """Issue a refund for a previously authorized PayPal transaction

        """
        params = dict(
            TRXTYPE="C",
            TENDER="C",
            ORIGID=pnref
        )
        params.update(kwargs)
        response_dict = self._get_response_dict(params)
        return response_dict
