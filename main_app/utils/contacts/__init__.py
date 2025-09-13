"""
Сервисы для работы с контактами в Битрикс24
"""

from .contact_service import BitrixContactService
from .contact_delete_service import ContactDeleteService

__all__ = ['BitrixContactService', 'ContactDeleteService']