from django.urls import path

from post.views import PostRetrieveUpdateDestroyAPIView, PostListCreateAPIView, PostCommentListCreateAPIView, \
    CommentListCreateAPIView, CommentRetrieveDestroyAPIView, \
    PostLikeAPIView, CommentLikeAPIView

urlpatterns = [
    path('list-create/', PostListCreateAPIView.as_view()),
    path('<uuid:pk>/', PostRetrieveUpdateDestroyAPIView.as_view()),
    path('<uuid:pk>/comments/', PostCommentListCreateAPIView.as_view()),
    path('comments/list-create/', CommentListCreateAPIView.as_view()),
    path('comments/<uuid:pk>/', CommentRetrieveDestroyAPIView.as_view()),
    path('<uuid:pk>/create-delete-like/', PostLikeAPIView.as_view()),
    path('comments/<uuid:pk>/create-delete-like/', CommentLikeAPIView.as_view()),

]
