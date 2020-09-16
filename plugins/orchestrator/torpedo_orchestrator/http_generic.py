from base import Base
from generic_client import GenericClient
from logger_agent import logger


class HTTP_GENERIC(Base):

    def __init__(self, tc, auth, **kwargs):
        self.auth = auth
        self.gc = GenericClient(auth)
        self.tc = tc
        self.url = tc['url']
        self.headers = tc['headers']
        self.body = tc['body']
        custom_req = kwargs.get("custom_req", None)
        logger.info(
            'Executing test case: {}'.format(tc['name'])
        )
        logger.info(
            'Executing test service endpoint: {}'.format(self.url)
        )

    def get(self):
        (tc_status, message) = self.gc.GET(self.url, headers=self.headers, data=self.body)
        return tc_status, message, self.tc

    def post(self, **kwargs):
        response = self.gc.POST(self.url, self.headers, self.body)
        return response
