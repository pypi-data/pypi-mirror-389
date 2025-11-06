from django.urls import path, include

urlpatterns = [
    path("comments/settings/", include("webcomment.api_urls.settings")),
    path("comments/", include("webcomment.api_urls.comments")),
    path("reactions/", include("webcomment.api_urls.reactions")),
    path("threads/", include("webcomment.api_urls.threads")),
]
