from django.utils import timezone
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models.notifications.in_app_notification import InAppNotification

class InAppNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InAppNotification
        fields = ['id', 'title', 'message', 'notification_type', 'reference_id', 
                  'is_read', 'created_at', 'read_at']
        read_only_fields = ['id', 'title', 'message', 'notification_type', 
                           'reference_id', 'created_at', 'read_at']


class InAppNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for in-app notifications
    """
    serializer_class = InAppNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's notifications"""
        return InAppNotification.objects.filter(user=self.request.user)
        
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all user's notifications as read"""
        notifications = self.get_queryset().filter(is_read=False)
        for notification in notifications:
            notification.mark_as_read()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=True, methods=['delete'])
    def delete(self, request, pk=None):
        """Delete a specific notification"""
        notification = self.get_object()
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=False, methods=['delete'])
    def delete_all(self, request):
        """Delete all notifications for the current user"""
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=False, methods=['delete'])
    def delete_read(self, request):
        """Delete all read notifications for the current user"""
        self.get_queryset().filter(is_read=True).delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 