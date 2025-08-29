from django.shortcuts import render
from django.views.generic import ListView
from .models import Post
# Create your views here.

class PostListView(ListView):
    model = Post
    template_name = 'posts/post_list.html'
    context_object_name = 'posts'
    paginate_by = 6
    ordering = ['-created_at']
