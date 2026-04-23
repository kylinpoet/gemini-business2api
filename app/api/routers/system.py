from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse


@dataclass(frozen=True)
class SystemRouteDeps:
    admin_key: Callable[[], str]
    get_config: Callable[[], Any]
    get_global_stats: Callable[[], dict[str, Any]]
    get_log_buffer: Callable[[], Any]
    get_multi_account_mgr: Callable[[], Any]
    get_sanitized_logs: Callable[[int], list[dict[str, Any]]]
    get_update_status: Callable[[], Any]
    get_version_info: Callable[[], Any]
    image_dir: str
    log_lock: Any
    logger: logging.Logger
    login_user: Callable[[Request], None]
    logout_user: Callable[[Request], None]
    require_login: Callable[..., Callable]
    save_stats: Callable[[dict[str, Any]], Awaitable[None]]
    scan_media_files: Callable[[], list[dict[str, Any]]]
    stats_db: Any
    stats_lock: Any
    uptime_tracker: Any
    video_dir: str


def register_system_routes(app: FastAPI, deps: SystemRouteDeps) -> None:
    @app.get("/")
    async def serve_frontend_index():
        index_path = os.path.join("static", "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(404, "Not Found")

    @app.get("/logo.svg")
    async def serve_logo():
        logo_path = os.path.join("static", "logo.svg")
        if os.path.exists(logo_path):
            return FileResponse(logo_path)
        raise HTTPException(404, "Not Found")

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    @app.get("/public/version")
    async def public_version():
        return deps.get_version_info()

    @app.post("/login")
    async def admin_login_post(request: Request, admin_key: str = Form(...)):
        if admin_key == deps.admin_key():
            deps.login_user(request)
            deps.logger.info("[AUTH] Admin login success")
            return {"success": True}
        deps.logger.warning("[AUTH] Login failed - invalid key")
        raise HTTPException(401, "Invalid key")

    @app.post("/logout")
    @deps.require_login(redirect_to_login=False)
    async def admin_logout(request: Request):
        deps.logout_user(request)
        deps.logger.info("[AUTH] Admin logout")
        return {"success": True}

    @app.get("/admin/version-check")
    @deps.require_login()
    async def admin_version_check(request: Request):
        return deps.get_update_status()

    @app.get("/admin/stats")
    @deps.require_login()
    async def admin_stats(request: Request, time_range: str = "24h"):
        multi_account_mgr = deps.get_multi_account_mgr()
        active_accounts = 0
        failed_accounts = 0
        rate_limited_accounts = 0
        idle_accounts = 0

        for account_manager in multi_account_mgr.accounts.values():
            account_config = account_manager.config
            cooldown_seconds, cooldown_reason = account_manager.get_cooldown_info()

            is_expired = account_config.is_expired()
            is_manual_disabled = account_config.disabled
            is_rate_limited = cooldown_seconds > 0 and cooldown_reason and "冷却" in cooldown_reason
            is_failed = is_expired
            is_active = (not is_failed) and (not is_manual_disabled) and (not is_rate_limited)

            if is_rate_limited:
                rate_limited_accounts += 1
            elif is_failed:
                failed_accounts += 1
            elif is_active:
                active_accounts += 1
            else:
                idle_accounts += 1

        trend_data = await deps.stats_db.get_stats_by_time_range(time_range)
        success_count, failed_count = await deps.stats_db.get_total_counts()

        return {
            "total_accounts": len(multi_account_mgr.accounts),
            "active_accounts": active_accounts,
            "failed_accounts": failed_accounts,
            "rate_limited_accounts": rate_limited_accounts,
            "idle_accounts": idle_accounts,
            "success_count": success_count,
            "failed_count": failed_count,
            "trend": trend_data,
        }

    @app.get("/admin/gallery")
    @deps.require_login()
    async def admin_get_gallery(request: Request):
        files = await asyncio.to_thread(deps.scan_media_files)
        total_size = sum(file_info["size"] for file_info in files)
        return {
            "files": files,
            "total": len(files),
            "total_size": total_size,
            "expire_hours": deps.get_config().basic.image_expire_hours,
        }

    @app.delete("/admin/gallery/{filename:path}")
    @deps.require_login()
    async def admin_delete_gallery_file(request: Request, filename: str):
        safe_name = os.path.basename(filename)
        if safe_name != filename or ".." in filename:
            raise HTTPException(400, "非法文件名")

        for directory in (deps.image_dir, deps.video_dir):
            filepath = os.path.join(directory, safe_name)
            if os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                    deps.logger.info(f"[GALLERY] Deleted file: {safe_name}")
                    return {"success": True, "message": f"Deleted {safe_name}"}
                except Exception as exc:
                    raise HTTPException(500, f"删除失败: {exc}") from exc

        raise HTTPException(404, "文件不存在")

    @app.post("/admin/gallery/cleanup")
    @deps.require_login()
    async def admin_cleanup_expired(request: Request):
        expire_hours = deps.get_config().basic.image_expire_hours
        if expire_hours < 0:
            return {
                "success": True,
                "deleted": 0,
                "deleted_images": 0,
                "deleted_videos": 0,
                "message": "当前设置为永不删除",
            }

        now = time.time()
        deleted_images = 0
        deleted_videos = 0
        video_exts = (".mp4", ".webm", ".mov")

        for directory, is_video_dir in ((deps.image_dir, False), (deps.video_dir, True)):
            if not os.path.isdir(directory):
                continue
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if not os.path.isfile(filepath):
                    continue
                try:
                    age_hours = (now - os.path.getmtime(filepath)) / 3600
                    if age_hours > expire_hours:
                        os.remove(filepath)
                        ext = os.path.splitext(filename)[1].lower()
                        if is_video_dir or ext in video_exts:
                            deleted_videos += 1
                        else:
                            deleted_images += 1
                except Exception:
                    continue

        deleted_count = deleted_images + deleted_videos
        if deleted_count > 0:
            deps.logger.info(
                "[GALLERY] Cleaned %s expired media files (images: %s, videos: %s)",
                deleted_count,
                deleted_images,
                deleted_videos,
            )

        return {
            "success": True,
            "deleted": deleted_count,
            "deleted_images": deleted_images,
            "deleted_videos": deleted_videos,
            "message": f"已清理 {deleted_count} 个过期文件" if deleted_count > 0 else "没有过期文件需要清理",
        }

    @app.get("/admin/log")
    @deps.require_login()
    async def admin_get_logs(
        request: Request,
        limit: int = 300,
        level: str | None = None,
        search: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ):
        log_buffer = deps.get_log_buffer()
        with deps.log_lock:
            logs = list(log_buffer)

        stats_by_level: dict[str, int] = {}
        error_logs = []
        chat_count = 0
        for log in logs:
            level_name = log.get("level", "INFO")
            stats_by_level[level_name] = stats_by_level.get(level_name, 0) + 1
            if level_name in ["ERROR", "CRITICAL"]:
                error_logs.append(log)
            if "收到请求" in log.get("message", ""):
                chat_count += 1

        if level:
            level = level.upper()
            logs = [log for log in logs if log["level"] == level]
        if search:
            logs = [log for log in logs if search.lower() in log["message"].lower()]
        if start_time:
            logs = [log for log in logs if log["time"] >= start_time]
        if end_time:
            logs = [log for log in logs if log["time"] <= end_time]

        limit = min(limit, log_buffer.maxlen)
        filtered_logs = logs[-limit:]

        return {
            "total": len(filtered_logs),
            "limit": limit,
            "filters": {
                "level": level,
                "search": search,
                "start_time": start_time,
                "end_time": end_time,
            },
            "logs": filtered_logs,
            "stats": {
                "memory": {
                    "total": len(log_buffer),
                    "by_level": stats_by_level,
                    "capacity": log_buffer.maxlen,
                },
                "errors": {"count": len(error_logs), "recent": error_logs[-10:]},
                "chat_count": chat_count,
            },
        }

    @app.delete("/admin/log")
    @deps.require_login()
    async def admin_clear_logs(request: Request, confirm: str | None = None):
        if confirm != "yes":
            raise HTTPException(400, "需要 confirm=yes 参数确认清空操作")
        log_buffer = deps.get_log_buffer()
        with deps.log_lock:
            cleared_count = len(log_buffer)
            log_buffer.clear()
        deps.logger.info("[LOG] Memory logs cleared")
        return {
            "status": "success",
            "message": "已清空内存日志",
            "cleared_count": cleared_count,
        }

    @app.get("/public/uptime")
    async def get_public_uptime(days: int = 90):
        if days < 1 or days > 90:
            days = 90
        return await deps.uptime_tracker.get_uptime_summary(days)

    @app.get("/public/stats")
    async def get_public_stats():
        async with deps.stats_lock:
            global_stats = deps.get_global_stats()
            current_time = time.time()
            recent_requests = [
                ts for ts in global_stats["request_timestamps"]
                if current_time - ts < 3600
            ]
            recent_minute = [ts for ts in recent_requests if current_time - ts < 60]
            requests_per_minute = len(recent_minute)

            if requests_per_minute < 10:
                load_status = "low"
                load_color = "#10b981"
            elif requests_per_minute < 30:
                load_status = "medium"
                load_color = "#f59e0b"
            else:
                load_status = "high"
                load_color = "#ef4444"

            return {
                "total_visitors": global_stats["total_visitors"],
                "total_requests": global_stats["total_requests"],
                "requests_per_minute": requests_per_minute,
                "load_status": load_status,
                "load_color": load_color,
            }

    @app.get("/public/display")
    async def get_public_display():
        public_display = deps.get_config().public_display
        return {
            "logo_url": public_display.logo_url,
            "chat_url": public_display.chat_url,
        }

    @app.get("/public/log")
    async def get_public_logs(request: Request, limit: int = 100):
        try:
            client_ip = request.client.host if request.client else "unknown"
            current_time = time.time()

            async with deps.stats_lock:
                global_stats = deps.get_global_stats()
                if "visitor_ips" not in global_stats:
                    global_stats["visitor_ips"] = {}
                global_stats["visitor_ips"] = {
                    ip: timestamp
                    for ip, timestamp in global_stats["visitor_ips"].items()
                    if current_time - timestamp <= 86400
                }
                if client_ip not in global_stats["visitor_ips"]:
                    global_stats["visitor_ips"][client_ip] = current_time
                    global_stats["total_visitors"] = global_stats.get("total_visitors", 0) + 1

                global_stats.setdefault("recent_conversations", [])
                await deps.save_stats(global_stats)
                stored_logs = list(global_stats.get("recent_conversations", []))

            sanitized_logs = deps.get_sanitized_logs(limit=min(limit, 1000))
            log_map = {log.get("request_id"): log for log in sanitized_logs}
            for log in stored_logs:
                request_id = log.get("request_id")
                if request_id and request_id not in log_map:
                    log_map[request_id] = log

            def get_log_ts(item: dict[str, Any]) -> float:
                if "start_ts" in item:
                    return float(item["start_ts"])
                try:
                    return datetime.strptime(item.get("start_time", ""), "%Y-%m-%d %H:%M:%S").timestamp()
                except Exception:
                    return 0.0

            merged_logs = sorted(log_map.values(), key=get_log_ts, reverse=True)[: min(limit, 1000)]
            output_logs = []
            for log in merged_logs:
                if "start_ts" in log:
                    log = dict(log)
                    log.pop("start_ts", None)
                output_logs.append(log)

            return {"total": len(output_logs), "logs": output_logs}
        except Exception as exc:
            deps.logger.error(f"[LOG] Failed to load public logs: {exc}")
            return {"total": 0, "logs": [], "error": str(exc)}

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
