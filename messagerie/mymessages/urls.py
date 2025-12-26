
from django.urls import path

from mymessages.views import MessageCreateView, MessageDeleteView, MessageDetailView, MessageListView, MessageUpdateView, import_messages, bulk_delete_messages, export_stats_pdf


urlpatterns = [
    path('', MessageListView.as_view(), name='message_list'),
    path('create/', MessageCreateView.as_view(), name='message_create'),
    path('import/', import_messages, name='message_import'),
    path('export-stats/', export_stats_pdf, name='export_stats_pdf'),
    path('bulk-delete/', bulk_delete_messages, name='message_bulk_delete'),
    path('<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
    path('<int:pk>/update/', MessageUpdateView.as_view(), name='message_update'),
    path('<int:pk>/delete/', MessageDeleteView.as_view(), name='message_delete'),
]
