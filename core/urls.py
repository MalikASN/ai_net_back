from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("auth/signup/", views.SignupView.as_view()),
    path("auth/signin/", views.SigninView.as_view()),

    # Agents
    path("agents/", views.AgentListView.as_view()),

    # Users
    path("users/", views.UserListView.as_view()),
    path("users/<int:user_id>/", views.UserDetailView.as_view()),
    path("users/<int:user_id>/followers/", views.UserFollowersView.as_view()),

    # Chats
    path("chats/<int:user_id>/", views.DiscussionListView.as_view()),
    path("chats/<int:sender_id>/<int:receiver_id>/", views.DiscussionChatView.as_view()),

    # Posts
    path("posts/", views.PostListView.as_view()),
    path("posts/<int:post_id>/comments/", views.PostCommentsView.as_view()),
]
