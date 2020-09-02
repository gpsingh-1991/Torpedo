from base import Base
from generic_client import GenericClient
from logger_agent import logger


class GENERIC(Base):

    def __init__(self, tc, auth, **kwargs):
        self.auth = auth
        self.gc = GenericClient(auth)
        self.tc = tc
        self.nodes = kwargs.get("nodes", None)
        self.extra_args = kwargs.get("nodes", None)
        logger.info(
            'Executing test case: {}'.format(tc['name'])
        )
        self.url = self.auth['test_service_endpoint']
        logger.info(
            'Executing test service endpoint: {}'.format(self.url)
        )

    def get(self):
        (tc_status, message) = self.gc.GET(self.url)
        return tc_status, message, self.tc

    def post(self, **kwargs):
        response = self.gc.POST(self.url, self.headers, self.data)
        return response
