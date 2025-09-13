from django import forms
from django.utils import timezone
from datetime import timedelta

from .file_handlers import FileHandlerFactory


class ContactImportForm(forms.Form):
    """Форма для импорта контактов"""
    
    file = forms.FileField(
        label='Файл с контактами',
        help_text='Поддерживаемые форматы: CSV, XLSX',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx'
        })
    )
    
    def clean_file(self):
        """Валидация загружаемого файла"""
        file = self.cleaned_data.get('file')
        
        if not file:
            raise forms.ValidationError('Файл не выбран')
        
        # Проверяем размер файла (максимум 10 МБ)
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Размер файла не должен превышать 10 МБ')
        
        # Проверяем расширение файла
        file_name = file.name.lower()
        if not any(file_name.endswith(ext) for ext in FileHandlerFactory.get_supported_extensions()):
            supported_extensions = ', '.join(FileHandlerFactory.get_supported_extensions())
            raise forms.ValidationError(f'Неподдерживаемый формат файла. Поддерживаемые форматы: {supported_extensions}')
        
        return file


class ContactExportForm(forms.Form):
    """Форма для экспорта контактов"""
    
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel (XLSX)'),
    ]
    
    EXPORT_PERIOD_CHOICES = [
        ('all', 'Все контакты'),
        ('today', 'За сегодня'),
        ('week', 'За последнюю неделю'),
        ('month', 'За последний месяц'),
        ('custom', 'Выбрать период'),
    ]
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        label='Формат файла',
        initial='csv',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    export_period = forms.ChoiceField(
        choices=EXPORT_PERIOD_CHOICES,
        label='Период экспорта',
        initial='all',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    date_from = forms.DateTimeField(
        label='Дата создания с',
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    date_to = forms.DateTimeField(
        label='Дата создания по',
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Устанавливаем текущую дату и время по умолчанию
        now = timezone.now()
        self.fields['date_to'].initial = now
        
        # Добавляем JavaScript для управления видимостью полей дат
        self.fields['date_from'].widget.attrs.update({
            'style': 'display: none;'
        })
        self.fields['date_to'].widget.attrs.update({
            'style': 'display: none;'
        })
    
    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        export_period = cleaned_data.get('export_period')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        # Если выбран кастомный период, проверяем даты
        if export_period == 'custom':
            if not date_from:
                raise forms.ValidationError('Укажите дату начала периода')
            if not date_to:
                raise forms.ValidationError('Укажите дату окончания периода')
            if date_from >= date_to:
                raise forms.ValidationError('Дата начала должна быть меньше даты окончания')
        
        return cleaned_data
    
    def get_date_range(self):
        """Получить диапазон дат для экспорта"""
        export_period = self.cleaned_data.get('export_period')
        now = timezone.now()
        
        if export_period == 'today':
            return now.replace(hour=0, minute=0, second=0, microsecond=0), now
        elif export_period == 'week':
            return now - timedelta(days=7), now
        elif export_period == 'month':
            return now - timedelta(days=30), now
        elif export_period == 'custom':
            return self.cleaned_data.get('date_from'), self.cleaned_data.get('date_to')
        else:  # all
            return None, None
