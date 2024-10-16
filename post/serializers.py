from rest_framework import serializers

from post.models import Post, PostLike, PostComment, CommentLike
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "image")


class PostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    post_like_count = serializers.SerializerMethodField("get_post_like_count")
    comment_like_count = serializers.SerializerMethodField("get_comment_like_count")
    me_liked = serializers.SerializerMethodField("get_me_liked")

    class Meta:
        model = Post
        fields = (
            "id", "author", "caption", "created_time", "post_like_count", "comment_like_count", "me_liked"
        )

        extra_kwargs = {"image": {"required": False}}

    @staticmethod
    def get_post_like_count(obj: Post):
        return obj.likes.count()

    @staticmethod
    def get_comment_like_count(obj: Post):
        return obj.comments.count()

    def get_me_liked(self, obj: Post):
        request = self.context.get("request", None)
        if request is not None and request.user.is_authenticated:
            try:
                PostLike.objects.get(post=obj, author=request.user)
                return True
            except PostLike.DoesNotExist:
                return False
        return False


class PostCommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField("get_replies")
    me_liked = serializers.SerializerMethodField("get_me_liked")
    likes_count = serializers.SerializerMethodField("get_likes_count")

    class Meta:
        model = PostComment
        fields = (
            "id",
            "author",
            "comment",
            "created_time",
            "parent",
            "replies",
            "me_liked",
            "likes_count",
            "post",
        )

    def get_replies(self, obj: PostComment):
        if obj.child.exists():
            serializer = self.__class__(obj.child.all(), many=True, context=self.context)
            return serializer.data
        else:
            return None

    def get_me_liked(self, obj: PostComment):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.likes.filter(author=user).exists()
        else:
            return False

    @staticmethod
    def get_likes_count(obj: PostComment):
        return obj.likes.count()


class CommentLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = (
            "id", "author", "comment",
        )
        extra_kwargs = {"comment": {"required": False}}


class PostLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = PostLike
        fields = (
            "id", "author", "post"
        )
        extra_kwargs = {"post": {"required": False}}
