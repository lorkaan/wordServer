
auth_session_key = "auth"
auth_ip_key = "ip"

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # Gets the first IP in the list
    else:
        ip = request.META.get('REMOTE_ADDR')  # Fallback to direct IP
    return ip

def set_auth_token(request):
    ip_addr = get_client_ip(request)
    request.session[auth_session_key] = True
    request.session[auth_ip_key] = ip_addr

def verify_auth(request):
    ip_addr = get_client_ip(request)
    authed_ip = request.session.get(auth_ip_key, None)
    auth_flag = request.session.get(auth_session_key, False)
    if auth_flag and authed_ip != None and ip_addr == authed_ip:
        return True
    else:
        return False
    
def clear_session(request):
    request.session.flush()