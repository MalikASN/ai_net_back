# core/services.py
# core/services.py

from datetime import datetime, timedelta
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.contenttypes.models import ContentType
import requests

from .models import Agent, Post, PostImage, Story, Follow, ChatMessage, Comment, PostLike
from .serializers import AgentSerializer, PostSerializer, PostLikeSerializer, CommentSerializer

User = get_user_model()
User = get_user_model()

# -------------------------------------------------------------------------
# JWT Helper
# -------------------------------------------------------------------------
class TokenPair:
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token

def generate_tokens_for_user(user: User) -> TokenPair:
    refresh = RefreshToken.for_user(user)
    return TokenPair(str(refresh.access_token), str(refresh))


def refresh_access_token(refresh_token_str: str) -> TokenPair:
    try:
        refresh = RefreshToken(refresh_token_str)
        access_token = str(refresh.access_token)
        return TokenPair(access_token, str(refresh))
    except Exception as e:
        raise ValueError("Invalid or expired refresh token") from e

# -------------------------------------------------------------------------
# Auth
# -------------------------------------------------------------------------
def signin(username: str, password: str) -> TokenPair:
    user = authenticate(username=username, password=password)
    if not user:
        raise ValueError("Invalid username/password")
    return generate_tokens_for_user(user)


def signup(username: str, email: str, password: str) -> TokenPair:
    user = User.objects.create_user(username=username, email=email, password=password)
    return generate_tokens_for_user(user)


def social_signup(provider: str, token: str) -> TokenPair:
    """
    Simplified: call provider API to verify token and get user info
    Then create or get user and return JWT tokens
    """
    if provider.lower() == "google":
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = resp.json()
        email = data.get("email")
        username = data.get("name") or email.split("@")[0]
    else:
        raise NotImplementedError("Provider not supported")
    
    user, _ = User.objects.get_or_create(email=email, defaults={"username": username})
    return generate_tokens_for_user(user)


def logout(user: User):
    # In JWT, logout is client-side: remove tokens. You could blacklist refresh token if needed.
    pass


# -------------------------------------------------------------------------
# Agents
# -------------------------------------------------------------------------
def get_agents(page_size=20, page_index=1, field=None):
    qs = Agent.objects.all()
    if field:
        qs = qs.filter(field=field)
    paginator = Paginator(qs, page_size)
    page = paginator.get_page(page_index)
    return AgentSerializer(page, many=True).data


def add_agent(name: str, field: str, agent_type: str, description: str = "", avatar_url: str = ""):
    agent = Agent.objects.create(
        name=name,
        field=field,
        agent_type=agent_type,
        description=description,
        avatar_url=avatar_url
    )
    # Optionally, fetch avatar from external API if avatar_url is empty
    if not avatar_url:
        # Example: fetch placeholder avatar
        resp = requests.get("https://api.multiavatar.com/" + name + ".png")
        if resp.status_code == 200:
            agent.avatar_url = resp.url
            agent.save()
    return AgentSerializer(agent).data


# -------------------------------------------------------------------------
# Users
# -------------------------------------------------------------------------
def get_users(page_size=10, page_index=1):
    qs = User.objects.all()
    paginator = Paginator(qs, page_size)
    page = paginator.get_page(page_index)
    return [{"id": u.id, "username": u.username, "email": u.email} for u in page]


def get_user(user_id):
    return User.objects.filter(id=user_id).values("id", "username", "email").first()


def get_followers(user_id, page_size=10, page_index=1):
    qs = Follow.objects.filter(target_content_type=ContentType.objects.get_for_model(User),
                               target_object_id=user_id)
    paginator = Paginator(qs, page_size)
    page = paginator.get_page(page_index)
    return [{"follower_id": f.follower.id, "follow_date": f.follow_date} for f in page]


# -------------------------------------------------------------------------
# Chats
# -------------------------------------------------------------------------

def get_discussions(user_id):
    user_ct = ContentType.objects.get_for_model(User)
    
    # Get all chat messages where the user is the sender
    qs = ChatMessage.objects.filter(
        sender_content_type=user_ct,
        sender_object_id=user_id
    ).select_related('receiver_content_type')  # optional for efficiency

    # Use a set to avoid duplicates
    receivers = {}
    for c in qs:
        receiver_obj = c.receiver
        if receiver_obj:
            rid = receiver_obj.id
            if rid not in receivers:
                # Determine avatar for agents, empty for regular users
                avatar = getattr(receiver_obj, 'get_avatar', lambda: None)()
                receivers[rid] = {
                    "id": rid,
                    "name": getattr(receiver_obj, "username", getattr(receiver_obj, "name", "")),
                    "avatar": avatar
                }

    # Return list of unique receivers
    return list(receivers.values())

def get_discussion_chats(sender_id, receiver_id):
    user_ct = ContentType.objects.get_for_model(User)
    qs = ChatMessage.objects.filter(
        sender_content_type=user_ct, sender_object_id=sender_id,
        receiver_content_type=user_ct, receiver_object_id=receiver_id
    ) | ChatMessage.objects.filter(
        sender_content_type=user_ct, sender_object_id=receiver_id,
        receiver_content_type=user_ct, receiver_object_id=sender_id
    )
    return [{"id": c.id, "type": c.type, "text": c.text} for c in qs.order_by("created_at")]


# -------------------------------------------------------------------------
# Posts & Comments
# -------------------------------------------------------------------------
def get_posts(page_size=20, page_index=1, field=None, sort_date_up=False):
    qs = Post.objects.all()
    if field:
        qs = qs.filter(field=field)
    if sort_date_up:
        qs = qs.order_by("created_at")
    else:
        qs = qs.order_by("-created_at")
    paginator = Paginator(qs, page_size)
    page = paginator.get_page(page_index)
    return PostSerializer(page, many=True).data



def get_post_comments(post_id):
    qs = Comment.objects.filter(post_id=post_id).order_by("created_at")
    return CommentSerializer(qs, many=True).data
