from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from accounts.models import User


class Agent(models.Model):
    class AgentField(models.TextChoices):
        TECHNOLOGY = "Technology", "Technology"
        HEALTH = "Health", "Health"
        FINANCE = "Finance", "Finance"
        EDUCATION = "Education", "Education"
        ENTERTAINMENT = "Entertainment", "Entertainment"
        TRAVEL = "Travel", "Travel"
        SPORTS = "Sports", "Sports"
        FOOD = "Food", "Food"
        LIFESTYLE = "Lifestyle", "Lifestyle"
        FASHION = "Fashion", "Fashion"
        ART = "Art", "Art"
        MUSIC = "Music", "Music"
        GAMING = "Gaming", "Gaming"
        ENVIRONMENT = "Environment", "Environment"
        POLITICS = "Politics", "Politics"
        SCIENCE = "Science", "Science"
        HISTORY = "History", "History"
        CULTURE = "Culture", "Culture"
        AUTOMOTIVE = "Automotive", "Automotive"

    class AgentStyle(models.TextChoices):
        GENERALIST = "Generalist", "Generalist"
        PROFESSIONAL = "Professional", "Professional"
        JOURNALIST = "Journalist", "Journalist"
        INFLUENCER = "Influencer", "Influencer"

    name = models.CharField(max_length=100)
    field = models.CharField(max_length=50, choices=AgentField.choices)
    sub_field = models.CharField(max_length=50)
    agent_style = models.CharField(max_length=20, choices=AgentStyle.choices, default=AgentStyle.ENTHUSIAST)
    description = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    avatar_image = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete="cascade", null= True)

    def __str__(self):
        return self.name

    def get_avatar(self):
        """
        Return URL for frontend. Prioritize uploaded image if exists, else fallback to URL.
        """
        if self.avatar_image:
            return self.avatar_image.url
        return self.avatar_url


class Post(models.Model):
    class PostCategory(models.TextChoices):
        TECHNOLOGY = "Technology", "Technology"
        HEALTH = "Health", "Health"
        FINANCE = "Finance", "Finance"
        EDUCATION = "Education", "Education"
        ENTERTAINMENT = "Entertainment", "Entertainment"
        TRAVEL = "Travel", "Travel"
        SPORTS = "Sports", "Sports"
        FOOD = "Food", "Food"
        LIFESTYLE = "Lifestyle", "Lifestyle"
        FASHION = "Fashion", "Fashion"
        ART = "Art", "Art"
        MUSIC = "Music", "Music"
        GAMING = "Gaming", "Gaming"
        ENVIRONMENT = "Environment", "Environment"
        POLITICS = "Politics", "Politics"
        SCIENCE = "Science", "Science"
        HISTORY = "History", "History"
        CULTURE = "Culture", "Culture"
        AUTOMOTIVE = "Automotive", "Automotive"

    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, related_name="posts")
    title = models.CharField(blank=False, max_length=50)
    text_content = models.TextField(blank=True)
    field = models.CharField(max_length=50, choices=PostCategory.choices)
    sub_field = models.CharField(blank=False, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="post_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class PostLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="liked_posts")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")


class Story(models.Model):
    class StoryType(models.TextChoices):
        IMAGE = "IMG", "image"
        TEXT = "TXT", "text"
        QUOTE = "QOT", "quote"

    content = models.TextField(blank=False)
    type = models.CharField(
        max_length=3,
        choices=StoryType.choices,
        default=StoryType.TEXT,
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.PositiveIntegerField()
    target = GenericForeignKey('target_content_type', 'target_object_id')
    follow_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'target_content_type', 'target_object_id'],
                name='unique_follow_per_target'
            )
        ]

    def __str__(self):
        return f"{self.follower} → {self.target_content_type.model}:{self.target_object_id}"


class ChatMessage(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'TEXT', 'Text'
        IMAGE_BASE64 = 'IMG64', 'Image (base64)'

    sender_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+')
    sender_object_id = models.PositiveIntegerField()
    sender = GenericForeignKey('sender_content_type', 'sender_object_id')

    receiver_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+')
    receiver_object_id = models.PositiveIntegerField()
    receiver = GenericForeignKey('receiver_content_type', 'receiver_object_id')

    type = models.CharField(max_length=5, choices=MessageType.choices, default=MessageType.TEXT)
    data = models.TextField(blank=False)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['sender_content_type', 'sender_object_id']),
            models.Index(fields=['receiver_content_type', 'receiver_object_id']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.type == self.MessageType.TEXT and not self.text:
            raise ValidationError('text is required for TEXT messages')
        if self.type == self.MessageType.IMAGE_BASE64 and not self.image_base64:
            raise ValidationError('image_base64 is required for IMG64 messages')


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    sender_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+')
    sender_object_id = models.PositiveIntegerField()
    sender = GenericForeignKey('sender_content_type', 'sender_object_id')

    receiver_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+')
    receiver_object_id = models.PositiveIntegerField()
    receiver = GenericForeignKey('receiver_content_type', 'receiver_object_id')

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "sender_content_type", "sender_object_id", "receiver_content_type", "receiver_object_id")
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['post']),
        ]
