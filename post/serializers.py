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

    def get_post_like_count(self, obj: Post):
        return obj.likes.count()

    def get_comment_like_count(self, obj: Post):
        return obj.comments.count()

    def get_me_liked(self, obj: Post):
        request = self.context.get("request", None)
        if request is not None and request.user.is_authenticated:
            try:
                like = PostLike.objects.get(post=obj, author=request.user)
                return True
            except PostLike.DoesNotExist:
                return False
        return False


# photo, username, comments, commentariyaga qoldirilgan izohlar, comentariyaga like bosilganini tekshirish,
# komentariyadagi like lar soni

class CommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField("get_replies")
    me_liked = serializers.SerializerMethodField("get_me_liked")
    likes_count = serializers.SerializerMethodField("get_likes_count")

    class Meta:
        model = PostComment
        fields = (
            "id", "author", "comment", "created_time", "parent", "replies", "me_liked", "likes_count"
        )

    def get_replies(self, obj: PostComment):
        if obj.child.exists():
            serializer = self.__class__(obj.child.all(), many=True, context=self.context)
            return serializer.data
        else:
            return None

    def get_me_liked(self, obj: PostComment):
        user = self.context.get("request", None)
        if user.is_authenticated:
            return obj.likes.filter(author=user).exists()
        else:
            return False
































