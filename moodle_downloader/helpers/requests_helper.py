from requests_html.requests_html import HTMLSession, HTMLResponse

def get_session() -> HTMLSession:
    """Create a session and return it"""
    session = HTMLSession()
    return session

def get_request(url : str, session : HTMLSession, discard : bool = True, js_render : bool = False) -> HTMLResponse:
    """Send a get request to the given url"""
    r : HTMLResponse = session.get(url)
    if js_render and r.ok:
        r.html.render(sleep=1, send_cookies_session = True)
    return r

def post_request(url : str, data : dict, session : HTMLSession) -> HTMLResponse:
    r = session.post(url, data=data)
    return r