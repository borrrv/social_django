from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        text = self.cleaned_data['text']

        if text == 'None':
            raise forms.ValidationError('Заполните обязательное поле text')
        return text


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        text = self.cleaned_data['text']

        if text == 'None':
            raise forms.ValidationError(
                'Заполните обязательное поле комментария')
        return text
