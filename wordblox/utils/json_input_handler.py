from django.http import HttpResponse
from django.conf import settings
import logging

class JsonInputHandler:

    return_success_key = "success"

    logger = logging.getLogger(__name__)

    @classmethod
    def is_debug(cls):
        return settings.__dict__.get("DEBUG", False)

    @classmethod
    def print_headers(cls, request):
        cls.logger.error("REQUEST HEADERS:")
        for k, v in request.META.items():
            cls.logger.error(f"{k}: {v}")
        
    @classmethod
    def log_object(cls, obj, label=""):
        cls.logger.error(f"----- {label} -----")
        for key, val in obj.items():
            cls.logger.error(f"\n\tKey: {key}\n\tValue: {val}")
        cls.logger.error("---------------------")

    @classmethod
    def log_array(cls, array, label=""):
        cls.logger.error(f"------ {label} -----")
        for elem in array:
            cls.logger.error(f"n\tElem: {elem}")
        cls.logger.error("---------------------")

    @classmethod
    def post_input(cls, request):
        return HttpResponse(status=500)

    @classmethod
    def get_input(cls, request):
        return HttpResponse(status=403)

    @classmethod
    def run(cls, request):
        if request.method == 'POST':
            return cls.post_input(request)
        else:
            return cls.get_input(request)
        
class DomainLockedJsonHandler(JsonInputHandler):

    domain_param_key = "domain"

class LoginDomainLockedJsonHandler(DomainLockedJsonHandler):

    username_param_key = "username"
    password_param_key = "password"