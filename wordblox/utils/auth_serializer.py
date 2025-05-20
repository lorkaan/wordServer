from utils.session_auth import verify_auth
from rest_framework import serializers

class AuthenticatedSerializer(serializers.ModelSerializer):

    def validate(self, data):
        request = self.context.get("request")
        if not request or not verify_auth(request):
            raise serializers.ValidationError("User must be authenticated")