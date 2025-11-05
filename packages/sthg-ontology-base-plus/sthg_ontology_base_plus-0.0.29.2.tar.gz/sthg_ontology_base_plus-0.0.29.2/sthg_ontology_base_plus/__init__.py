# sthg_ontology_base_plus/__init__.py
# from sthg_ontology_base_plus import (
#     function, edit, delete, create,  # 来自 base_decorator
#     TGClient, BaseModel, QuerySet, JoinedQuerySet, OntologyNamespace, BaseRelation  # 来自 base_crud
# )
#
# from .utils.base_decorator import function, edit, delete, create  # 来自 base_decorator
# from .utils.base_crud import TGClient, BaseModel, QuerySet, JoinedQuerySet, OntologyNamespace, BaseRelation  # 来自 base_crud
# from .utils.registry import MODEL_REGISTRY, RELATION_REGISTRY
# # 导出所有旧模块的成员
# __all__ = ['TGClient', 'BaseModel', 'QuerySet', 'JoinedQuerySet', 'OntologyNamespace', 'BaseRelation',
#            'function', 'edit', 'delete', 'create', 'MODEL_REGISTRY', 'RELATION_REGISTRY']
#
# # 向后兼容：让整个旧模块可用
# import sys
# sys.modules['sthg_ontology_base'] = sys.modules[__name__]

from .utils.base_crud import BaseModel, OntologyNamespace

__all__ = [
    'BaseModel',
    'OntologyNamespace',
]