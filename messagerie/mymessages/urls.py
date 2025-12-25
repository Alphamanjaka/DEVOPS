
from django.urls import path

from mymessages.views import MessageCreateView, MessageDeleteView, MessageDetailView, MessageListView, MessageUpdateView


urlpatterns = [
    path('', MessageListView.as_view(), name='message_list'),
    path('create/', MessageCreateView.as_view(), name='message_create'),
    path('<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
    path('<int:pk>/update/', MessageUpdateView.as_view(), name='message_update'),
    path('<int:pk>/delete/', MessageDeleteView.as_view(), name='message_delete'),
]
