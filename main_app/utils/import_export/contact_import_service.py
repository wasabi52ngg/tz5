# -*- coding: utf-8 -*-
"""
Сервис для импорта контактов с оптимизацией для больших объемов
"""
import logging
from typing import List, Dict, Any

from integration_utils.bitrix24.models.bitrix_user_token import BitrixUserToken
from ..contacts.contact_service import BitrixContactService
from ..companies.company_service import BitrixCompanyService

logger = logging.getLogger(__name__)


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
        
        for contact_data in contacts_data:
            contact_fields = self._prepare_contact_fields(contact_data)
            contacts_to_create.append(contact_fields)
            
            # Собираем уникальные названия компаний (проверяем оба варианта)
            company_name = contact_data.get('компания', '').strip() or contact_data.get('Компания', '').strip()
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
            company_name = contact['data'].get('компания', '').strip() or contact['data'].get('Компания', '').strip()
            if company_name and company_name in company_name_to_id:
                company_links.append({
                    'contact_id': contact['id'],
                    'company_id': company_name_to_id[company_name],
                    'company_name': company_name
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