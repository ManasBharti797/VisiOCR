# visiocrs/serializers.py

from rest_framework import serializers

class OCRDataSerializer(serializers.Serializer):
    document_type = serializers.CharField(max_length=100)
    id_number = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    dob = serializers.CharField(max_length=10)



