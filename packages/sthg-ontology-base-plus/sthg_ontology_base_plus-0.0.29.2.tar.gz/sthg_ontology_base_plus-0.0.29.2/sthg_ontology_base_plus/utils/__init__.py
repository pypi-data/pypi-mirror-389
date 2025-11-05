"""
utils 模块兼容层
"""

# 直接导入新包的 utils 模块
from sthg_ontology_base_plus.utils import *

# 明确导入常用的类和变量
from sthg_ontology_base_plus.utils.base_crud import BaseModel, ObjectNamespace, TGClient, BaseModel, QuerySet, \
    JoinedQuerySet, OntologyNamespace, BaseRelation,BaseRelation,RelationMeta
from sthg_ontology_base_plus.utils.registry import MODEL_REGISTRY, RELATION_REGISTRY
from sthg_ontology_base_plus.utils.base_decorator import function, edit, delete, create
from sthg_ontology_base_plus.utils.snowflake_generator import SnowflakeIdGenerator

# 确保这些名称在模块中可用
BaseModel = BaseModel
OntologyNamespace = OntologyNamespace
MODEL_REGISTRY = MODEL_REGISTRY
RELATION_REGISTRY = RELATION_REGISTRY
BaseRelation = BaseRelation
RelationMeta = RelationMeta
function = function
edit = edit
delete = delete
create = create
SnowflakeIdGenerator = SnowflakeIdGenerator
QuerySet = QuerySet
JoinedQuerySet = JoinedQuerySet
TGClient = TGClient
ObjectNamespace = ObjectNamespace


__all__ = [
    'BaseModel',
    'OntologyNamespace',
    'MODEL_REGISTRY',
    'RELATION_REGISTRY',
    'BaseRelation',
    'RelationMeta',
    'function',
    'edit',
    'delete',
    'create',
    'SnowflakeIdGenerator',
    'QuerySet',
    'JoinedQuerySet',
    'TGClient',
    'ObjectNamespace'
]
