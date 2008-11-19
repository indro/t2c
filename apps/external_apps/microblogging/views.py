from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from microblogging.utils import twitter_account_for_user, twitter_verify_credentials
from microblogging.pownce_utils import pownce_account_for_user, pownce_verify_credentials

from microblogging.models import Tweet, TweetInstance
from microblogging.forms import TweetForm

def personal(request, form_class=TweetForm,
        template_name="microblogging/personal.html", success_url=None):
    """
    just the tweets the current user is following
    """
    twitter_account = twitter_account_for_user(request.user)
    pownce_account  = pownce_account_for_user(request.user)

    if request.method == "POST":
        form = form_class(request.user, request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            form.save()
            if request.POST.get("pub2twitter", False):
                twitter_account.PostUpdate(text)
            if request.POST.get("pub2pownce", False):
                pownce_account.post_message('all', text)
            if success_url is None:
                success_url = reverse('microblogging.views.personal')
            return HttpResponseRedirect(success_url)
        reply = None
    else:
        reply = request.GET.get("reply", None)
        form = form_class()
        if reply:
            form.fields['text'].initial = u"@%s " % reply
    tweets = TweetInstance.objects.tweets_for(request.user).order_by("-sent")
    return render_to_response(template_name, {
        "form": form,
        "reply": reply,
        "tweets": tweets,
        "twitter_authorized": twitter_verify_credentials(twitter_account),
        "pownce_authorized": pownce_verify_credentials(pownce_account),
    }, context_instance=RequestContext(request))
personal = login_required(personal)
    
def public(request, template_name="microblogging/public.html"):
    """
    all the tweets
    """
    tweets = Tweet.objects.all().order_by("-sent")

    return render_to_response(template_name, {
        "tweets": tweets,
    }, context_instance=RequestContext(request))

def single(request, id, template_name="microblogging/single.html"):
    """
    A single tweet.
    """
    tweet = get_object_or_404(Tweet, id=id)
    return render_to_response(template_name, {
        "tweet": tweet,
    }, context_instance=RequestContext(request))


def _follow_list(request, username, template_name):
    # the only difference between followers/following views is template
    # this function captures the similarity
    
    other_user = get_object_or_404(User, username=username)
    
    return render_to_response(template_name, {
        "other_user": other_user,
    }, context_instance=RequestContext(request))

def followers(request, username, template_name="microblogging/followers.html"):
    """
    a list of users following the given user.
    """
    return _follow_list(request, username, template_name)


def following(request, username, template_name="microblogging/following.html"):
    """
    a list of users the given user is following.
    """
    return _follow_list(request, username, template_name)
