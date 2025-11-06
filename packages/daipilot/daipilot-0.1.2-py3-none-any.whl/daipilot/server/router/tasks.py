from fastapi import APIRouter
from task_arrange.core import TaskManager

def create_router(database_url: str,
                  logger = None):
    task = TaskManager(database_url=database_url)

    router = APIRouter(
        tags=["task"] # 这里使用 Depends 确保每次请求都验证
    )

    @router.get("/create_project",
                description="可",)
    async def create_project(name: str, description: str):
        result = task.create_project("project1","this is project 1")
        return {"message": "success", "result": result}

    @router.get("/create_task",
                description="可",)
    async def create_task(title: str, description: str, due_date: str, status: str, priority: int):
        result = task.create_task(
            title=title,
            description=description,
            due_date=due_date,
            status=status,
            priority=priority
        )
        return {"message": "success", "result": result}
    

    @router.get("/search_tasks_by_title",description="可",)
    async def search_tasks_by_title(name: str):
        task.search_tasks_by_title(name)
        return {"message": "success", "result": ''}
    
    @router.get("/search_all_tasks")
    async def search_all_tasks():
        task.search_all_tasks()
        return {"message": "success", "result": ''}

    return router

