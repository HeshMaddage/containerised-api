from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
import json

from .database import engine, get_db
from . import models, schemas
from .cache import get_cached, set_cache, invalidate_cache

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API", version="1.0.0")

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/tasks", response_model=List[schemas.TaskResponse])
def list_tasks(response: Response, db: Session = Depends(get_db)):
    cached = get_cached("tasks:all")
    if cached:
        response.headers["X-Cache"] = "HIT"
        return json.loads(cached)
    
    tasks = db.query(models.Task).all()
    response.headers["X-Cache"] = "MISS"
    serialised = [schemas.TaskResponse.from_orm(t).dict() for t in tasks]
    set_cache("tasks:all", json.dumps(serialised, default=str))
    return tasks

@app.post("/tasks", response_model=schemas.TaskResponse, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    invalidate_cache("tasks:*")
    return db_task

@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task(task_id: int, response: Response, db: Session = Depends(get_db)):
    cached = get_cached(f"tasks:{task_id}")
    if cached:
        response.headers["X-Cache"] = "HIT"
        return json.loads(cached)
    
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response.headers["X-Cache"] = "MISS"
    set_cache(f"tasks:{task_id}", json.dumps(schemas.TaskResponse.from_orm(task).dict(), default=str))
    return task

@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, updates: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    invalidate_cache("tasks:*")
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    invalidate_cache("tasks:*")