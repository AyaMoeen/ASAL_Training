from rest_framework import serializers
from .models import Post, Comment


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'body', 'status', 'author', 'publish', 'created', 'updated']
        read_only_fields = ['slug', 'author', 'publish', 'created', 'updated'] 

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['created', 'updated']

    def create(self, validated_data):
        return super().create(validated_data)