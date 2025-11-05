from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Filter, FieldCondition, MatchValue



class QdrantManager:
    """
    一个用于与 MySQL 数据库交互的通用工具包。
    提供了连接管理、增删改查 (CRUD) 操作和错误处理。
    """

    def __init__(self, host, port=6333):
        """
        初始化数据库管理器。
        :param host: 数据库主机名或 IP 地址。
        :param user: 数据库用户名。
        :param password: 数据库密码。
        :param database: 默认数据库名称 (可选，如果只连接到服务器而不指定数据库)。
        :param port: 数据库端口 (默认为 3306)。
        """
        self.host = host
        self.port = port
        # client = QdrantClient(":memory:")
        self.connection = QdrantClient(host=host, port=port)

    # --- CRUD 操作封装 ---

    def create_collection(self, collection_name: str, vector_dimension = 4):
        """
        创建表。
        注意： recreate_collection 会在集合存在时先删除再创建。如果你只想在集合不存在时创建，可以使用 create_collection。
        :param table_name: 要创建的表名。
        :param columns_definition: 列定义字符串，例如 "id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), age INT"。
        :return: True 如果成功，False 如果失败。
        """

        self.connection.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_dimension, distance=models.Distance.COSINE),
            # 可以选择配置 payload_m_config 来优化存储
            # payload_m_config=models.PayloadMConfig(
            #     enable_m=True,
            #     m=16, # 默认 16，越大索引构建越慢，但查询越快，内存占用越多
            # )
        )
        print('创建成功')
        return True
    
    def insert(self, collection_name, data):
        """
        插入单条数据。
        :param table_name: 表名。
        :param data: 字典，键为列名，值为要插入的数据。
                     例如: {'name': 'Alice', 'age': 30, 'email': 'alice@example.com',}
                     核心要有 vector 字段, vector=embedding,
                     payload={"text": doc["text"], "category": doc["category"]}  # 存储原始文本和任何其他元数据
        :return: 新插入记录的 ID (如果表有自增主键)，否则返回 None。
        """
        if not data:
            print("错误：插入数据为空。")
            return None
        points = [
                models.PointStruct(
                    **data
                )
            ]
        self.connection.upsert(
            collection_name=collection_name,
            wait=True,
            points=points
        )

        return True

    def bulk_insert(self, collection_name, data_list):
        """
        批量插入数据。
        :param table_name: 表名。
        :param columns: 列名列表，例如 ['name', 'age', 'email']。
        :param data_list: 包含元组或列表的列表，每个元组/列表代表一行数据。
                          例如: [('Alice', 30, 'alice@example.com'), ('Bob', 25, 'bob@example.com')]
        :return: 影响的行数，或 None。
        """

        if not data_list:
            print("错误：批量插入数据为空。")
            return None

        points_to_insert = [models.PointStruct(**data) for data in data_list]        

        self.connection.upsert(
            collection_name=collection_name,
            wait=True,  # 等待操作完成
            points=points_to_insert
        )
        print(f"Inserted/Upserted {len(points_to_insert)} points into '{collection_name}'.")


    def select_by_id(self,collection_name,ids =[1, 3] ):
            
        retrieved_points = self.connection.retrieve(
            collection_name=collection_name,
            ids=ids,
            with_vectors=True,  # 是否返回向量数据
            with_payload=True   # 是否返回负载数据
        )
        return retrieved_points
    
    def select_by_vector(self,query_vector = [0.12, 0.22, 0.32, 0.42],
                            collection_name = "",
                                limit = 2 # 返回最相似的 2 个点
                         ):
        """
        # 查找城市为 "New York" 的点中，与查询向量最相似的
        query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="city",
                        match=models.MatchValue(value="New York")
                    )
                ]
            ),

        # 查找年龄大于 30 的点
        query_filter=models.Filter(
                must=[
                    models.Range(
                        key="age",
                        gte=30 # Great than or Equal to 30
                    )
                ]
            ),
        """

        search_results = self.connection.search(
            query_vector=query_vector,
            collection_name=collection_name,
            query_filter = None,
            limit=limit,
            with_payload=True,
            with_vectors=False # 通常搜索结果不需要返回向量本身
        )
        return search_results
    
    def scroll(self,collection_name):

        """
        # 带过滤条件的滚动
        scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="city",
                        match=models.MatchValue(value="London")
                    )
                ]
            ),
        """
        # 获取集合中所有点 # 分页查询
        all_points = self.connection.scroll(
            collection_name=collection_name,
            scroll_filter = None,
            limit=10, # 每次请求返回的最大点数
            with_payload=True,
            with_vectors=False
        )
        return all_points

    def update(self, collection_name, data_list):
        """
        更新数据。
        :param table_name: 表名。
        :param data: 字典，键为要更新的列名，值为新数据。
                     例如: {'age': 31, 'email': 'new_alice@example.com'}
        :param conditions: WHERE 子句的条件字符串，例如 "id = %s"。
        :param params: 条件对应的参数 (元组或列表)。
        :return: 影响的行数，或 None。
        """


        if not data_list:
            print("错误：批量插入数据为空。")
            return None

        points_to_insert = [models.PointStruct(**data) for data in data_list]        

        # 更新 ID 为 1 的点的年龄
        self.connection.upsert(
            collection_name=collection_name,
            wait=True,
            points=points_to_insert
        )

    def set_payload_by_id(self,collection_name,payload:dict,ids = []):
        # 为 ID 2 的点设置一个新的字段 "occupation"
        self.connection.set_payload(
            collection_name=collection_name,
            payload=payload,
            points=ids, # 指定要更新的点 ID
            wait=True
        )
   
    def delete(self, collection_name, conditions, params=None):
        """
        删除数据。
        :param table_name: 表名。
        :param conditions: WHERE 子句的条件字符串，例如 "id = %s"。
        :param params: 条件对应的参数 (元组或列表)。
        :return: 影响的行数，或 None。
        """

        # 清除 ID 1 的点的 'status' 字段
        self.connection.clear_payload(
            collection_name=collection_name,
            points_selector=models.PointIdsList(points=[1]), # 也可以使用 query_filter
            keys=["status"],
            wait=True
        )

    def work(self,collection_name = "diglifetest2", target_document_id = "1977681868206968833"):
        """
        根据id llama_index 来查询是否存在
        """
        try:
            # 构建过滤器
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=target_document_id)
                    )
                ]
            )

            # 使用 scroll 方法
            # QdrantClient 的 scroll 方法会自动处理分页，但如果你需要手动控制，可以循环调用
            # 第一次调用，offset=None
            # 第二次及以后调用，offset=prev_result.next_page_offset
            
            # 简单的只获取一页结果
            scroll_result, next_page_offset = self.connection.scroll(
                collection_name=collection_name,
                scroll_filter=query_filter, # 注意参数是 scroll_filter
                limit=10,
                with_payload=True,
                with_vectors=False
            )

            if scroll_result:
                print(f"找到 document_id 为 '{target_document_id}' 的点:")
                for point in scroll_result:
                    print(f"ID: {point.id}, Payload: {point.payload}")
            else:
                print(f"未找到 document_id 为 '{target_document_id}' 的点。")

        except Exception as e:
            print(f"发生错误: {e}")

    def work2(self,collection_name = "diglifetest2",type_ = 1):
        """
        根据id llama_index 来查询是否存在
        """
        try:
            # 构建过滤器
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="type",
                        match=MatchValue(value=type_)
                    )
                ]
            )

            # 使用 scroll 方法
            # QdrantClient 的 scroll 方法会自动处理分页，但如果你需要手动控制，可以循环调用
            # 第一次调用，offset=None
            # 第二次及以后调用，offset=prev_result.next_page_offset
            
            # 简单的只获取一页结果
            scroll_result, next_page_offset = self.connection.scroll(
                collection_name=collection_name,
                scroll_filter=query_filter, # 注意参数是 scroll_filter
                limit=1000,
                with_payload=True,
                with_vectors=False
            )

            if scroll_result:
                for point in scroll_result:
                    doc_id = point.payload["document_id"]
                    print(f"ID: {point.id}, doc_id: {doc_id}")
            else:
                print(f"未找到")

        except Exception as e:
            print(f"发生错误: {e}")


