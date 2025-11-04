from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from datetime import datetime
from moesifapi.moesif_api_client import *
from moesifapi.app_config import AppConfig
from .async_iterator_wrapper import async_iterator_wrapper
from .logger_helper import LoggerHelper
from .event_mapper import EventMapper
from moesifapi.update_companies import Company
from moesifapi.update_users import User
from starlette.middleware.base import _StreamingResponse
from moesifpythonrequest.start_capture.start_capture import StartCapture
from moesifapi.config_manager import ConfigUpdateManager
from moesifapi.workers import BatchedWorkerPool, ConfigJobScheduler
from starlette.types import Message
from importlib.metadata import version
from distutils.version import LooseVersion
import math
import random
import logging
import time
from datetime import datetime

import queue
from datetime import datetime, timedelta
import atexit
from moesifapi.governance_manager import GovernanceRulesManager
from .send_batch_events import SendEventAsync
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

logger = logging.getLogger(__name__)


def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"[{datetime.utcnow()}] Function {func.__name__} took {execution_time_ms:.2f} milliseconds to execute.")
        return result

    return wrapper


class MoesifMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware for recording of request-response"""

    def __init__(self, settings=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if settings is None:
            raise Exception('Moesif Application ID is required in settings')
        self.settings = settings
        self.DEBUG = self.settings.get('DEBUG', False)

        self.initialize_logger()
        self.validate_settings()

        self.initialize_counter()
        self.initialize_client()
        # self.initialize_config()
        # self.initialize_worker_pool()


        Configuration.BASE_URI = self.settings.get("BASE_URI", "https://api.moesif.net")
        Configuration.version = 'moesifasgi-python/1.0.1'
        self.LOG_BODY = self.settings.get("LOG_BODY", True)
        self.batch_size = self.settings.get("BATCH_SIZE", 100)
        self.last_event_job_run_time = datetime(1970, 1, 1, 0, 0)  # Assuming job never ran, set it to epoch start time
        self.app_config = AppConfig()
        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
        self.send_async_events = SendEventAsync()
        self.scheduler = None
        self.config_etag = None
        self.is_event_job_scheduled = False
        self.max_queue_size = self.settings.get("EVENT_QUEUE_SIZE", 1000000)
        self.moesif_events_queue = queue.Queue(maxsize=self.max_queue_size)

        try:
            if self.config:
                self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(
                    self.config, self.DEBUG)
        except Exception as ex:
            if self.DEBUG:
                logger.info(f'Error while parsing application configuration on initialization:{str(ex)}')

        if self.settings.get('CAPTURE_OUTGOING_REQUESTS', False):
            try:
                if self.DEBUG:
                    logger.info('Start capturing outgoing requests')
                # Start capturing outgoing requests
                StartCapture().start_capture_outgoing(self.settings)
            except:
                logger.warning('Error while starting to capture the outgoing events')

        self.disable_transaction_id = self.settings.get('DISABLED_TRANSACTION_ID', False)
        self.starlette_version = version('starlette')

    def initialize_logger(self):
        """Initialize logger mirroring the debug and stdout behavior of previous print statements for compatibility"""
        logging.basicConfig(
            level=logging.DEBUG if self.DEBUG else logging.INFO,
            format='%(asctime)s\t%(levelname)s\tPID: %(process)d\tThread: %(thread)d\t%(funcName)s\t%(message)s',
            handlers=[logging.StreamHandler()]
        )

    def validate_settings(self):
        if self.settings is None or not self.settings.get("APPLICATION_ID", None):
            raise Exception("Moesif Application ID is required in settings")

    def initialize_counter(self):
        self.dropped_events = 0
        self.logger_helper = LoggerHelper()
        self.event_mapper = EventMapper()

    def initialize_client(self):
        self.api_version = self.settings.get("API_VERSION")
        self.client = MoesifAPIClient(self.settings.get("APPLICATION_ID"))
        self.api_client = self.client.api
        self.govern_manager = GovernanceRulesManager(self.api_client)

    def schedule_config_job(self):
        try:
            ConfigJobScheduler(self.DEBUG, self.config).schedule_background_job()
            self.is_config_job_scheduled = True
        except Exception as ex:
            self.is_config_job_scheduled = False
            if self.DEBUG:
                logger.info(f'Error while starting the config scheduler job in background: {str(ex)}')

    # def initialize_config(self):
    #     Configuration.BASE_URI = self.settings.get("BASE_URI", "https://api.moesif.net")
    #     Configuration.version = 'moesifasgi-python/1.0.1'
    #     self.LOG_BODY = self.settings.get("LOG_BODY", True)
    #
    #     self.app_config = AppConfig()
    #     self.config = ConfigUpdateManager(self.api_client, self.app_config, self.DEBUG)
    #     self.schedule_config_job()
    #
    # def initialize_worker_pool(self):
    #     # Create queues and threads which will batch and send events in the background
    #     self.worker_pool = BatchedWorkerPool(
    #         worker_count=self.settings.get("EVENT_WORKER_COUNT", 2),
    #         api_client=self.api_client,
    #         config=self.config,
    #         debug=self.DEBUG,
    #         max_queue_size=self.settings.get("EVENT_QUEUE_SIZE", 1000000),
    #         batch_size=self.settings.get("BATCH_SIZE", 100),
    #         timeout=self.settings.get("EVENT_BATCH_TIMEOUT", 1),
    #     )

    # Function to listen to the send event job response
    def moesif_event_listener(self, event):
        if event.exception:
            if self.DEBUG:
                logger.info('Error reading response from the scheduled job')
        else:
            if event.retval:
                response_etag, self.last_event_job_run_time = event.retval
                if response_etag is not None \
                        and self.config_etag is not None \
                        and self.config_etag != response_etag \
                        and datetime.utcnow() > self.last_updated_time + timedelta(minutes=5):
                    try:
                        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
                        self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(
                            self.config, self.DEBUG)
                    except Exception as ex:
                        if self.DEBUG:
                            logger.info(f'Error while updating the application configuration: {str(ex)}')

    def schedule_background_job(self):
        try:
            if not self.scheduler:
                self.scheduler = BackgroundScheduler(daemon=True)
            if not self.scheduler.get_jobs():
                self.scheduler.add_listener(self.moesif_event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
                self.scheduler.start()
                self.scheduler.add_job(
                    func=lambda: self.send_async_events.batch_events(self.api_client, self.moesif_events_queue,
                                                                     self.DEBUG, self.batch_size),
                    trigger=IntervalTrigger(seconds=2),
                    id='moesif_events_batch_job',
                    name='Schedule events batch job every 2 second',
                    replace_existing=True)

                # Avoid passing logging message to the ancestor loggers
                logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
                logging.getLogger('apscheduler.executors.default').propagate = False

                # Exit handler when exiting the app
                atexit.register(lambda: self.send_async_events.exit_handler(self.scheduler, self.DEBUG))
        except Exception as ex:
            if self.DEBUG:
                logger.info(f"Error when scheduling the job: {str(ex)}")

    def update_user(self, user_profile):
        User().update_user(user_profile, self.api_client, self.DEBUG)

    def update_users_batch(self, user_profiles):
        User().update_users_batch(user_profiles, self.api_client, self.DEBUG)

    def update_company(self, company_profile):
        Company().update_company(company_profile, self.api_client, self.DEBUG)

    def update_companies_batch(self, companies_profiles):
        Company().update_companies_batch(companies_profiles, self.api_client, self.DEBUG)

    def set_body(self, request: Request, body: bytes):
        async def receive() -> Message:
            return {"type": "http.request", "body": body}

        request._receive = receive

    async def get_body(self, request: Request) -> bytes:
        body = await request.body()
        # In higher version of Starlette(>0.27.0), we could read the body on the middleware without hanging
        # Reference: https://github.com/tiangolo/fastapi/discussions/8187#discussioncomment-7962881
        if LooseVersion(self.starlette_version) < LooseVersion("0.27.0"):
            self.set_body(request, body)
        return body

    @classmethod
    def get_time(cls):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    # Prepare response for the governance rule
    def prepare_response_content(self, body):
        response_content = None
        try:
            response_content = body[0]
        except Exception as ex:
            if self.DEBUG:
                logger.info(f"Error while preparing the response content: {str(ex)}")
        return response_content

    @measure_time
    async def dispatch(self, request, call_next):

        dispatch_start_time = time.time()

        # request time
        request_time = self.get_time()
        if self.DEBUG:
            logger.info(f"event request time: {str(request_time)}")

        # Read Request Body
        request_body = None
        if self.LOG_BODY:
            request_body = await self.get_body(request)

        # Prepare Event Request Model
        event_req = self.event_mapper.to_request(request, request_time, request_body, self.api_version,
                                                 self.disable_transaction_id, self.DEBUG)

        governed_response = {}
        # if self.config.have_governance_rules():
        #     # we must fire these hooks early.
        #     user_id = await self.logger_helper.get_user_id(self.settings, request, None, dict(request.headers), self.DEBUG)
        #     company_id = await self.logger_helper.get_company_id(self.settings, request, None, self.DEBUG)
        #     governed_response = self.config.govern_request(event_req, user_id, company_id, event_req.body)

        if self.govern_manager.has_rules():
            user_id = await self.logger_helper.get_user_id(self.settings, request, None, dict(request.headers), self.DEBUG)
            company_id = await self.logger_helper.get_company_id(self.settings, request, None, self.DEBUG)
            # governed_response = self.config.govern_request(event_req, user_id, company_id, event_req.body)
            governed_response = self.govern_manager.govern_request(self.config, event_req, user_id, company_id, event_req.body)

        response_start_time = time.time()
        blocked_by = None
        if 'blocked_by' in governed_response:
            # start response immediately, skip next step
            response_content = self.prepare_response_content(governed_response['body'])
            blocked_by = governed_response['blocked_by']
            async def generate_data():
                yield response_content
            headers = {k: self.logger_helper.sanitize_header_value(v) for k, v in governed_response['headers'].items() }
            response = _StreamingResponse(content=generate_data(), status_code=governed_response['status'], headers=headers)
        else:
            # Call the next middleware
            response = await call_next(request)

        # response = await call_next(request)

        response_end_time = time.time()
        response_time_ms = (response_end_time - response_start_time) * 1000  # Convert to milliseconds
        print(f"response took {response_time_ms:.2f} milliseconds to execute.")

        # response time
        response_time = self.get_time()
        if self.DEBUG:
            logger.info(f"event response time: {str(response_time)}")

        # Check if needs to skip the event
        skip = await self.logger_helper.should_skip(self.settings, request, response, self.DEBUG)
        if skip:
            if self.DEBUG:
                logger.info("Skipped Event using should_skip configuration option")
            return response

        # Read Response Body
        resp_body = None
        if self.LOG_BODY:
            # Consuming FastAPI response and grabbing body here
            resp_body = [section async for section in response.__dict__['body_iterator']]
            # Preparing FastAPI response
            response.__setattr__('body_iterator', async_iterator_wrapper(resp_body))

        # Prepare Event Response Model
        event_rsp = self.event_mapper.to_response(response, response_time, resp_body)

        # Add user, company, session_token, and metadata
        user_id = await self.logger_helper.get_user_id(self.settings, request, response, dict(request.headers),
                                                       self.DEBUG)
        company_id = await self.logger_helper.get_company_id(self.settings, request, response, self.DEBUG)
        session_token = await self.logger_helper.get_session_token(self.settings, request, response, self.DEBUG)
        metadata = await self.logger_helper.get_metadata(self.settings, request, response, self.DEBUG)

        # Prepare Event Model
        event_data = await self.event_mapper.to_event(event_req, event_rsp, user_id, company_id, session_token,
                                                      metadata, blocked_by)

        # Mask Event Model
        if self.logger_helper.is_coroutine_function(self.logger_helper.mask_event):
            event_data = await self.logger_helper.mask_event(event_data, self.settings, self.DEBUG)
        else:
            event_data = self.logger_helper.mask_event(event_data, self.settings, self.DEBUG)

        # Sampling percentage
        random_percentage = random.random() * 100
        self.sampling_percentage = self.app_config.get_sampling_percentage(event_data, self.config, user_id, company_id)

        # Add Weight to the event
        event_data.weight = 1 if self.sampling_percentage == 0 else math.floor(100 / self.sampling_percentage)

        if random_percentage >= self.sampling_percentage:
            logger.info(f"Skipped Event due to sampling percentage: {str(self.sampling_percentage)}"
                        f" and random percentage: {str(random_percentage)}")
            return response

        print(f"TransactionId {event_data.transaction_id}, 1_queue_start_time {dispatch_start_time}")
        # try:
        #     # Add Event to the queue if able and count the dropped event if at capacity
        #     if self.worker_pool.add_event(event_data):
        #         logger.debug("Add Event to the queue")
        #         if self.DEBUG:
        #             logger.info(f"Event added to the queue: {APIHelper.json_serialize(event_data)}")
        #     else:
        #         self.dropped_events += 1
        #         logger.info(f"Dropped Event due to queue capacity drop_count: {str(self.dropped_events)}")
        #         if self.DEBUG:
        #             logger.info(f"Event dropped: {APIHelper.json_serialize(event_data)}")
        # # add_event does not throw exceptions so this is unexepected
        # except Exception as ex:
        #     logger.exception(f"Error while adding event to the queue: {str(ex)}")

        try:
            if not self.is_event_job_scheduled and datetime.utcnow() > self.last_event_job_run_time + timedelta(
                    minutes=5):
                try:
                    self.schedule_background_job()
                    self.is_event_job_scheduled = True
                    self.last_event_job_run_time = datetime.utcnow()
                except Exception as ex:
                    self.is_event_job_scheduled = False
                    if self.DEBUG:
                        logger.info(f'Error while starting the event scheduler job in background: {str(ex)}')
            # Add Event to the queue
            if self.DEBUG:
                logger.info('Add Event to the queue')
            self.moesif_events_queue.put(event_data)
        except Exception as ex:
            if self.DEBUG:
                logger.info(f"Error while adding event to the queue: {str(ex)}")

        dispatch_end_time = time.time()
        dispatch_time_ms = (dispatch_end_time - dispatch_start_time) * 1000  # Convert to milliseconds
        print(f"Function dispatch took {dispatch_time_ms:.2f} milliseconds to execute.")

        return response
