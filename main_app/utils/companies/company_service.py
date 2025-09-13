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