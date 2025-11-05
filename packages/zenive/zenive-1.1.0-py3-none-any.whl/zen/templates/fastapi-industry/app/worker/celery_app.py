"""
Celery application configuration for FastAPI Industry Template.

Provides distributed task queue with Redis broker, result backend,
monitoring, and comprehensive task management.
"""

import os
from typing import Any, Dict

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_success
import structlog

from app.core.config import settings
from app.middleware.metrics import record_background_task

logger = structlog.get_logger(__name__)

# Create Celery application
celery_app = Celery(
    "fastapi_industry_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.worker.tasks.send_email": {"queue": "emails"},
        "app.worker.tasks.process_upload": {"queue": "uploads"},
        "app.worker.tasks.generate_report": {"queue": "reports"},
        "app.worker.tasks.cleanup_old_data": {"queue": "maintenance"},
    },
    
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,       # 10 minutes hard limit
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-data": {
            "task": "app.worker.tasks.cleanup_old_data",
            "schedule": 3600.0,  # Run every hour
        },
        "health-check": {
            "task": "app.worker.tasks.health_check",
            "schedule": 300.0,  # Run every 5 minutes
        },
        "generate-daily-report": {
            "task": "app.worker.tasks.generate_daily_report",
            "schedule": 86400.0,  # Run daily
        },
    },
    
    # Queue configuration
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "emails": {
            "exchange": "emails",
            "routing_key": "emails",
        },
        "uploads": {
            "exchange": "uploads", 
            "routing_key": "uploads",
        },
        "reports": {
            "exchange": "reports",
            "routing_key": "reports",
        },
        "maintenance": {
            "exchange": "maintenance",
            "routing_key": "maintenance",
        },
    },
)


# Task monitoring signals
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Log task start."""
    logger.info(
        "Task started",
        task_id=task_id,
        task_name=task.name if task else sender,
        args=args,
        kwargs=kwargs
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                        retval=None, state=None, **kwds):
    """Log task completion."""
    logger.info(
        "Task completed",
        task_id=task_id,
        task_name=task.name if task else sender,
        state=state,
        return_value=str(retval)[:100] if retval else None
    )
    
    # Record metrics
    task_name = task.name if task else sender
    record_background_task(task_name, state == "SUCCESS")


@task_success.connect
def task_success_handler(sender=None, result=None, **kwds):
    """Handle successful task completion."""
    logger.info("Task succeeded", task_name=sender, result=str(result)[:100] if result else None)


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Handle task failure."""
    logger.error(
        "Task failed",
        task_id=task_id,
        task_name=sender,
        exception=str(exception),
        traceback=traceback
    )
    
    # Record failure metrics
    record_background_task(sender, False)


# Utility functions for task management
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a specific task."""
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "traceback": result.traceback,
            "date_done": result.date_done,
        }
    except Exception as e:
        logger.error("Error getting task status", task_id=task_id, error=str(e))
        return {"task_id": task_id, "status": "UNKNOWN", "error": str(e)}


def cancel_task(task_id: str) -> bool:
    """Cancel a running task."""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info("Task cancelled", task_id=task_id)
        return True
    except Exception as e:
        logger.error("Error cancelling task", task_id=task_id, error=str(e))
        return False


def get_active_tasks() -> Dict[str, Any]:
    """Get list of active tasks."""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        return active_tasks or {}
    except Exception as e:
        logger.error("Error getting active tasks", error=str(e))
        return {}


def get_worker_stats() -> Dict[str, Any]:
    """Get worker statistics."""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        return stats or {}
    except Exception as e:
        logger.error("Error getting worker stats", error=str(e))
        return {}


def purge_queue(queue_name: str) -> int:
    """Purge all tasks from a specific queue."""
    try:
        purged = celery_app.control.purge()
        logger.info("Queue purged", queue=queue_name, purged_count=purged)
        return purged
    except Exception as e:
        logger.error("Error purging queue", queue=queue_name, error=str(e))
        return 0


# Health check for Celery workers
def check_celery_health() -> Dict[str, Any]:
    """Check health of Celery workers."""
    try:
        inspect = celery_app.control.inspect()
        
        # Check if workers are available
        stats = inspect.stats()
        active = inspect.active()
        
        if not stats:
            return {
                "status": "unhealthy",
                "message": "No workers available",
                "workers": 0,
                "active_tasks": 0
            }
        
        worker_count = len(stats)
        active_task_count = sum(len(tasks) for tasks in (active or {}).values())
        
        return {
            "status": "healthy",
            "message": f"{worker_count} workers available",
            "workers": worker_count,
            "active_tasks": active_task_count,
            "worker_stats": stats
        }
        
    except Exception as e:
        logger.error("Error checking Celery health", error=str(e))
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "workers": 0,
            "active_tasks": 0
        }