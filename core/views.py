from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from . import services


# -------------------------------------------------------------------------
# Auth Controllers
# -------------------------------------------------------------------------
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        try:
            tokens = services.signup(
                username=data["username"],
                email=data["email"],
                password=data["password"]
            )
            return Response({"access": tokens.access_token, "refresh": tokens.refresh_token})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SigninView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        try:
            tokens = services.signin(data["username"], data["password"])
            return Response({"access": tokens.access_token, "refresh": tokens.refresh_token})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


# -------------------------------------------------------------------------
# Agent Controllers
# -------------------------------------------------------------------------
class AgentListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        category = request.query_params.get("category")
        page_size = request.query_params.get("page_size", 20)
        page_index = request.query_params.get("page_index", 1)
        agents = services.get_agents(page_size, page_index, category)
        return Response(agents)

    def post(self, request):
        data = request.data
        agent = services.add_agent(
            name=data["name"],
            category=data["category"],
            agent_type=data["agent_type"],
            description=data.get("description", ""),
            avatar_url=data.get("avatar_url", "")
        )
        return Response(agent, status=status.HTTP_201_CREATED)


# -------------------------------------------------------------------------
# User Controllers
# -------------------------------------------------------------------------
class UserListView(APIView):
    def get(self, request):
        page_size = request.query_params.get("page_size", 10)
        page_index = request.query_params.get("page_index", 1)
        users = services.get_users(page_size, page_index)
        return Response(users)


class UserDetailView(APIView):
    def get(self, request, user_id):
        user = services.get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(user)


class UserFollowersView(APIView):
    def get(self, request, user_id):
        page_size = request.query_params.get("page_size", 10)
        page_index = request.query_params.get("page_index", 1)
        followers = services.get_followers(user_id, page_size, page_index)
        return Response(followers)


# -------------------------------------------------------------------------
# Chat Controllers
# -------------------------------------------------------------------------
class DiscussionListView(APIView):
    def get(self, request, user_id):
        discussions = services.get_discussions(user_id)
        return Response(discussions)


class DiscussionChatView(APIView):
    def get(self, request, sender_id, receiver_id):
        chats = services.get_discussion_chats(sender_id, receiver_id)
        return Response(chats)


# -------------------------------------------------------------------------
# Post Controllers
# -------------------------------------------------------------------------
class PostListView(APIView):
    def get(self, request):
        category = request.query_params.get("field")
        page_size = request.query_params.get("page_size", 20)
        page_index = request.query_params.get("page_index", 1)
        sort_date_up = request.query_params.get("sort_date_up", "false").lower() == "true"
        posts = services.get_posts(page_size, page_index, category, sort_date_up)
        return Response(posts)


class PostCommentsView(APIView):
    def get(self, request, post_id):
        comments = services.get_post_comments(post_id)
        return Response(comments)


