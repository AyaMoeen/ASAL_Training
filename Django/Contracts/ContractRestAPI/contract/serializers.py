from rest_framework import serializers
from .models import Profile, Contract, Job

class Profileserializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Profile
        fields = ['id', 'username', 'first_name', 'last_name', 'profession', 'type_profile', 'balance']

class ContractSerializer(serializers.ModelSerializer):
    client:serializers.StringRelatedField = serializers.StringRelatedField()
    contractor: serializers.StringRelatedField = serializers.StringRelatedField()
    
    class Meta:
        model = Contract
        fields = '__all__'
        
class JobSerializer(serializers.ModelSerializer):
    contract = ContractSerializer(read_only=True)
    
    class Meta:
        model = Job
        fields = '__all__'

    
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    profession = serializers.CharField(required=True)
    type_profile = serializers.ChoiceField(choices=Profile.ROLE_CHOICES, required=True)

    class Meta:
        model = Profile
        fields = ('username', 'password', 'email', 'profession', 'type_profile')

    def create(self, validated_data):
        validated_data.pop('profession')
        validated_data.pop('type_profile')

        user = Profile(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user
