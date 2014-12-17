from django.conf import settings

# Querystring Parameter Names
INCLUDE_INVISIBLE_PARAM = 'include_invisible'
INCLUDE_PRIVATE_PARAM = 'include_private'
INCLUDE_SUBMISSIONS_PARAM = 'include_submissions'
NEAR_PARAM = 'near'
DISTANCE_PARAM = 'distance_lt'
BBOX_PARAM = 'bounds'
FORMAT_PARAM = 'format'
TEXTSEARCH_PARAM = 'search'

PAGE_PARAM = 'page'
PAGE_SIZE_PARAM = lambda: getattr(settings, 'REST_FRAMEWORK', {}).get('PAGINATE_BY_PARAM')
CALLBACK_PARAM = lambda view: (
    'callback'
    if view.get_content_negotiator().select_renderer(
        view.request, view.get_renderers(), view.format_kwarg)[0].format == 'jsonp'
    else None
)