from django import forms
from django.core.exceptions import ValidationError
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

        def clean_text(self):
            data = self.clean_data['text']
            if data == '':
                raise ValidationError
            return data

        labels = {
            'text': 'Текст комментария',
        }
