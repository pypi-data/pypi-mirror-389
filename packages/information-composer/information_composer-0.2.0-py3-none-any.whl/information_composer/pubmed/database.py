"""
PubMed 数据库持久化模块

使用 Pony ORM 实现 PubMed 文献数据的持久化存储。
支持完整的 CRUD 操作、批量处理、数据转换等功能。

核心组件：
- PubMedArticle: Pony ORM 实体模型，定义数据库表结构
- PubMedDatabase: 数据库管理类，提供高层次的业务接口
"""

from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional

from pony.orm import (
    Database,
    PrimaryKey,
    Required,
    count,
    db_session,
    select,
)
from pony.orm import (
    Optional as PonyOptional,
)


# 为了支持测试中的多实例，我们需要能够创建多个数据库实例
# 但是 Pony ORM 的限制是一旦 generate_mapping() 后就不能再次 bind
# 所以我们使用一个全局数据库实例，但允许更改数据库文件路径
db = Database()


class PubMedArticle(db.Entity):
    """
    PubMed 文献实体模型

    使用 Pony ORM 声明式定义，包含 40 个字段：
    - 35 个 processed_record 标准字段
    - 2 个扩展字段（abstract_zh, pdf_path）
    - 3 个数据库管理字段（created_at, updated_at, raw_data）
    """

    # 主键字段
    pmid = PrimaryKey(str)

    # 基础信息字段（3个）
    title = Required(str)
    abstract = PonyOptional(str)
    abstract_zh = PonyOptional(str)  # 摘要中文翻译（扩展字段）

    # 期刊信息字段（6个）
    journal = PonyOptional(str, index=True)
    journal_abbreviation = PonyOptional(str)
    journal_iso = PonyOptional(str)
    volume = PonyOptional(str)
    issue = PonyOptional(str)
    pagination = PonyOptional(str)

    # 日期字段（4个）
    pubdate = PonyOptional(str, index=True)
    create_date = PonyOptional(str)
    complete_date = PonyOptional(str)
    revision_date = PonyOptional(str)

    # 出版详情字段（3个）
    publication_types = PonyOptional(str)  # JSON 数组
    publication_status = PonyOptional(str)
    language = PonyOptional(str)

    # 作者和机构字段（3个）
    authors = PonyOptional(str)  # JSON 数组
    authors_full = PonyOptional(str)  # JSON 数组
    affiliations = PonyOptional(str)  # JSON 数组

    # 标识符字段（3个）
    doi = PonyOptional(str, index=True)
    pmcid = PonyOptional(str)
    article_id = PonyOptional(str)  # JSON 数组

    # 主题词字段（5个）
    mesh_terms = PonyOptional(str)  # JSON 数组
    mesh_qualifiers = PonyOptional(str)  # JSON 数组
    keywords = PonyOptional(str)  # JSON 数组
    chemicals = PonyOptional(str)  # JSON 数组
    chemical_names = PonyOptional(str)  # JSON 数组

    # 资助信息字段（2个）
    grants = PonyOptional(str)  # JSON 数组
    grant_agencies = PonyOptional(str)  # JSON 数组

    # 其他信息字段（6个）
    comments_corrections = PonyOptional(str)  # JSON 数组
    publication_country = PonyOptional(str)
    article_type = PonyOptional(str)  # JSON 数组
    citation_subset = PonyOptional(str)  # JSON 数组

    # 文件管理字段（1个）
    pdf_path = PonyOptional(str)  # PDF 文件路径（扩展字段）

    # 数据库管理字段（3个）
    raw_data = PonyOptional(str)  # 完整原始数据 JSON
    created_at = Required(datetime, index=True)
    updated_at = Required(datetime)


