# -*- coding: utf-8 -*-
"""
Сервис для работы с компаниями в Битрикс24
"""
import logging
from typing import List, Dict, Any, Optional

from integration_utils.bitrix24.models.bitrix_user_token import BitrixUserToken

logger = logging.getLogger(__name__)


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
    
    def get_companies_by_names(self, company_names: List[str]) -> Dict[str, str]:
        """
        Получить компании по названиям одним запросом
        
        Args:
            company_names: Список названий компаний
            
        Returns:
            Словарь {название_компании: ID_компании}
        """
        if not company_names:
            return {}
        
        try:
            response = self.get_companies_list(
                filters={'TITLE': company_names},
                select=['ID', 'TITLE']
            )
            
            companies = response.get('result', [])
            return {company['TITLE']: company['ID'] for company in companies}
            
        except Exception as e:
            logger.error(f"Ошибка при получении компаний по названиям: {e}")
            raise