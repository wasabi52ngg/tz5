from django.urls import path
from . import views

app_name = 'main_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('import/', views.import_contacts, name='import_contacts'),
    path('export/', views.export_contacts, name='export_contacts'),
    path('delete-all/', views.delete_all_contacts, name='delete_all_contacts'),
]
