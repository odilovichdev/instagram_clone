from django.urls import path

from users.views import CreateUserAPIView

urlpatterns = [
    path('signup/', CreateUserAPIView.as_view()),
]