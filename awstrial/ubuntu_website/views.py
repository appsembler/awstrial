from django.shortcuts import render_to_response


def test(request):
    return render_to_response('ubuntu_website_base.html', {'ubuntu_website_media':'/ubuntu-website/media'})

