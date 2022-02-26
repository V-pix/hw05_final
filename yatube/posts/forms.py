from django import forms
from django.forms import ModelForm

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'group': 'Группа',
            'text': 'Текст поста',
        }
        help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

        labels = {
            'text': 'Текст комментария',
        }
