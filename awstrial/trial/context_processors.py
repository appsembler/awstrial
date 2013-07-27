'''
Context processors for AWSTrial pages
'''
from django.conf import settings

def google_analytics_id(request):
    """Adds the google analytics id to the context if it's present."""
    return {
        'google_analytics_id': getattr(settings, 'GOOGLE_ANALYTICS_ID', None),
        }

def theme_assets_root(request):
    """Adds the ASSET_ROOT variable from the settings file"""
    root = getattr(settings, 'ASSET_ROOT', '')
    if root.endswith('/'):
        root = root[:-1]
    return {
        'ASSET_ROOT': root,
        }
