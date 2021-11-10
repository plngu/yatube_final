from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст', 'group': 'Группа', 'image': 'Картинка'}
        help_texts = {'text': 'Введите текст в это поле',
                      'group': 'Группа, к которой будет относиться пост',
                      'image': 'Ваша картинка к посту'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
        labels = {'text': 'Комментарий', }
        help_texts = {'text': 'Введите комментарий в это поле', }
