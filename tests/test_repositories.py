import json
import pytest
from pathlib import Path
from src.infrastructure.repositories import TaskRepository

@pytest.fixture
def temp_task_file(tmp_path):
    f = tmp_path / "tasks.json"
    return str(f)

def test_task_repository_add(temp_task_file):
    repo = TaskRepository(temp_task_file)
    task = repo.add({"content": "Test task"})
    
    assert task["content"] == "Test task"
    assert task["status"] == "pending"
    assert "id" in task
    assert "created_at" in task

def test_task_repository_list_pending(temp_task_file):
    repo = TaskRepository(temp_task_file)
    repo.add({"content": "Task 1"})
    repo.add({"content": "Task 2"})
    
    pending = repo.list_pending()
    assert len(pending) == 2

def test_task_repository_complete(temp_task_file):
    repo = TaskRepository(temp_task_file)
    task = repo.add({"content": "Task to complete"})
    task_id = task["id"]
    
    completed = repo.complete(task_id[:8])
    assert completed["status"] == "completed"
    assert "completed_at" in completed
    
    pending = repo.list_pending()
    assert len(pending) == 0
