# -*- coding: utf-8 -*-
"""
Сервисы для работы с API Битрикс24
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from integration_utils.bitrix24.models.bitrix_user_token import BitrixUserToken

logger = logging.getLogger(__name__)


class BitrixContactService:
    """Сервис для работы с контактами в Битрикс24"""
    
    def __init__(self, user_token: BitrixUserToken):
        self.user_token = user_token
    
    def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создать контакт в Битрикс24
        
        Args:
            contact_data: Данные контакта
            
        Returns:
            Результат создания контакта
        """
        try:
            return self.user_token.call_api_method(
                'crm.contact.add',
                {'fields': contact_data}
            )
        except Exception as e:
            logger.error(f"Ошибка при создании контакта: {e}")
            raise
    
    def create_contacts_batch(self, contacts_data: List[Dict[str, Any]], chunk_size: int = 50) -> Dict[str, Any]:
        """
        Создать контакты пакетно с эффективной обработкой больших объемов
        
        Args:
            contacts_data: Список данных контактов
            chunk_size: Размер чанка для пакетной обработки (максимум 50)
            
        Returns:
            Результат пакетного создания
        """
        from integration_utils.bitrix24.functions.batch_api_call import _batch_api_call
        
        methods = []
        for i, contact_data in enumerate(contacts_data):
            methods.append((
                f'contact_{i}',
                'crm.contact.add',
                {'fields': contact_data}
            ))
        
        try:
            # Используем _batch_api_call напрямую для лучшего контроля
            return _batch_api_call(
                methods=methods,
                bitrix_user_token=self.user_token,
                function_calling_from_bitrix_user_token_think_before_use=True,
                chunk_size=min(chunk_size, 50),  # Максимум 50 запросов в батче
                halt=0,  # Продолжать при ошибках
                timeout=60
            )
        except Exception as e:
            logger.error(f"Ошибка при пакетном создании контактов: {e}")
            raise
    
    def get_contacts_list(self, filters: Optional[Dict[str, Any]] = None, 
                         select: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Получить список контактов
        
        Args:
            filters: Фильтры для выборки
            select: Поля для выборки
            
        Returns:
            Список контактов
        """
        if select is None:
            select = ['ID', 'NAME', 'SECOND_NAME', 'LAST_NAME', 'PHONE', 'EMAIL', 'COMPANY_ID', 'DATE_CREATE']
        
        params = {
            'select': select,
            'order': {'DATE_CREATE': 'DESC'}
        }
        
        if filters:
            params['filter'] = filters
        
        try:
            return self.user_token.call_api_method('crm.contact.list', params)
        except Exception as e:
            logger.error(f"Ошибка при получении списка контактов: {e}")
            raise
    
    def add_company_to_contact(self, contact_id: int, company_id: int, is_primary: bool = True) -> Dict[str, Any]:
        """
        Добавить компанию к контакту
        
        Args:
            contact_id: ID контакта
            company_id: ID компании
            is_primary: Является ли компания основной
            
        Returns:
            Результат добавления компании
        """
        try:
            return self.user_token.call_api_method(
                'crm.contact.company.add',
                {
                    'id': contact_id,
                    'fields': {
                        'COMPANY_ID': company_id,
                        'IS_PRIMARY': 'Y' if is_primary else 'N'
                    }
                }
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении компании к контакту: {e}")
            raise


class BitrixCompanyService:
    """Сервис для работы с компаниями в Битрикс24"""
    
    def __init__(self, user_token: BitrixUserToken):
        self.user_token = user_token
    
    def get_companies_list(self, filters: Optional[Dict[str, Any]] = None,
                          select: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Получить список компаний
        
        Args:
            filters: Фильтры для выборки
            select: Поля для выборки
            
        Returns:
            Список компаний
        """
        if select is None:
            select = ['ID', 'TITLE', 'COMPANY_TYPE', 'INDUSTRY', 'REVENUE', 'CURRENCY_ID']
        
        params = {
            'select': select,
            'order': {'TITLE': 'ASC'}
        }
        
        if filters:
            params['filter'] = filters
        
        try:
            return self.user_token.call_api_method('crm.company.list', params)
        except Exception as e:
            logger.error(f"Ошибка при получении списка компаний: {e}")
            raise
    
    def get_companies_batch(self, company_names: List[str], chunk_size: int = 50) -> Dict[str, Any]:
        """
        Получить компании по названиям пакетно с эффективной обработкой
        
        Args:
            company_names: Список названий компаний
            chunk_size: Размер чанка для пакетной обработки
            
        Returns:
            Результат пакетного получения компаний
        """
        from integration_utils.bitrix24.functions.batch_api_call import _batch_api_call
        
        methods = []
        for i, company_name in enumerate(company_names):
            methods.append((
                f'company_{i}',
                'crm.company.list',
                {
                    'filter': {'TITLE': company_name},
                    'select': ['ID', 'TITLE']
                }
            ))
        
        try:
            return _batch_api_call(
                methods=methods,
                bitrix_user_token=self.user_token,
                function_calling_from_bitrix_user_token_think_before_use=True,
                chunk_size=min(chunk_size, 50),
                halt=0,
                timeout=60
            )
        except Exception as e:
            logger.error(f"Ошибка при пакетном получении компаний: {e}")
            raise


class ContactImportService:
    """Сервис для импорта контактов с оптимизацией для больших объемов"""
    
    def __init__(self, user_token: BitrixUserToken):
        self.user_token = user_token
        self.contact_service = BitrixContactService(user_token)
        self.company_service = BitrixCompanyService(user_token)
        self.chunk_size = 50  # Оптимальный размер чанка для Битрикс24
    
    def import_contacts_from_data(self, contacts_data: List[Dict[str, Any]], 
                                progress_callback=None) -> Dict[str, Any]:
        """
        Импортировать контакты из данных с оптимизацией для больших объемов
        
        Args:
            contacts_data: Список данных контактов
            progress_callback: Функция для отслеживания прогресса
            
        Returns:
            Результат импорта
        """
        result = {
            'total': len(contacts_data),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        if not contacts_data:
            return result
        
        # Шаг 1: Подготавливаем данные контактов
        contacts_to_create = []
        company_names = set()
        
        for i, contact_data in enumerate(contacts_data):
            contact_fields = self._prepare_contact_fields(contact_data)
            contacts_to_create.append(contact_fields)
            
            # Собираем уникальные названия компаний
            company_name = contact_data.get('компания', '').strip()
            if company_name:
                company_names.add(company_name)
        
        # Шаг 2: Создаем контакты чанками для эффективности
        created_contacts = []
        total_chunks = (len(contacts_to_create) + self.chunk_size - 1) // self.chunk_size
        
        for chunk_idx in range(0, len(contacts_to_create), self.chunk_size):
            chunk = contacts_to_create[chunk_idx:chunk_idx + self.chunk_size]
            chunk_contacts_data = contacts_data[chunk_idx:chunk_idx + self.chunk_size]
            
            try:
                # Создаем контакты в текущем чанке
                batch_result = self.contact_service.create_contacts_batch(
                    chunk, 
                    chunk_size=self.chunk_size
                )
                
                # Обрабатываем результаты чанка
                for key, response in batch_result.items():
                    contact_index = chunk_idx + int(key.split('_')[1])
                    if response['error'] is None and response['result']:
                        contact_id = response['result']
                        created_contacts.append({
                            'id': contact_id,
                            'data': chunk_contacts_data[int(key.split('_')[1])]
                        })
                        result['success'] += 1
                    else:
                        result['failed'] += 1
                        error_msg = self._extract_error_message(response.get('error'))
                        result['errors'].append(
                            f"Не удалось импортировать контакт номер {contact_index + 1}: {error_msg}"
                        )
                
                # Уведомляем о прогрессе
                if progress_callback:
                    progress = min(100, int((chunk_idx + self.chunk_size) / len(contacts_to_create) * 50))
                    progress_callback(progress, f"Создано контактов: {result['success']}")
                
            except Exception as e:
                logger.error(f"Ошибка при создании чанка контактов {chunk_idx}-{chunk_idx + self.chunk_size}: {e}")
                # Помечаем все контакты в чанке как неудачные
                for i in range(len(chunk)):
                    result['failed'] += 1
                    result['errors'].append(
                        f"Не удалось импортировать контакт номер {chunk_idx + i + 1}: {str(e)}"
                    )
        
        # Шаг 3: Получаем компании пакетно (если есть)
        if company_names and created_contacts:
            try:
                companies_batch = self.company_service.get_companies_batch(
                    list(company_names), 
                    chunk_size=self.chunk_size
                )
                
                # Создаем словарь название -> ID компании
                company_name_to_id = {}
                for key, response in companies_batch.items():
                    if response['error'] is None and response['result']:
                        companies = response['result']
                        if companies:
                            company_name_to_id[companies[0]['TITLE']] = companies[0]['ID']
                
                # Шаг 4: Привязываем компании к контактам пакетно
                self._link_companies_to_contacts(created_contacts, company_name_to_id, result)
                
                if progress_callback:
                    progress_callback(100, f"Импорт завершен. Успешно: {result['success']}, Ошибок: {result['failed']}")
                
            except Exception as e:
                logger.error(f"Ошибка при привязке компаний: {e}")
                result['errors'].append(f"Ошибка при привязке компаний: {str(e)}")
        
        return result
    
    def _prepare_contact_fields(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовить поля контакта для API"""
        contact_fields = {
            'NAME': contact_data.get('имя', '').strip(),
            'SECOND_NAME': contact_data.get('отчество', '').strip(),
            'LAST_NAME': contact_data.get('фамилия', '').strip(),
        }
        
        # Добавляем телефон
        phone = contact_data.get('номер телефона', '').strip()
        if phone:
            contact_fields['PHONE'] = [{'VALUE': phone, 'VALUE_TYPE': 'WORK'}]
        
        # Добавляем email
        email = contact_data.get('почта', '').strip()
        if email:
            contact_fields['EMAIL'] = [{'VALUE': email, 'VALUE_TYPE': 'WORK'}]
        
        return contact_fields
    
    def _extract_error_message(self, error) -> str:
        """Извлечь сообщение об ошибке из ответа API"""
        if isinstance(error, dict):
            return error.get('error_description', str(error))
        return str(error) if error else 'Unknown error'
    
    def _link_companies_to_contacts(self, created_contacts: List[Dict], 
                                  company_name_to_id: Dict[str, str], 
                                  result: Dict[str, Any]) -> None:
        """Привязать компании к контактам пакетно"""
        from integration_utils.bitrix24.functions.batch_api_call import _batch_api_call
        
        # Группируем контакты по компаниям для пакетной обработки
        company_links = []
        for contact in created_contacts:
            company_name = contact['data'].get('компания', '').strip()
            if company_name and company_name in company_name_to_id:
                company_links.append({
                    'contact_id': contact['id'],
                    'company_id': company_name_to_id[company_name]
                })
        
        if not company_links:
            return
        
        # Создаем методы для пакетной привязки компаний
        methods = []
        for i, link in enumerate(company_links):
            methods.append((
                f'link_{i}',
                'crm.contact.company.add',
                {
                    'id': link['contact_id'],
                    'fields': {
                        'COMPANY_ID': link['company_id'],
                        'IS_PRIMARY': 'Y'
                    }
                }
            ))
        
        try:
            # Выполняем пакетную привязку
            batch_result = _batch_api_call(
                methods=methods,
                bitrix_user_token=self.user_token,
                function_calling_from_bitrix_user_token_think_before_use=True,
                chunk_size=self.chunk_size,
                halt=0,
                timeout=60
            )
            
            # Обрабатываем результаты привязки
            for key, response in batch_result.items():
                if response['error'] is not None:
                    link_index = int(key.split('_')[1])
                    contact_id = company_links[link_index]['contact_id']
                    error_msg = self._extract_error_message(response['error'])
                    result['errors'].append(
                        f"Не удалось привязать компанию к контакту {contact_id}: {error_msg}"
                    )
                    
        except Exception as e:
            logger.error(f"Ошибка при пакетной привязке компаний: {e}")
            result['errors'].append(f"Ошибка при привязке компаний: {str(e)}")


class ContactExportService:
    """Сервис для экспорта контактов"""
    
    def __init__(self, user_token: BitrixUserToken):
        self.user_token = user_token
        self.contact_service = BitrixContactService(user_token)
        self.company_service = BitrixCompanyService(user_token)
    
    def export_contacts_to_data(self, date_from: Optional[datetime] = None,
                               date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Экспортировать контакты в данные
        
        Args:
            date_from: Дата создания с
            date_to: Дата создания по
            
        Returns:
            Список данных контактов
        """
        # Формируем фильтры
        filters = {}
        if date_from:
            filters['>=DATE_CREATE'] = date_from.strftime('%Y-%m-%d %H:%M:%S')
        if date_to:
            filters['<=DATE_CREATE'] = date_to.strftime('%Y-%m-%d %H:%M:%S')
        
        # Получаем контакты
        contacts_response = self.contact_service.get_contacts_list(filters=filters)
        contacts = contacts_response.get('result', [])
        
        # Получаем все уникальные ID компаний
        company_ids = set()
        for contact in contacts:
            if contact.get('COMPANY_ID'):
                company_ids.add(contact['COMPANY_ID'])
        
        # Получаем информацию о компаниях
        companies_data = {}
        if company_ids:
            companies_response = self.company_service.get_companies_list(
                filters={'ID': list(company_ids)},
                select=['ID', 'TITLE']
            )
            companies = companies_response.get('result', [])
            companies_data = {company['ID']: company['TITLE'] for company in companies}
        
        # Формируем данные для экспорта
        export_data = []
        for contact in contacts:
            # Извлекаем телефон
            phone = ''
            if contact.get('PHONE') and len(contact['PHONE']) > 0:
                phone = contact['PHONE'][0].get('VALUE', '')
            
            # Извлекаем email
            email = ''
            if contact.get('EMAIL') and len(contact['EMAIL']) > 0:
                email = contact['EMAIL'][0].get('VALUE', '')
            
            # Получаем название компании
            company_name = ''
            if contact.get('COMPANY_ID') and contact['COMPANY_ID'] in companies_data:
                company_name = companies_data[contact['COMPANY_ID']]
            
            export_data.append({
                'имя': contact.get('NAME', ''),
                'фамилия': contact.get('LAST_NAME', ''),
                'отчество': contact.get('SECOND_NAME', ''),
                'номер телефона': phone,
                'почта': email,
                'компания': company_name
            })
        
        return export_data


class ContactDeleteService:
    """Сервис для удаления контактов"""
    
    def __init__(self, user_token: BitrixUserToken):
        self.user_token = user_token
        self.contact_service = BitrixContactService(user_token)
    
    def delete_contact(self, contact_id: int) -> bool:
        """
        Удалить контакт по ID
        
        Args:
            contact_id: ID контакта
            
        Returns:
            True если удален успешно
        """
        try:
            result = self.user_token.call_api_method(
                'crm.contact.delete',
                {'id': contact_id}
            )
            return result.get('result', False)
        except Exception as e:
            logger.error(f"Ошибка при удалении контакта {contact_id}: {e}")
            return False
    
    def delete_all_contacts(self, progress_callback=None) -> Dict[str, Any]:
        """
        Удалить все контакты с оптимизацией для больших объемов
        
        Returns:
            Результат удаления
        """
        from integration_utils.bitrix24.functions.batch_api_call import _batch_api_call
        
        result = {
            'total': 0,
            'deleted': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Получаем все контакты
            contacts_response = self.contact_service.get_contacts_list(
                select=['ID']
            )
            contacts = contacts_response.get('result', [])
            result['total'] = len(contacts)
            
            if not contacts:
                return result
            
            # Удаляем контакты чанками для эффективности
            chunk_size = 50
            for chunk_idx in range(0, len(contacts), chunk_size):
                chunk = contacts[chunk_idx:chunk_idx + chunk_size]
                
                # Создаем методы для текущего чанка
                methods = []
                for i, contact in enumerate(chunk):
                    methods.append((
                        f'delete_{chunk_idx + i}',
                        'crm.contact.delete',
                        {'id': contact['ID']}
                    ))
                
                try:
                    # Выполняем пакетное удаление
                    batch_result = _batch_api_call(
                        methods=methods,
                        bitrix_user_token=self.user_token,
                        function_calling_from_bitrix_user_token_think_before_use=True,
                        chunk_size=chunk_size,
                        halt=0,
                        timeout=60
                    )
                    
                    # Обрабатываем результаты
                    for key, response in batch_result.items():
                        if response['error'] is None and response.get('result'):
                            result['deleted'] += 1
                        else:
                            result['failed'] += 1
                            contact_index = chunk_idx + int(key.split('_')[1])
                            contact_id = contacts[contact_index]['ID']
                            error_msg = self._extract_error_message(response.get('error'))
                            result['errors'].append(f"Не удалось удалить контакт ID {contact_id}: {error_msg}")
                    
                    # Уведомляем о прогрессе
                    if progress_callback:
                        progress = min(100, int((chunk_idx + chunk_size) / len(contacts) * 100))
                        progress_callback(progress, f"Удалено контактов: {result['deleted']}")
                    
                except Exception as e:
                    logger.error(f"Ошибка при удалении чанка {chunk_idx}-{chunk_idx + chunk_size}: {e}")
                    # Помечаем все контакты в чанке как неудачные
                    for contact in chunk:
                        result['failed'] += 1
                        result['errors'].append(f"Не удалось удалить контакт ID {contact['ID']}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Ошибка при удалении всех контактов: {e}")
            result['errors'].append(f"Общая ошибка удаления: {str(e)}")
        
        return result
    
    def _extract_error_message(self, error) -> str:
        """Извлечь сообщение об ошибке из ответа API"""
        if isinstance(error, dict):
            return error.get('error_description', str(error))
        return str(error) if error else 'Unknown error'
