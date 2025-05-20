from .models import Tag, Word, Domain
from utils.auth_serializer import AuthenticatedSerializer
from rest_framework import serializers

class TagSerializer(AuthenticatedSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'text']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['text'].read_only = True

class WordSerializer(AuthenticatedSerializer):

    tag = TagSerializer(many=False, read_only=True)

    tag_id = serializers.PrimaryKeyRelatedField( # write
        queryset=Tag.objects.all(), source='tag', write_only=True
    )

    class Meta:
        model = Word
        fields = ['id', 'text', 'details', "tag", "tag_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance: # will not exist on creation
            self.fields['text'].ready_only = True


class DomainSerializer(AuthenticatedSerializer):
    """
        Serializer controlling domains in the current system. There should never be a write
        function from a user applied to this data.
    """

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Domain
        fields = ['id', 'url', 'tags']
        read_only_fields = ['id', 'url']