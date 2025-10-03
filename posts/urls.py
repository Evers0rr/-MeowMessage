from django.urls import path
from .views import (
    HomeView,
    PostsListView,
    PostCreateView,
    PostDetailView,
    # PrivatePostDetailView,
    PostDeleteView,
    DeleteCommentView,
    CategoryPostsView,
    like_post,
    dislike_post,
    MyPostsView,
)

app_name = 'posts' 

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('all/', PostsListView.as_view(), name='posts-list'),
    path('my-posts/', MyPostsView.as_view(), name='my-posts'),
    path('create/', PostCreateView.as_view(), name='create-post'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('<int:pk>/delete/', PostDeleteView.as_view(), name='delete-post'),
    path('<int:post_pk>/comments/<int:comment_pk>/delete/', DeleteCommentView.as_view(), name='delete-comment'),
    path('category/<str:category>/', CategoryPostsView.as_view(), name='category-posts'),
    path('<int:pk>/like/', like_post, name="like-post"),
    path('<int:pk>/dislike/', dislike_post, name="dislike-post"),
    # path('posts/private/<uuid:token>/', PrivatePostDetailView.as_view(), name="post-detail-private")
]
