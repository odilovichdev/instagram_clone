from django.urls import path

from users.views import CreateUserAPIView, VerifyAPIView, GetNewVerificationAPIView

urlpatterns = [
    path('signup/', CreateUserAPIView.as_view()),
    path('verify/', VerifyAPIView.as_view()),
    path('new-verify/', GetNewVerificationAPIView.as_view()),
]