import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_PATH, 'templates')
MEDIA_ROOT = os.path.join(BASE_PATH, 'media')
MEDIA_URL = '/ubuntu-website/media'

def media_processor(request):
    """
    add the ubuntu-website media path to template context processor. 
    """
    return {'ubuntu_website_media': MEDIA_URL}

def popup_check(request):
    return {'is_popup': request.REQUEST.has_key('_popup')}
   
