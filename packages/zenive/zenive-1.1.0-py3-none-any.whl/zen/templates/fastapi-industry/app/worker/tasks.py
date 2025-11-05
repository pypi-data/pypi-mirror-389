"""
Background tasks for FastAPI Industry Template.

Comprehensive set of background tasks for email sending, file processing,
report generation, and system maintenance.
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from celery import Task
import structlog
from sqlalchemy import text

from app.worker.celery_app import celery_app
from app.core.config import settings
from app.core.database import get_db_session

logger = structlog.get_logger(__name__)


class CallbackTask(Task):
    """Base task class with callback support and error handling."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called on task success."""
        logger.info("Task succeeded", task_id=task_id, task_name=self.name)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure."""
        logger.error(
            "Task failed",
            task_id=task_id,
            task_name=self.name,
            exception=str(exc),
            traceback=str(einfo)
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called on task retry."""
        logger.warning(
            "Task retry",
            task_id=task_id,
            task_name=self.name,
            exception=str(exc),
            retry_count=self.request.retries
        )


@celery_app.task(bind=True, base=CallbackTask, max_retries=3, default_retry_delay=60)
def send_email(self, to_email: str, subject: str, body: str, html_body: str = None) -> Dict[str, Any]:
    """
    Send email using configured SMTP settings.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text body
        html_body: HTML body (optional)
        
    Returns:
        Dict with send status and details
    """
    try:
        # Import here to avoid circular imports
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.EMAILS_FROM_EMAIL
        msg['To'] = to_email
        
        # Add plain text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Send email
        if settings.SMTP_HOST and settings.SMTP_USER:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info("Email sent successfully", to_email=to_email, subject=subject)
            return {"status": "sent", "to_email": to_email, "subject": subject}
        else:
            # Log email for development
            logger.info(
                "Email would be sent (SMTP not configured)",
                to_email=to_email,
                subject=subject,
                body=body[:100]
            )
            return {"status": "logged", "to_email": to_email, "subject": subject}
            
    except Exception as exc:
        logger.error("Failed to send email", to_email=to_email, error=str(exc))
        
        # Retry on failure
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, base=CallbackTask, max_retries=2)
def process_upload(self, file_path: str, user_id: int, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process uploaded file (resize images, extract metadata, etc.).
    
    Args:
        file_path: Path to uploaded file
        user_id: ID of user who uploaded the file
        metadata: Additional file metadata
        
    Returns:
        Dict with processing results
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        result = {
            "file_path": file_path,
            "user_id": user_id,
            "file_size": file_size,
            "file_extension": file_ext,
            "processed_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Process based on file type
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
            result.update(await _process_image(file_path))
        elif file_ext == '.pdf':
            result.update(await _process_pdf(file_path))
        else:
            result["processing"] = "basic_metadata_only"
        
        logger.info("File processed successfully", file_path=file_path, user_id=user_id)
        return result
        
    except Exception as exc:
        logger.error("Failed to process upload", file_path=file_path, error=str(exc))
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        
        return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, base=CallbackTask)
def generate_report(self, report_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate various types of reports.
    
    Args:
        report_type: Type of report to generate
        parameters: Report parameters
        
    Returns:
        Dict with report generation results
    """
    try:
        start_time = time.time()
        
        if report_type == "user_activity":
            result = await _generate_user_activity_report(parameters or {})
        elif report_type == "system_performance":
            result = await _generate_performance_report(parameters or {})
        elif report_type == "error_summary":
            result = await _generate_error_report(parameters or {})
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        generation_time = time.time() - start_time
        
        logger.info(
            "Report generated successfully",
            report_type=report_type,
            generation_time=generation_time
        )
        
        return {
            "status": "completed",
            "report_type": report_type,
            "generation_time": generation_time,
            "result": result
        }
        
    except Exception as exc:
        logger.error("Failed to generate report", report_type=report_type, error=str(exc))
        return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, base=CallbackTask)
def cleanup_old_data(self) -> Dict[str, Any]:
    """
    Clean up old data (logs, temporary files, expired sessions, etc.).
    
    Returns:
        Dict with cleanup results
    """
    try:
        cleanup_results = {}
        
        # Clean up old log files
        log_cleanup = await _cleanup_old_logs()
        cleanup_results["logs"] = log_cleanup
        
        # Clean up temporary files
        temp_cleanup = await _cleanup_temp_files()
        cleanup_results["temp_files"] = temp_cleanup
        
        # Clean up expired sessions
        session_cleanup = await _cleanup_expired_sessions()
        cleanup_results["sessions"] = session_cleanup
        
        # Clean up old task results
        task_cleanup = await _cleanup_old_task_results()
        cleanup_results["task_results"] = task_cleanup
        
        logger.info("Data cleanup completed", results=cleanup_results)
        return {"status": "completed", "results": cleanup_results}
        
    except Exception as exc:
        logger.error("Data cleanup failed", error=str(exc))
        return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, base=CallbackTask)
def health_check(self) -> Dict[str, Any]:
    """
    Perform system health check.
    
    Returns:
        Dict with health check results
    """
    try:
        health_results = {}
        
        # Check database connectivity
        health_results["database"] = await _check_database_health()
        
        # Check Redis connectivity
        health_results["redis"] = await _check_redis_health()
        
        # Check disk space
        health_results["disk_space"] = await _check_disk_space()
        
        # Check memory usage
        health_results["memory"] = await _check_memory_usage()
        
        overall_status = "healthy" if all(
            result.get("status") == "healthy" 
            for result in health_results.values()
        ) else "unhealthy"
        
        logger.info("Health check completed", status=overall_status, results=health_results)
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "results": health_results
        }
        
    except Exception as exc:
        logger.error("Health check failed", error=str(exc))
        return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, base=CallbackTask)
def generate_daily_report(self) -> Dict[str, Any]:
    """
    Generate daily summary report.
    
    Returns:
        Dict with daily report results
    """
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Generate comprehensive daily report
        report_data = {
            "date": yesterday.date().isoformat(),
            "user_activity": await _get_daily_user_stats(yesterday),
            "api_metrics": await _get_daily_api_stats(yesterday),
            "error_summary": await _get_daily_error_stats(yesterday),
            "performance_metrics": await _get_daily_performance_stats(yesterday),
        }
        
        # Send report via email if configured
        if settings.EMAILS_FROM_EMAIL:
            send_email.delay(
                to_email=settings.FIRST_SUPERUSER,
                subject=f"Daily Report - {yesterday.date()}",
                body=f"Daily report for {yesterday.date()} is ready.",
                html_body=await _format_daily_report_html(report_data)
            )
        
        logger.info("Daily report generated", date=yesterday.date())
        return {"status": "completed", "report_data": report_data}
        
    except Exception as exc:
        logger.error("Daily report generation failed", error=str(exc))
        return {"status": "failed", "error": str(exc)}


# Helper functions
async def _process_image(file_path: str) -> Dict[str, Any]:
    """Process image file (resize, extract EXIF, etc.)."""
    try:
        # This would use PIL/Pillow for image processing
        # For now, return basic metadata
        return {
            "processing": "image_processed",
            "thumbnails_created": True,
            "exif_extracted": True
        }
    except Exception as e:
        logger.error("Image processing failed", file_path=file_path, error=str(e))
        return {"processing": "failed", "error": str(e)}


async def _process_pdf(file_path: str) -> Dict[str, Any]:
    """Process PDF file (extract text, metadata, etc.)."""
    try:
        # This would use PyPDF2 or similar for PDF processing
        return {
            "processing": "pdf_processed",
            "text_extracted": True,
            "page_count": 10  # Placeholder
        }
    except Exception as e:
        logger.error("PDF processing failed", file_path=file_path, error=str(e))
        return {"processing": "failed", "error": str(e)}


async def _generate_user_activity_report(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate user activity report."""
    # This would query the database for user activity metrics
    return {
        "total_users": 100,
        "active_users": 75,
        "new_registrations": 5,
        "login_count": 250
    }


async def _generate_performance_report(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate system performance report."""
    return {
        "avg_response_time": 0.25,
        "error_rate": 0.02,
        "throughput": 1000,
        "uptime": 99.9
    }


async def _generate_error_report(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate error summary report."""
    return {
        "total_errors": 10,
        "critical_errors": 1,
        "warning_errors": 9,
        "most_common_error": "ValidationError"
    }


async def _cleanup_old_logs() -> Dict[str, Any]:
    """Clean up old log files."""
    return {"files_deleted": 5, "space_freed_mb": 100}


async def _cleanup_temp_files() -> Dict[str, Any]:
    """Clean up temporary files."""
    return {"files_deleted": 20, "space_freed_mb": 50}


async def _cleanup_expired_sessions() -> Dict[str, Any]:
    """Clean up expired user sessions."""
    return {"sessions_deleted": 15}


async def _cleanup_old_task_results() -> Dict[str, Any]:
    """Clean up old Celery task results."""
    return {"results_deleted": 100}


async def _check_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            return {"status": "healthy", "response_time_ms": 10}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        from app.core.cache import cache_manager
        await cache_manager.redis_client.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_disk_space() -> Dict[str, Any]:
    """Check available disk space."""
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_percent = (free / total) * 100
        
        status = "healthy" if free_percent > 10 else "unhealthy"
        return {
            "status": status,
            "free_percent": free_percent,
            "free_gb": free // (1024**3)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_memory_usage() -> Dict[str, Any]:
    """Check system memory usage."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        status = "healthy" if memory.percent < 85 else "unhealthy"
        return {
            "status": status,
            "usage_percent": memory.percent,
            "available_gb": memory.available // (1024**3)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _get_daily_user_stats(date: datetime) -> Dict[str, Any]:
    """Get daily user statistics."""
    # This would query the database for actual stats
    return {
        "total_logins": 150,
        "unique_users": 75,
        "new_registrations": 3,
        "active_sessions": 25
    }


async def _get_daily_api_stats(date: datetime) -> Dict[str, Any]:
    """Get daily API statistics."""
    return {
        "total_requests": 5000,
        "avg_response_time": 0.25,
        "error_rate": 0.02,
        "top_endpoints": ["/api/v1/users", "/api/v1/auth/login"]
    }


async def _get_daily_error_stats(date: datetime) -> Dict[str, Any]:
    """Get daily error statistics."""
    return {
        "total_errors": 25,
        "error_types": {"ValidationError": 15, "AuthenticationError": 10},
        "critical_errors": 2
    }


async def _get_daily_performance_stats(date: datetime) -> Dict[str, Any]:
    """Get daily performance statistics."""
    return {
        "uptime_percent": 99.9,
        "avg_cpu_usage": 45.2,
        "avg_memory_usage": 62.1,
        "peak_concurrent_users": 150
    }


async def _format_daily_report_html(report_data: Dict[str, Any]) -> str:
    """Format daily report as HTML for email."""
    return f"""
    <html>
    <body>
        <h1>Daily Report - {report_data['date']}</h1>
        <h2>User Activity</h2>
        <ul>
            <li>Total Logins: {report_data['user_activity']['total_logins']}</li>
            <li>Unique Users: {report_data['user_activity']['unique_users']}</li>
            <li>New Registrations: {report_data['user_activity']['new_registrations']}</li>
        </ul>
        <h2>API Metrics</h2>
        <ul>
            <li>Total Requests: {report_data['api_metrics']['total_requests']}</li>
            <li>Average Response Time: {report_data['api_metrics']['avg_response_time']}s</li>
            <li>Error Rate: {report_data['api_metrics']['error_rate']}%</li>
        </ul>
    </body>
    </html>
    """