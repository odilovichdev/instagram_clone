from django.contrib import admin

from .models import PostLike, Post, PostComment, CommentLike


@admin.register(Post)
class PostModelAdmin(admin.ModelAdmin):
    list_display = 'id', 'author', 'caption', 'created_time'
    search_fields = "id", "author__username", 'caption'


@admin.register(PostComment)
class PostCommentModelAdmin(admin.ModelAdmin):
    list_display = "id", "author", "post", "created_time"
    search_fields = "id", "author__username", "comment"


@admin.register(PostLike)
class PostLikeModelAdmin(admin.ModelAdmin):
    list_display = "id", "author", "post", "created_time"
    search_fields = "id", "author__username"


@admin.register(CommentLike)
class CommentLikeModelAdmin(admin.ModelAdmin):
    list_display = "id", "author", "comment", "created_time"
    search_fields = "id", "author__username"
