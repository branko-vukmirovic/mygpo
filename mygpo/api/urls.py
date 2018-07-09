from django.urls import path, register_converter
from django.conf import settings as django_settings
from django.views.static import serve

from . import legacy, simple, advanced, advanced, subscriptions
from .advanced import auth, lists, sync, updates, episode, settings
from mygpo.users import converters
from mygpo.usersettings.converters import ScopeConverter

register_converter(converters.ClientUIDConverter, 'client-uid')
register_converter(converters.UsernameConverter, 'username')
register_converter(ScopeConverter, 'scope')


urlpatterns = [
    path('api/' + django_settings.API_DEFINITION_FILE_NAME,
        serve,
        kwargs={
            'path': django_settings.API_DEFINITION_FILE_NAME,
            'document_root': django_settings.API_DEFINITION_FILE_PATH
            }
        ),

    path('upload',
        legacy.upload),

    path('getlist',
        legacy.getlist),

    path('toplist.opml',
        simple.toplist,
        kwargs={'count': 50, 'format': 'opml'}),

    path('subscriptions/<username:username>/'
         '<client-uid:device_uid>.<str:format>',
        simple.subscriptions),

    path('subscriptions/<username:username>.<str:format>',
        simple.all_subscriptions,
        name='api-all-subscriptions'),

    path('toplist/<int:count>.<str:format>',
        simple.toplist,
        name='toplist-opml'),

    path('search.<str:format>',
        simple.search),

    path('suggestions/<int:count>.<str:format>',
        simple.suggestions,
        name='suggestions-opml'),

    path('toplist.<str:format>',
        simple.toplist,
        kwargs={'count': 50}),

    path('gpodder-examples.<str:format>',
        simple.example_podcasts,
        name='example-opml'),

    path('api/<int:version>/subscriptions/<username:username>/'
        '<client-uid:device_uid>.json',
        subscriptions.SubscriptionsAPI.as_view(),
        name='subscriptions-api'),

    path('api/<int:version>/episodes/<username:username>.json',
        advanced.episodes),

    path('api/<int:version>/devices/<username:username>/'
        '<client-uid:device_uid>.json',
        advanced.device),

    path('api/<int:version>/devices/<username:username>.json',
        advanced.devices),

    path('api/2/auth/<username:username>/login.json',
        auth.login),

    path('api/2/auth/<username:username>/logout.json',
        auth.logout),

    path('api/2/tags/<int:count>.json',
        advanced.directory.top_tags),

    path('api/2/tag/<str:tag>/<int:count>.json',
        advanced.directory.tag_podcasts),

    path('api/2/data/podcast.json',
        advanced.directory.podcast_info),

    path('api/2/data/episode.json',
        advanced.directory.episode_info,
        name='api-episode-info'),

    path('api/2/chapters/<username:username>.json',
        episode.ChaptersAPI.as_view()),

    path('api/2/updates/<username:username>/<client-uid:device_uid>.json',
        updates.DeviceUpdates.as_view()),

    path('api/2/settings/<username:username>/<scope:scope>.json',
        settings.SettingsAPI.as_view(),
        name='settings-api'),

    path('api/2/favorites/<username:username>.json',
        advanced.favorites),

    path('api/2/lists/<username:username>/create.<str:format>',
        lists.create),

    path('api/2/lists/<username:username>.json',
        lists.get_lists),

    path('api/2/lists/<username:username>/list/<slug:slug>.<str:format>',
        lists.podcast_list,
        name='api-get-list'),

    path('api/2/sync-devices/<username:username>.json',
        sync.main),

]