'''

# 3. 使用属性删除点
# 目标：删除所有 'color' 属性为 'red' 的点

# 定义一个过滤器
# 这个过滤器会匹配所有 payload 中 'color' 字段值为 'red' 的点
red_color_filter = Filter(
    must=[
        FieldCondition(
            key="color",
            match=MatchValue(value="red")
        )
    ]
)

# 执行删除操作
# 注意：你需要将 `points_selector` 设置为 `red_color_filter`
delete_result = client.delete(
    collection_name=collection_name,
    points_selector=red_color_filter, # 使用过滤器来选择要删除的点
    wait=True
)

'''


# --- 假设的依赖项 ---
# Qdrant 客户端
from qdrant_client import QdrantClient, models # 你需要根据实际情况导入 Qdrant 客户端
qdrant_client = QdrantClient(host="localhost", port=6333) # 示例Qdrant客户端初始化


from typing import Any, List
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.embeddings import BaseEmbedding
from volcenginesdkarkruntime import Ark


class VolcanoEmbedding(BaseEmbedding):
    _model = PrivateAttr()
    _ark_client = PrivateAttr()
    _encoding_format = PrivateAttr()

    def __init__(
        self,
        model_name: str = "doubao-embedding-text-240715",
        api_key: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._ark_client = Ark(api_key=api_key)
        self._model = model_name
        self._encoding_format = "float"

    @classmethod
    def class_name(cls) -> str:
        return "ark"

    def _get_query_embedding(self, query: str) -> List[float]:
        """
        获取查询字符串的 embedding。
        通常查询和文档使用相同的 embedding 模型。
        """

        resp = self._ark_client.embeddings.create(
            model=self._model,
            input=[query],
            encoding_format=self._encoding_format,
        )
        return resp.data[0].embedding

    def _get_text_embedding(self, text: str) -> List[float]:
        """
        获取单个文档字符串的 embedding。
        """
        resp = self._ark_client.embeddings.create(
            model=self._model,
            input=[text],
            encoding_format=self._encoding_format,
        )
        return resp.data[0].embedding

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        批量获取文档字符串的 embedding。
        如果你的火山模型支持批量推理，强烈建议实现此方法以提高效率。
        否则，它可以简单地循环调用 _get_text_embedding。
        """
        resp = self._ark_client.embeddings.create(
            model=self._model,
            input=texts,
            encoding_format=self._encoding_format,
        )
        return [i.embedding for i in resp.data]

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

if __name__ == "__main__":

    embedding_model = VolcanoEmbedding(
        model_name = "doubao-embedding-text-240715",
        api_key = "39ad310a-c6f7-4d66-962e-1fbfa7e6edf1"
    )



from sqlalchemy import create_engine
import os
from typing import List
from .database import Base, CodeTemplate
from .vectorstore import VolcanoEmbedding
QDRANT_COLLECTION_NAME = "template_collection" # 你的 Qdrant collection 名称
from pro_craft.utils import create_session
from qdrant_client import QdrantClient, models
from uuid import uuid4
from .template_extract import extract_template
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct, CollectionStatus, Distance, VectorParams

class CoderTemplateManager():
    def __init__(self,
                 database_url = "mysql+pymysql://zxf_root:Zhf4233613%40@rm-2ze0793c6548pxs028o.mysql.rds.aliyuncs.com:3306/serverz",
                 model_name = "",
                 logger = None,
                ):
        database_url = database_url or os.getenv("database_url")
        assert database_url
        self.engine = create_engine(database_url, echo=False, # echo=True 仍然会打印所有执行的 SQL 语句
                                    pool_size=10,        # 连接池中保持的连接数
                                    max_overflow=20,     # 当pool_size不够时，允许临时创建的额外连接数
                                    pool_recycle=3600,   # 每小时回收一次连接
                                    pool_pre_ping=True,  # 使用前检查连接活性
                                    pool_timeout=30      # 等待连接池中连接的最长时间（秒）
                                    ) 
        self.embedding_model = VolcanoEmbedding(
            model_name = "doubao-embedding-text-240715",
            api_key = "39ad310a-c6f7-4d66-962e-1fbfa7e6edf1"
        )


        Base.metadata.create_all(self.engine)
        
        self.connection = QdrantClient(host="127.0.0.1", port=6333)

        self.connection.recreate_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=models.VectorParams(size=2560, distance=models.Distance.COSINE),
        )
        self.logger = logger
    
        # if model_name in ["gemini-2.5-flash-preview-05-20-nothinking",]:
        #     self.llm = BianXieAdapter(model_name = model_name)
        # elif model_name in ["doubao-1-5-pro-256k-250115","doubao-1-5-pro-32k-250115"]:
        #     self.llm = ArkAdapter(model_name = model_name)
        # else:
        #     raise Exception("error llm name")

    def get_embedding(self,text: str) -> List[float]:
        return self.embedding_model._get_text_embedding(text)
    
    def add_template(self,
                     use_case: str,
                     template_id: str,
                     description: str,):   
        template = extract_template(use_case)
        embedding_vector = self.get_embedding(description)
        points = [
                models.PointStruct(
                    id = str(uuid4()),
                    vector=embedding_vector,
                    payload={
                        "template_id": template_id,
                        "description": description,
                        "use_case": use_case,
                        "template": template,
                    }
                )
            ]
        self.connection.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            wait=True,
            points=points
        )
        # 数据库
        with create_session(self.engine) as session:
            new_template = CodeTemplate(
                template_id=template_id,
                version=1,
                description=description,
                template_code=template,
            )
            session.add(new_template)
            session.commit()
            session.refresh(new_template)
        return "success"


    def delete_template(self, template_id: str) -> bool:
        """
        逻辑删除指定的代码模板。
        """


        # 3. 使用属性删除点
        # 目标：删除所有 'color' 属性为 'red' 的点

        # 定义一个过滤器
        # 这个过滤器会匹配所有 payload 中 'color' 字段值为 'red' 的点
        _filter = Filter(
            must=[
                FieldCondition(
                    key="template_id",
                    match=MatchValue(value=template_id)
                )
            ]
        )
        self.connection.delete(
            collection_name=QDRANT_COLLECTION_NAME,
            points_selector=_filter,
            wait=True
        )


        with create_session(self.engine) as session:
            template = session.query(CodeTemplate).filter_by(template_id=template_id).first()
            if template:
                session.delete(template)
                session.commit()
                return True
        return False
    
        
    def search(self, text , limit , query_filter=None):
        query_vector = self.get_embedding(text)
        results = self.connection.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter
        )
        return results

    def get_template_obj(self, template_id: str):
        # 模拟从数据库获取模板详情
        # 实际使用时，你需要根据你的数据库 setup 来实现
        with create_session(self.engine) as session:
            template = session.query(CodeTemplate).filter_by(template_id = template_id).first()
        return template