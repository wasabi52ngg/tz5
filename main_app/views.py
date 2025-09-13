import os
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from django.conf import settings

from .forms import ContactImportForm, ContactExportForm
from .utils import ContactImportService, ContactExportService, ContactDeleteService
from .file_handlers import FileProcessor, FileHandlerFactory

logger = logging.getLogger(__name__)


@main_auth(on_cookies=True)
def index(request):
    """Главная страница"""
    context = {
        'user': request.bitrix_user,
        'is_authenticated': True,
        'app_settings': settings.APP_SETTINGS,
        'supported_formats': FileHandlerFactory.get_supported_extensions()
    }
    
    return render(request, 'main_app/index.html', context)


@main_auth(on_cookies=True)
def import_contacts(request):
    """Страница импорта контактов"""
    if request.method == 'POST':
        form = ContactImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Читаем файл
                file = form.cleaned_data['file']
                file_content = file.read()
                file_extension = os.path.splitext(file.name)[1].lower()
                
                # Обрабатываем файл
                processor = FileProcessor(file_extension)
                contacts_data = processor.read_contacts(file_content)
                
                # Импортируем контакты
                import_service = ContactImportService(request.bitrix_user_token)
                result = import_service.import_contacts_from_data(contacts_data)
                
                # Показываем сообщения пользователю
                if result['success'] > 0:
                    messages.success(
                        request, 
                        f'Успешно импортировано {result["success"]} контактов из {result["total"]}'
                    )
                
                if result['failed'] > 0:
                    messages.warning(
                        request, 
                        f'Не удалось импортировать {result["failed"]} контактов'
                    )
                
                # Показываем ошибки
                for error in result['errors']:
                    messages.error(request, error)
                
                return redirect('main_app:import_contacts')
                
            except Exception as e:
                logger.error(f"Ошибка при импорте контактов: {e}")
                messages.error(request, f'Ошибка при импорте: {str(e)}')
    else:
        form = ContactImportForm()
    
    context = {
        'form': form,
        'supported_formats': FileHandlerFactory.get_supported_extensions()
    }
    
    return render(request, 'main_app/import_contacts.html', context)


@main_auth(on_cookies=True)
def export_contacts(request):
    """Страница экспорта контактов"""
    if request.method == 'POST':
        form = ContactExportForm(request.POST)
        if form.is_valid():
            try:
                # Получаем диапазон дат
                date_from, date_to = form.get_date_range()
                
                # Экспортируем контакты
                export_service = ContactExportService(request.bitrix_user_token)
                contacts_data = export_service.export_contacts_to_data(date_from, date_to)
                
                if not contacts_data:
                    messages.info(request, 'Контакты для экспорта не найдены')
                    return redirect('main_app:export_contacts')
                
                # Формируем файл
                format_type = form.cleaned_data['format']
                file_extension = f'.{format_type}'
                file_name = f'contacts_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}{file_extension}'
                
                processor = FileProcessor(file_extension)
                file_content = processor.write_contacts(contacts_data)
                
                # Возвращаем файл
                response = HttpResponse(
                    file_content,
                    content_type=processor.get_mime_type()
                )
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                
                return response
                
            except Exception as e:
                logger.error(f"Ошибка при экспорте контактов: {e}")
                messages.error(request, f'Ошибка при экспорте: {str(e)}')
    else:
        form = ContactExportForm()
    
    context = {
        'form': form,
        'supported_formats': FileHandlerFactory.get_supported_extensions()
    }
    
    return render(request, 'main_app/export_contacts.html', context)


@main_auth(on_cookies=True)
def delete_all_contacts(request):
    """Удалить все контакты"""
    if request.method == 'POST':
        try:
            delete_service = ContactDeleteService(request.bitrix_user_token)
            result = delete_service.delete_all_contacts()
            
            if result['deleted'] > 0:
                messages.success(
                    request, 
                    f'Успешно удалено {result["deleted"]} контактов из {result["total"]}'
                )
            
            if result['failed'] > 0:
                messages.warning(
                    request, 
                    f'Не удалось удалить {result["failed"]} контактов'
                )
            
            # Показываем ошибки
            for error in result['errors']:
                messages.error(request, error)
            
        except Exception as e:
            logger.error(f"Ошибка при удалении контактов: {e}")
            messages.error(request, f'Ошибка при удалении: {str(e)}')
    
    return redirect('main_app:index')
