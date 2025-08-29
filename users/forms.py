from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django_countries.fields import CountryField

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="Нікнейм",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Введіть нікнейм'})
    )
    first_name = forms.CharField(
        label="Ім'я",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Введіть ім\'я'})
    )
    last_name = forms.CharField(
        label="Прізвище",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Введіть прізвище'})
    )
    email = forms.EmailField(
        label="Пошта",
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Введіть email'})
    )
    password1 = forms.CharField(
        label="Пароль",
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'})
    )
    password2 = forms.CharField(
        label="Повторення паролю",
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторіть пароль'})
    )



    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Користувач з такою поштою вже існує.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Користувач з таким нікнеймом вже існує.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Паролі не співпадають.")
        return cleaned_data
    
class ProfileSettingsForm(forms.ModelForm):
    avatar = forms.ImageField(
        label="Змінити аватар",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'avatar-input'})
    )
    status = forms.CharField(
        label="Статус",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ваш статус'})
    )
    bio = forms.CharField(
        label="BIO",
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'Коротка біографія', 'rows': 3})
    )
    birthday = forms.DateField(
        label="Дата народження",
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    new_email = forms.EmailField(
        label="Нова пошта",
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'Введіть нову пошту'})
    )
    current_email = forms.EmailField(
        label="Поточна пошта",
        required=False,
        disabled=True
    )
    country = CountryField(blank_label='(Виберіть країну)').formfield(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = [
            'avatar', 'first_name', 'last_name', 'current_email', 'new_email',
            'status', 'bio', 'birthday', 'country'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['current_email'].initial = self.instance.email
            if hasattr(self.instance, 'country'):
                self.fields['country'].initial = self.instance.country

    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email')
        if new_email and User.objects.filter(email=new_email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Користувач з такою поштою вже існує.")
        return new_email
