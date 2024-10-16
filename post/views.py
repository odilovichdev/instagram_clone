from rest_framework import permissions, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from post.models import Post, PostComment, PostLike, CommentLike
from post.serializers import PostSerializer, PostCommentSerializer, PostLikeSerializer, CommentLikeSerializer
from shared.custom_pagination import CustomPagination


class PostListCreateAPIView(ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    def get_queryset(self):
        return Post.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def put(self, request, *args, **kwargs):
        post = self.get_object()
        serializer = self.serializer_class(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "success": True,
                "code": HTTP_200_OK,
                "message": "Post successfully update",
                "data": serializer.data,
            }
        )

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        post.delete()
        return Response(
            {
                "success": True,
                "code": HTTP_204_NO_CONTENT,
                "message": "Post successfully delete"
            }
        )


class PostCommentListCreateAPIView(ListCreateAPIView):
    serializer_class = PostCommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        post_id = self.kwargs['pk']
        serializer.save(author=self.request.user, post_id=post_id)

    def get_queryset(self):
        post_id = self.kwargs['pk']
        return PostComment.objects.filter(post__id=post_id)


class CommentListCreateAPIView(ListCreateAPIView):
    queryset = PostComment.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = PostCommentSerializer
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentRetrieveDestroyAPIView(RetrieveDestroyAPIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = PostCommentSerializer
    queryset = PostComment.objects.all()

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return Response(
            {
                "success": True,
                "code": HTTP_204_NO_CONTENT,
                "message": "Comment successfully delete"
            }
        )


class PostLikeAPIView(APIView):
    def post(self, request, pk):
        try:
            post_like = PostLike.objects.get(
                author=self.request.user,
                post_id=pk
            )
            post_like.delete()
            return Response(
                {
                    "success": True,
                    "message": "Postga bosilgan like muvaffaqiyatli o'chirildi"
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except PostLike.DoesNotExist:
            post_like = PostLike.objects.create(
                author=self.request.user,
                post_id=pk
            )
            serializer = PostLikeSerializer(post_like)
            return Response(
                {
                    "success": True,
                    "message": "Post ga like muvaffaqiyatli qo'shildi",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )


class CommentLikeAPIView(APIView):

    def post(self, request, pk):
        try:
            comment_like = CommentLike.objects.get(
                author=self.request.user,
                comment_id=pk
            )
            comment_like.delete()
            return Response(
                {
                    "success": True,
                    "message": "Commentga bosilgan like o'chirildi"
                }
            )
        except CommentLike.DoesNotExist:
            comment_like = CommentLike.objects.create(
                author=self.request.user,
                comment_id=pk
            )
            serializer = CommentLikeSerializer(comment_like)
            return Response(
                {
                    "success": True,
                    "message": "Commentga like bosildi",
                    "data": serializer.data
                }
            )
