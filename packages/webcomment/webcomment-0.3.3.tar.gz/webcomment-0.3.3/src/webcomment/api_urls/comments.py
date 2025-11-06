from django.urls import path
from ..endpoints.comments import (
    CommentListEndpoint,
    CommentItemEndpoint,
    CommentReplyEndpoint,
)

urlpatterns = [
    path("", CommentListEndpoint.as_view()),
    path("<int:pk>/", CommentItemEndpoint.as_view()),
    path("<int:pk>/reply/", CommentReplyEndpoint.as_view()),
]
