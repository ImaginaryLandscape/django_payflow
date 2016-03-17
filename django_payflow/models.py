import logging

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
import uuid

from requests import Request, Session

from django.conf import settings

logger = logging.getLogger(__name__)


class PayflowPayment(object):

    def __init__(self, trxtype='S', **kwargs):
        """ Create object with the minimum requirements neccessary for succeful transaction.
        
         Arguments:
             trxtype: type of credit card transaction (default is 'S' for 'sale')
             (Other trxtype options listed at
             https://developer.paypal.com/docs/classic/payflow/integration-guide/#core-credit-card-parameters)
             kwargs: any extra arguments that payflow allows. ex (USER1, USER2, ORDID) etc..
        """

        self.partner = settings.DJANGO_PAYFLOW['PARTNER']
        self.merchant_login = settings.DJANGO_PAYFLOW['MERCHANT_LOGIN']
        self.user = settings.DJANGO_PAYFLOW['USER']
        self.password = settings.DJANGO_PAYFLOW['PASSWORD']
        self.trxtype = trxtype
        self.kwargs = kwargs

        if settings.DJANGO_PAYFLOW['TEST_MODE'] == True:
            self.endpoint_url = 'https://pilot-payflowpro.paypal.com/'
        else:
            self.endpoint_url = 'https://payflowpro.paypal.com/'

    def _generate_secure_token_id(self):
        """ Generate secure token with uuid 

        Returns:
            token: The 'SERCURETOKENID' parameter that will be sent to the paypal api endpoint
        """

        uid = uuid.uuid4()
        token = uid.hex
        return token

    def _prepare_secure_token_request(self, secure_token_id, amount):
        """ Prepare an http request object with all of the neccesarry request parameters.

        In order to access the payflow api and get a secure token, we need to authenticate 
        ourselves with our credentials and include (at a minimum) the following 
        parameters (TRXTYPE, AMT, CREATESECURETOKEN, SECURETOKENID). When this request is
        sent, it will return a 'secure token'.
        """
        
        payload = dict(
            PARTNER=self.partner,
            VENDOR=self.merchant_login,
            USER=self.user,
            PWD=self.password,
            TRXTYPE=self.trxtype,
            AMT=amount,
            CREATESECURETOKEN="Y",
            SECURETOKENID=secure_token_id,
        )

        payload.update(self.kwargs)

        request = Request('POST', self.endpoint_url, data=payload)
        prepared_request = request.prepare()

        return prepared_request

    def get_secure_token_and_secure_token_id(self, amount, **kwargs):
        """ Create the SECURETOKEN and SECURETOKENID parameters need for a valid payflow transaction.

        Arguments:
            amount: the total amount the charge the credit card

        Returns:
            secure_token: correponds to the SECURETOKEN parameter that will be returned after the 
                          payflow request is sent
            secure_token_id: corresponds to the SECURETOKENID paramter that will be sent in the
                             payflow request
        """

        secure_token_id = self._generate_secure_token_id()
        prepared_request = self._prepare_secure_token_request(secure_token_id, amount, **kwargs)

        session = Session()
        response = session.send(prepared_request,)

        if response.status_code >= 300:
            raise Exception("Unable to connect to processor - http code {}".format(
                response.status_code))

        response_dict = urlparse.parse_qs(response.text)

        secure_token = response_dict['SECURETOKEN'][0]

        return secure_token, secure_token_id
