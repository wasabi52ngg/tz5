# -*- coding: utf-8 -*-
"""
Сервис для работы с контактами в Битрикс24
"""
import logging
from typing import List, Dict, Any, Optional

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