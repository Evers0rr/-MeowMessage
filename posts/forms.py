from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    title = forms.CharField(
        label="Заголовок",
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Введіть заголовок', 'class': 'form-control'})
    )
    content = forms.CharField(
        label="Текст поста",
        widget=forms.Textarea(attrs={'placeholder': 'Введіть текст поста', 'rows': 5, 'class': 'form-control'})
    )
    privacy_status = forms.ChoiceField(
        choices=Post.privacy_choices,
        label="Статус приватності",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    image = forms.ImageField(
        label="Зображення",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'privacy_status']

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise forms.ValidationError("Заголовок не може бути порожнім.")
        return title

    def clean_content(self):
        content = self.cleaned_data['content'].strip()
        if not content:
            raise forms.ValidationError("Текст поста не може бути порожнім.")
        return content

class GroupCommentForm(forms.ModelForm):
    content = forms.CharField(
        label="Коментар",
        max_length=500,
        widget=forms.Textarea(attrs={'placeholder': 'Введіть коментар', 'rows': 3, 'class': 'form-control'})
    )

    class Meta:
        model = Comment
        fields = ['content', 'parent_comment'] 