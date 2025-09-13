# -*- coding: utf-8 -*-
"""
Сервис для удаления контактов
"""
import logging
from typing import Dict, Any

from integration_utils.bitrix24.models.bitrix_user_token import BitrixUserToken
from .contact_service import BitrixContactService

logger = logging.getLogger(__name__)


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