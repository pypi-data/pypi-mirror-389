from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine # 异步核心
from contextlib import asynccontextmanager, contextmanager
from db_handy import logger

@contextmanager
def create_session(engine):
    # 5. 创建会话 (Session)
    # Session 是与数据库交互的主要接口，它管理着你的对象和数据库之间的持久化操作
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session

    except Exception as e:
        logger.error(f"An error & {e}& -")
        session.rollback() # 发生错误时回滚事务
    finally:
        session.close() # 关闭会话，释放资源


@asynccontextmanager
async def create_async_session(async_engine):
    # 5. 创建会话 (Session)
    # Session 是与数据库交互的主要接口，它管理着你的对象和数据库之间的持久化操作
    Session = sessionmaker(bind=async_engine,
                           expire_on_commit=False, 
                           class_=AsyncSession
                           )
    session = Session()
    try:
        yield session
        
    except Exception as e:
        logger.error(f"An error async & {e}& -")
        await session.rollback() # 发生错误时回滚事务
    finally:
        await session.close() # 关闭会话，释放资源