class PubMedDatabase:
    """
    PubMed 数据库管理类

    封装 Pony ORM 操作，提供高层次的业务接口：
    - 数据库初始化和连接管理
    - CRUD 操作
    - 批量操作
    - 数据转换和验证
    - 数据库维护
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，默认为 "data/pubmed/pubmed.db"
        """
        if db_path is None:
            db_path = "data/pubmed/pubmed.db"

        self.db_path = db_path

        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # 如果数据库尚未绑定，则进行绑定和映射
        if db.provider is None:
            # 绑定数据库
            db.bind(provider="sqlite", filename=db_path, create_db=True)
            # 生成表结构
            db.generate_mapping(create_tables=True)
        else:
            # 如果已经绑定，我们需要更新数据库文件路径
            # 注意：Pony ORM 不支持动态更改数据库路径
            # 在测试环境中，我们需要先 disconnect 再重新 bind
            db.disconnect()
            db.provider = None
            db.schema = None
            db.bind(provider="sqlite", filename=db_path, create_db=True)
            db.generate_mapping(create_tables=True)

    def close(self) -> None:
        """关闭数据库连接"""
        db.disconnect()

    @db_session
    def save_article(self, article: Dict[str, Any]) -> None:
        """
        保存单篇文献到数据库

        存在则更新，不存在则插入。自动处理 JSON 序列化和时间戳。

        Args:
            article: 文献信息字典（processed_record 格式）

        Raises:
            ValueError: 缺少必需字段
            RuntimeError: 数据库操作失败
        """
        if "pmid" not in article or "title" not in article:
            raise ValueError("Missing required fields: pmid and title")

        pmid = article["pmid"]
        existing = PubMedArticle.get(pmid=pmid)

        # 准备实体数据
        entity_data = self._prepare_entity_data(article)

        if existing:
            # 更新现有记录
            existing.set(**entity_data)
        else:
            # 创建新记录
            PubMedArticle(**entity_data)

    @db_session
    def save_articles_batch(self, articles: List[Dict[str, Any]]) -> int:
        """
        批量保存文献

        使用事务保证原子性，全部成功或全部失败。

        Args:
            articles: 文献信息列表

        Returns:
            成功保存的记录数
        """
        count = 0
        for article in articles:
            pmid = article.get("pmid")
            if not pmid:
                continue

            existing = PubMedArticle.get(pmid=pmid)
            entity_data = self._prepare_entity_data(article)

            if existing:
                existing.set(**entity_data)
            else:
                PubMedArticle(**entity_data)

            count += 1

        return count

    @db_session
    def get_article(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        根据 PMID 获取单篇文献

        Args:
            pmid: PubMed ID

        Returns:
            文献信息字典，不存在则返回 None
        """
        article = PubMedArticle.get(pmid=pmid)
        if not article:
            return None

        return self._entity_to_dict(article)

    @db_session
    def get_articles_batch(self, pmids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取多篇文献

        Args:
            pmids: PMID 列表

        Returns:
            以 PMID 为键的字典，值为文献信息
        """
        # 使用 query 方法代替生成器表达式以兼容 Python 3.13
        articles = []
        for pmid in pmids:
            article = PubMedArticle.get(pmid=pmid)
            if article:
                articles.append(article)
        return {a.pmid: self._entity_to_dict(a) for a in articles}

    @db_session
    def check_exists(self, pmid: str) -> bool:
        """
        检查指定 PMID 是否存在

        Args:
            pmid: PubMed ID

        Returns:
            存在返回 True，否则返回 False
        """
        return PubMedArticle.exists(pmid=pmid)

    @db_session
    def get_missing_pmids(self, pmids: List[str]) -> List[str]:
        """
        筛选出数据库中不存在的 PMID

        Args:
            pmids: 待检查的 PMID 列表

        Returns:
            数据库中不存在的 PMID 列表
        """
        # 使用 query 方法代替生成器表达式以兼容 Python 3.13
        existing = set()
        for pmid in pmids:
            article = PubMedArticle.get(pmid=pmid)
            if article:
                existing.add(pmid)
        return [pmid for pmid in pmids if pmid not in existing]

    @db_session
    def delete_article(self, pmid: str) -> bool:
        """
        删除指定 PMID 的文献

        Args:
            pmid: PubMed ID

        Returns:
            删除成功返回 True，记录不存在返回 False
        """
        article = PubMedArticle.get(pmid=pmid)
        if article:
            article.delete()
            return True
        return False

    @db_session
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            包含总记录数、最早和最新记录时间、数据库大小等信息的字典
        """
        # 使用 SQL 查询代替生成器表达式以兼容 Python 3.13
        total = PubMedArticle.select().count()

        stats = {
            "total_records": total,
            "database_size": self._get_db_file_size(),
        }

        if total > 0:
            # 使用 PonyORM 支持的排序语法获取最早和最新记录
            earliest_article = (
                PubMedArticle.select().order_by(PubMedArticle.created_at).first()
            )
            latest_article = (
                PubMedArticle.select().order_by(PubMedArticle.created_at.desc()).first()
            )
            if earliest_article:
                stats["earliest_record"] = earliest_article.created_at
            if latest_article:
                stats["latest_record"] = latest_article.created_at

        return stats

    def vacuum(self) -> None:
        """优化数据库，回收空间"""
        db.execute("VACUUM")

    def _prepare_entity_data(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备实体数据

        将 processed_record 格式转换为实体字段格式，
        包括 JSON 序列化和时间戳处理。

        Args:
            article: processed_record 格式的文献数据

        Returns:
            适用于 Pony ORM 实体的数据字典
        """
        now = datetime.now()

        # 列表类型字段需要序列化为 JSON
        list_fields = [
            "publication_types",
            "authors",
            "authors_full",
            "affiliations",
            "article_id",
            "mesh_terms",
            "mesh_qualifiers",
            "keywords",
            "chemicals",
            "chemical_names",
            "grants",
            "grant_agencies",
            "comments_corrections",
            "article_type",
            "citation_subset",
        ]

        entity_data = {
            "pmid": article["pmid"],
            "title": article.get("title", "N/A"),
            "updated_at": now,
        }

        # 如果是新记录，设置 created_at
        if not PubMedArticle.exists(pmid=article["pmid"]):
            entity_data["created_at"] = now

        # 处理文本字段
        text_fields = [
            "abstract",
            "abstract_zh",
            "journal",
            "journal_abbreviation",
            "journal_iso",
            "volume",
            "issue",
            "pagination",
            "pubdate",
            "create_date",
            "complete_date",
            "revision_date",
            "publication_status",
            "language",
            "doi",
            "pmcid",
            "publication_country",
            "pdf_path",
        ]

        for field in text_fields:
            if field in article:
                value = article[field]
                if value and value != "N/A":
                    entity_data[field] = str(value)

        # 处理列表字段（序列化为 JSON）
        for field in list_fields:
            if field in article:
                value = article[field]
                if isinstance(value, list):
                    entity_data[field] = json.dumps(value, ensure_ascii=False)
                elif value:
                    entity_data[field] = str(value)

        # 保存完整原始数据
        entity_data["raw_data"] = json.dumps(article, ensure_ascii=False)

        return entity_data

    def _entity_to_dict(self, entity: PubMedArticle) -> Dict[str, Any]:
        """
        将实体转换为字典

        包括 JSON 反序列化处理。

        Args:
            entity: PubMedArticle 实体实例

        Returns:
            文献信息字典
        """
        result = {
            "pmid": entity.pmid,
            "title": entity.title,
            "abstract": entity.abstract,
            "abstract_zh": entity.abstract_zh,
            "journal": entity.journal,
            "journal_abbreviation": entity.journal_abbreviation,
            "journal_iso": entity.journal_iso,
            "volume": entity.volume,
            "issue": entity.issue,
            "pagination": entity.pagination,
            "pubdate": entity.pubdate,
            "create_date": entity.create_date,
            "complete_date": entity.complete_date,
            "revision_date": entity.revision_date,
            "publication_status": entity.publication_status,
            "language": entity.language,
            "doi": entity.doi,
            "pmcid": entity.pmcid,
            "publication_country": entity.publication_country,
            "pdf_path": entity.pdf_path,
            "raw_data": entity.raw_data,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

        # 反序列化 JSON 字段
        list_fields = {
            "publication_types": entity.publication_types,
            "authors": entity.authors,
            "authors_full": entity.authors_full,
            "affiliations": entity.affiliations,
            "article_id": entity.article_id,
            "mesh_terms": entity.mesh_terms,
            "mesh_qualifiers": entity.mesh_qualifiers,
            "keywords": entity.keywords,
            "chemicals": entity.chemicals,
            "chemical_names": entity.chemical_names,
            "grants": entity.grants,
            "grant_agencies": entity.grant_agencies,
            "comments_corrections": entity.comments_corrections,
            "article_type": entity.article_type,
            "citation_subset": entity.citation_subset,
        }

        for field, value in list_fields.items():
            if value:
                try:
                    result[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[field] = []
            else:
                result[field] = []

        return result

    def _get_db_file_size(self) -> int:
        """
        获取数据库文件大小（字节）

        Returns:
            文件大小，如果文件不存在返回 0
        """
        if os.path.exists(self.db_path):
            return os.path.getsize(self.db_path)
        return 0
