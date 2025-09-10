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
    
    def create_contacts_batch(self, contacts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Создать контакты пакетно
        
        Args:
            contacts_data: Список данных контактов
            
        Returns:
            Результат пакетного создания
        """
        methods = []
        for i, contact_data in enumerate(contacts_data):
            methods.append((
                f'contact_{i}',
                'crm.contact.add',
                {'fields': contact_data}
            ))
        
        try:
            return self.user_token.batch_api_call(methods)
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
    
    def get_companies_batch(self, company_names: List[str]) -> Dict[str, Any]:
        """
        Получить компании по названиям пакетно
        
        Args:
            company_names: Список названий компаний
            
        Returns:
            Результат пакетного получения компаний
        """
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
            return self.user_token.batch_api_call(methods)
        except Exception as e:
            logger.error(f"Ошибка при пакетном получении компаний: {e}")
            raise


class ContactImportService:
    """Сервис для импорта контактов"""
    
    def __init__(self, user_token: BitrixUserToken):
        self.user_token = user_token
        self.contact_service = BitrixContactService(user_token)
        self.company_service = BitrixCompanyService(user_token)
    
    def import_contacts_from_data(self, contacts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Импортировать контакты из данных
        
        Args:
            contacts_data: Список данных контактов
            
        Returns:
            Результат импорта
        """
        result = {
            'total': len(contacts_data),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        # Шаг 1: Создаем контакты без привязки к компаниям
        contacts_to_create = []
        company_names = set()
        
        for i, contact_data in enumerate(contacts_data):
            # Извлекаем данные контакта
            contact_fields = {
                'NAME': contact_data.get('имя', ''),
                'SECOND_NAME': contact_data.get('отчество', ''),
                'LAST_NAME': contact_data.get('фамилия', ''),
            }
            
            # Добавляем телефон
            phone = contact_data.get('номер телефона', '')
            if phone:
                contact_fields['PHONE'] = [{'VALUE': phone, 'VALUE_TYPE': 'WORK'}]
            
            # Добавляем email
            email = contact_data.get('почта', '')
            if email:
                contact_fields['EMAIL'] = [{'VALUE': email, 'VALUE_TYPE': 'WORK'}]
            
            contacts_to_create.append(contact_fields)
            
            # Собираем названия компаний
            company_name = contact_data.get('компания', '')
            if company_name:
                company_names.add(company_name)
        
        # Создаем контакты пакетно
        try:
            batch_result = self.contact_service.create_contacts_batch(contacts_to_create)
            
            # Обрабатываем результаты создания контактов
            created_contacts = []
            for key, response in batch_result.items():
                contact_index = int(key.split('_')[1])
                if response['error'] is None and response['result']:
                    contact_id = response['result']
                    created_contacts.append({
                        'id': contact_id,
                        'data': contacts_data[contact_index]
                    })
                    result['success'] += 1
                else:
                    result['failed'] += 1
                    error_msg = response.get('error', 'Unknown error')
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get('error_description', str(error_msg))
                    result['errors'].append(f"Не удалось импортировать контакт номер {contact_index + 1}: {error_msg}")
            
            # Шаг 2: Получаем компании пакетно
            if company_names:
                companies_batch = self.company_service.get_companies_batch(list(company_names))
                
                # Создаем словарь название -> ID компании
                company_name_to_id = {}
                for key, response in companies_batch.items():
                    if response['error'] is None and response['result']:
                        companies = response['result']
                        if companies:
                            company_name_to_id[companies[0]['TITLE']] = companies[0]['ID']
                
                # Шаг 3: Привязываем компании к контактам
                for contact in created_contacts:
                    company_name = contact['data'].get('компания', '')
                    if company_name and company_name in company_name_to_id:
                        try:
                            self.contact_service.add_company_to_contact(
                                contact['id'],
                                company_name_to_id[company_name]
                            )
                        except Exception as e:
                            logger.warning(f"Не удалось привязать компанию {company_name} к контакту {contact['id']}: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка при импорте контактов: {e}")
            result['errors'].append(f"Общая ошибка импорта: {str(e)}")
            result['failed'] = result['total']
            result['success'] = 0
        
        return result


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
    
    def delete_all_contacts(self) -> Dict[str, Any]:
        """
        Удалить все контакты
        
        Returns:
            Результат удаления
        """
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
            
            # Удаляем контакты пакетно
            methods = []
            for i, contact in enumerate(contacts):
                methods.append((
                    f'delete_{i}',
                    'crm.contact.delete',
                    {'id': contact['ID']}
                ))
            
            batch_result = self.user_token.batch_api_call(methods)
            
            # Обрабатываем результаты
            for key, response in batch_result.items():
                if response['error'] is None and response.get('result'):
                    result['deleted'] += 1
                else:
                    result['failed'] += 1
                    contact_index = int(key.split('_')[1])
                    contact_id = contacts[contact_index]['ID']
                    error_msg = response.get('error', 'Unknown error')
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get('error_description', str(error_msg))
                    result['errors'].append(f"Не удалось удалить контакт ID {contact_id}: {error_msg}")
            
        except Exception as e:
            logger.error(f"Ошибка при удалении всех контактов: {e}")
            result['errors'].append(f"Общая ошибка удаления: {str(e)}")
        
        return result
