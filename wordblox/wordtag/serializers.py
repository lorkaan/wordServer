from .models import Tag, Word, Domain
from utils.auth_serializer import AuthenticatedSerializer

class WordSerializer(AuthenticatedSerializer):
    class Meta:
        model = Word
        fields = ['id', 'text', 'details']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance: # will not exist on creation
            self.fields['text'].ready_only = True

class TagSerializer(AuthenticatedSerializer):
    words = WordSerializer(many=True, read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'text', 'words']

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