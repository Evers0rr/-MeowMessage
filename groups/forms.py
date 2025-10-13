from django import forms
from django.contrib.auth import get_user_model
from .models import (Group,
                    GroupCategory,
                    GroupPost,
                    GroupComment)


User = get_user_model()

class GroupCreateForm(forms.ModelForm):
    name = forms.CharField(
        label="Назва групи",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Введіть назву групи', 'class': 'form-control'})
    )
    description = forms.CharField(
        label="Опис групи",
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'Короткий опис', 'rows': 3, 'class': 'form-control'})
    )
    category = forms.ModelChoiceField(
        queryset=GroupCategory.objects.all(),
        label="Категорія",
        empty_label="Оберіть категорію",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    avatar = forms.ImageField(
        label="Аватар групи",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'avatar-input', 'accept': 'image/*'})
    )
    public_or_private = forms.ChoiceField(
        choices=Group.GROUP_PUBLIC_OR_PRIVATE,
        label="Тип групи",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Group
        fields = ['name', 'description', 'category', 'avatar', 'public_or_private']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError("Назва групи не може бути порожньою.")
        return name

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if not category:
            raise forms.ValidationError("Будь ласка, виберіть категорію для групи.")
        return category

class GroupPostForm(forms.ModelForm):
    title = forms.CharField(
        label="Заголовок",
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Введіть заголовок', 'class': 'form-control'})
    )
    content = forms.CharField(
        label="Текст поста",
        widget=forms.Textarea(attrs={'placeholder': 'Введіть текст поста', 'rows': 5, 'class': 'form-control'})
    )
    image = forms.ImageField(
        label="Зображення",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta:
        model = GroupPost
        fields = ['title', 'content', 'image']

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

class GroupInvitationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Нікнейм користувача",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть нікнейм користувача'}),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("Користувач з таким нікнеймом не знайдений.")
        return user

class GroupCommentForm(forms.ModelForm):
    content = forms.CharField(
        label="Коментар",
        max_length=500,
        widget=forms.Textarea(attrs={'placeholder': 'Введіть коментар', 'rows': 3, 'class': 'form-control'})
    )

    class Meta:
        model = GroupComment
        fields = ['content', 'parent'] 