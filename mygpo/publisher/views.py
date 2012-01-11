from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponseForbidden, Http404
from django.views.decorators.cache import cache_page
from django.core.urlresolvers import reverse

from mygpo.core.models import Podcast, PodcastGroup
from mygpo.core.proxy import proxy_object
from mygpo.publisher.auth import require_publisher, is_publisher
from mygpo.publisher.forms import SearchPodcastForm
from mygpo.publisher.utils import listener_data, episode_listener_data, check_publisher_permission, subscriber_data
from mygpo.web.heatmap import EpisodeHeatmap
from mygpo.web.views.episode import oldid_decorator, slug_id_decorator
from mygpo.web.views.podcast import \
         slug_id_decorator as podcast_slug_id_decorator, \
         oldid_decorator as podcast_oldid_decorator
from mygpo.web.utils import get_podcast_link_target
from django.contrib.sites.models import RequestSite
from mygpo.data.feeddownloader import update_podcasts
from mygpo.decorators import requires_token, allowed_methods
from mygpo.users.models import User


def home(request):
    if is_publisher(request.user):
        podcasts = Podcast.get_multi(request.user.published_objects)
        form = SearchPodcastForm()
        return render_to_response('publisher/home.html', {
            'podcasts': podcasts,
            'form': form,
            }, context_instance=RequestContext(request))

    else:
        site = RequestSite(request)
        return render_to_response('publisher/info.html', {
            'site': site
            }, context_instance=RequestContext(request))


@require_publisher
def search_podcast(request):
    form = SearchPodcastForm(request.POST)
    if form.is_valid():
        url = form.cleaned_data['url']

        podcast = Podcast.for_url(url)
        if not podcast:
            raise Http404

        url = get_podcast_link_target(podcast, 'podcast-publisher-detail')
    else:
        url = reverse('publisher')

    return HttpResponseRedirect(url)


@require_publisher
@allowed_methods(['GET', 'POST'])
def podcast(request, podcast):

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    timeline_data = listener_data([podcast])
    subscription_data = subscriber_data([podcast])[-20:]

    if podcast.group:
        group = PodcastGroup.get(podcast.group)
    else:
        group = None

#    if request.method == 'POST':
#        form = NonePodcastForm(request.POST, instance=p)
#        if form.is_valid():
#            form.save()

#    elif request.method == 'GET':
#        form = PodcastForm(instance=p)

    if 'new_token' in request.GET:
        request.user.create_new_token('publisher_update_token')
        request.user.save()

    update_token = request.user.publisher_update_token

    heatmap = EpisodeHeatmap(podcast.get_id())

    site = RequestSite(request)

    return render_to_response('publisher/podcast.html', {
        'site': site,
        'podcast': podcast,
        'group': group,
        'form': None,
        'timeline_data': timeline_data,
        'subscriber_data': subscription_data,
        'update_token': update_token,
        'heatmap': heatmap,
        }, context_instance=RequestContext(request))


@require_publisher
def group(request, group):

    podcasts = group.podcasts

    # users need to have publisher access for at least one of the group's podcasts
    if not any([check_publisher_permission(request.user, p) for p in podcasts]):
        return HttpResponseForbidden()

    timeline_data = listener_data(podcasts)
    subscription_data = list(subscriber_data(podcasts))[-20:]

    return render_to_response('publisher/group.html', {
        'group': group,
        'timeline_data': timeline_data,
        'subscriber_data': subscription_data,
        }, context_instance=RequestContext(request))


@require_publisher
def update_podcast(request, podcast):

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    update_podcasts( [podcast] )

    url = get_podcast_link_target(podcast, 'podcast-publisher-detail')
    return HttpResponseRedirect(url)


@requires_token(token_name='publisher_update_token')
def update_published_podcasts(request, username):
    user = User.get_user(username)
    if not user:
        raise Http404

    published_podcasts = Podcast.get_multi(user.published_objects)
    update_podcasts(published_podcasts)

    return HttpResponse('Updated:\n' + '\n'.join([p.url for p in published_podcasts]), mimetype='text/plain')


@require_publisher
def episodes(request, podcast):

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    episodes = podcast.get_episodes(descending=True)
    listeners = dict(podcast.episode_listener_counts())

    max_listeners = max(listeners.values() + [0])

    def annotate_episode(episode):
        listener_count = listeners.get(episode._id, None)
        return proxy_object(episode, listeners=listener_count)

    episodes = map(annotate_episode, episodes)

    return render_to_response('publisher/episodes.html', {
        'podcast': podcast,
        'episodes': episodes,
        'max_listeners': max_listeners
        }, context_instance=RequestContext(request))


@require_publisher
@allowed_methods(['GET', 'POST'])
def episode(request, episode):

    podcast = Podcast.get(episode.podcast)

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = None #EpisodeForm(request.POST, instance=e)
        #if form.is_valid():
        #    form.save()

    elif request.method == 'GET':
        form = None #EpisodeForm(instance=e)

    timeline_data = list(episode_listener_data(episode))

    heatmap = EpisodeHeatmap(episode.podcast, episode._id,
              duration=episode.duration)

    return render_to_response('publisher/episode.html', {
        'episode': episode,
        'podcast': podcast,
        'form': form,
        'timeline_data': timeline_data,
        'heatmap': heatmap,
        }, context_instance=RequestContext(request))


def link(request):
    current_site = RequestSite(request)
    return render_to_response('link.html', {
        'url': current_site
        }, context_instance=RequestContext(request))


def advertise(request):
    site = RequestSite(request)
    return render_to_response('publisher/advertise.html', {
        'site': site
    }, context_instance=RequestContext(request))


def group_slug_id_decorator(f):
    def _decorator(request, slug_id, *args, **kwargs):
        group = PodcastGroup.for_slug_id(slug_id)

        if podcast is None:
            raise Http404

        return f(request, group, *args, **kwargs)

    return _decorator


def group_oldid_decorator(f):
    def _decorator(request, pid, *args, **kwargs):
        try:
            pid = int(pid)
        except (TypeError, ValueError):
            raise Http404

        group = PodcastGroup.for_oldid(pid)

        if not podcast:
            raise Http404

        return f(request, group, *args, **kwargs)

    return _decorator



episode_oldid        = oldid_decorator(episode)
podcast_oldid        = podcast_oldid_decorator(podcast)
update_podcast_oldid = podcast_oldid_decorator(update_podcast)
episodes_oldid       = podcast_oldid_decorator(episodes)
group_oldid          = group_oldid_decorator(group)

episode_slug_id        = slug_id_decorator(episode)
podcast_slug_id        = podcast_slug_id_decorator(podcast)
episodes_slug_id       = podcast_slug_id_decorator(episodes)
update_podcast_slug_id = podcast_slug_id_decorator(update_podcast)
group_slug_id          = group_slug_id_decorator(group)
