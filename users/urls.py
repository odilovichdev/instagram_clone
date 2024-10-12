from django.urls import path

from users.views import CreateUserAPIView, VerifyAPIView, GetNewVerificationAPIView, ChangeUserInfoAPIView, \
    ChangeUserImageAPIView, LoginView, LoginRefreshView, LogOutView, ForgetPasswordView, ResetPasswordView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('login/refresh/', LoginRefreshView.as_view()),
    path('signup/', CreateUserAPIView.as_view()),
    path('logout/', LogOutView.as_view()),
    path('forgot-password/', ForgetPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    path('verify/', VerifyAPIView.as_view()),
    path('new-verify/', GetNewVerificationAPIView.as_view()),
    path('change-user/', ChangeUserInfoAPIView.as_view()),
    path('change-user-photo/', ChangeUserImageAPIView.as_view()),
]
