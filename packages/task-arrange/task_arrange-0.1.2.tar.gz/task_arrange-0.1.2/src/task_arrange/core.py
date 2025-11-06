

import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .database import Base, Project,Task


from contextlib import contextmanager
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine # 异步核心
from contextlib import asynccontextmanager # 注意这里是 asynccontextmanager

from sqlalchemy import create_engine

@contextmanager
def create_session(engine):
    # 5. 创建会话 (Session)
    # Session 是与数据库交互的主要接口，它管理着你的对象和数据库之间的持久化操作
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session

    except Exception as e:
        print(f"An error occurred: {e}")
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
        # await session.commit() # 在成功的情况下自动提交事务

    except Exception as e:
        print(f"An error occurred: {e}")
        await session.rollback() # 发生错误时回滚事务
        raise # 重新抛出异常，让调用者知道操作失败
    finally:
        await session.close() # 关闭会话，释放资源



class TaskManager():
    def __init__(self,
                 database_url = "",
                 model_name = "",
                 logger = None,
                ):
        database_url = database_url or os.getenv("database_url")
        print(database_url,'database_url')
        self.logger = logger
        self.engine = create_engine(database_url, echo=False,
                                    pool_size=10,        # 连接池中保持的连接数
                                    max_overflow=20,     # 当pool_size不够时，允许临时创建的额外连接数
                                    pool_recycle=3600,   # 每小时回收一次连接
                                    pool_pre_ping=True,  # 使用前检查连接活性
                                    pool_timeout=30      # 等待连接池中连接的最长时间（秒）
                                           )
        Base.metadata.create_all(self.engine)

    async def create_database(self,engine):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def create_project(self,name,description):
        with create_session(self.engine) as session:
            new_project = Project(name=name, description=description)
            session.add(new_project)
            session.commit()
            self.logger and self.logger.info(f"Created project: {new_project}")
            return new_project
        
    def create_task(self,title,description,due_date,status,priority):
        with create_session(self.engine) as session:
            new_task = Task(
                title=title,
                description=description,
                due_date=due_date,
                status=status,
                priority=priority,
            )
            session.add(new_task)
            session.commit()
            self.logger and self.logger.info(f"Created task: {new_task}")
            return new_task
        
    def search_tasks_by_title(self,title_keyword):
        with create_session(self.engine) as session:
            results = session.query(Task).filter(Task.title.ilike(f"%{title_keyword}%")).all()
            return results

        
    def search_all_tasks(self):
        with create_session(self.engine) as session:
            results = session.query(Task).all()
            return results
        
    def search_by_time_range(self,start_date,end_date):
        with create_session(self.engine) as session:
            results = session.query(Task).filter(Task.due_date.between(start_date, end_date)).all()
            return results
        
    def update_task_status(self,task_id,new_status):
        with create_session(self.engine) as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = new_status
                session.commit()
                self.logger and self.logger.info(f"Updated task status: {task}")
                return task
            else:
                self.logger and self.logger.warning(f"Task with id {task_id} not found.")
                return None
            
    def delete_task(self,task_id):
        with create_session(self.engine) as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                session.delete(task)
                session.commit()
                self.logger and self.logger.info(f"Deleted task: {task}")
                return True
            else:
                self.logger and self.logger.warning(f"Task with id {task_id} not found.")
                return False
    
