"""
    This is where tokens that are required by the user are generated

    It is separate from any views, even though it handles some
    web requests from clients as it is kind of independent of
    the wordtag application.

    Currently, only tokens that are generated for CRSF verification
    are generated here as there is not a need at present for other tokens.
"""
from django.http import JsonResponse
from django.middleware.crsf import get_token

def get_crsf_token(request):
    return JsonResponse({'crsfToken': get_token(request)})
