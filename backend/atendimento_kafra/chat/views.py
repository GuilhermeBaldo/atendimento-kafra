from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Chat, ChatMessage
from .serializers import ChatSerializer, ChatMessageSerializer


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        # Also delete related chat messages
        ChatMessage.objects.filter(chat_id=instance.id).delete()
        instance.delete()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({"chats": serializer.data})

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        chat = self.get_object()
        messages = ChatMessage.objects.filter(chat_id=chat.id).order_by('timestamp')
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)
