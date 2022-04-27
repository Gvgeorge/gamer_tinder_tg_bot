from django.urls import re_path
from .views import CommandReceiveView


urlpatterns = [
    re_path(r'^(?P<bot_token>.+)/$', CommandReceiveView.as_view(), name='command'),
]
