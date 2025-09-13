# -*- coding: utf-8 -*-
"""
Сервис для экспорта контактов
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from integration_utils.bitrix24.models.bitrix_user_token import BitrixUserToken
from ..contacts.contact_service import BitrixContactService
from ..companies.company_service import BitrixCompanyService

logger = logging.getLogger(__name__)


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