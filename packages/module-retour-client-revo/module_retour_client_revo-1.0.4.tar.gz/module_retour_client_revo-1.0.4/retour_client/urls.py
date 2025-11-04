from django.urls import path

from retour_client.views import RetourClientView, PipelineRetourClientView, KanbanRetourClientView, \
    RetourClientItemView, ChangementStatutBugLink, FilteredRetourClientListView, ChangementStatutV2Link
from retour_client.views.retour_client import RefusValidationBugLink, ChangementTypeV1Link, ChangementTypeQuestionLink, \
    ChangementTypeBugLink, update_statut_kanban

app_name = 'retour_client'

urlpatterns = [
    path('retour-client/', RetourClientView.as_view(), name='retour_client_form'),
    path('pipeline-retours/', PipelineRetourClientView.as_view(), name='pipeline_retours'),
    path('kanban-retours/', KanbanRetourClientView.as_view(), name='kanban_retours'),
    path('item-retour/<int:pk>', RetourClientItemView.as_view(), name='item_retour'),
    path('changement-statut/<int:id_bug>', ChangementStatutBugLink.as_view(), name='changement-statut-bug'),
    path('refus-validation-bug/<int:id_bug>', RefusValidationBugLink.as_view(), name='refus-validation-bug'),
    path('filtered/', FilteredRetourClientListView.as_view(), name='filtered_list'),

    path('changement-statut-v2/<int:id_bug>', ChangementStatutV2Link.as_view(), name='changement-statut-v2'),
    path('changement-type-v1/<int:id_bug>', ChangementTypeV1Link.as_view(), name='changement-type-v1'),
    path('changement-type-question/<int:id_bug>', ChangementTypeQuestionLink.as_view(),
         name='changement-type-question'),
    path('changement-type-bug/<int:id_bug>', ChangementTypeBugLink.as_view(), name='changement-type-bug'),
    path("update-statut-kanban/", update_statut_kanban, name="update_statut_kanban"),
]
