from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Callable

from fastapi import Body, FastAPI, HTTPException, Request


@dataclass(frozen=True)
class SettingsRouteDeps:
    apply_runtime_state: Callable[[dict[str, Any]], None]
    build_retry_policy: Callable[[], Any]
    config_manager: Any
    create_http_client: Callable[[str | None], Any]
    get_config: Callable[[], Any]
    get_multi_account_mgr: Callable[[], Any]
    get_runtime_state: Callable[[], dict[str, Any]]
    logger: logging.Logger
    parse_proxy_setting: Callable[[str], tuple[str | None, str | None]]
    require_login: Callable[..., Callable]


REFRESH_BASIC_KEYS = (
    "proxy_for_auth",
    "duckmail_base_url",
    "duckmail_api_key",
    "duckmail_verify_ssl",
    "temp_mail_provider",
    "moemail_base_url",
    "moemail_api_key",
    "moemail_domain",
    "freemail_base_url",
    "freemail_jwt_token",
    "freemail_verify_ssl",
    "freemail_domain",
    "mail_proxy_enabled",
    "gptmail_base_url",
    "gptmail_api_key",
    "gptmail_verify_ssl",
    "gptmail_domain",
    "cfmail_base_url",
    "cfmail_api_key",
    "cfmail_verify_ssl",
    "cfmail_domain",
    "browser_mode",
    "browser_headless",
    "refresh_window_hours",
    "register_domain",
    "register_default_count",
)

REFRESH_RETRY_KEYS = (
    "auto_refresh_accounts_seconds",
    "scheduled_refresh_enabled",
    "scheduled_refresh_interval_minutes",
    "scheduled_refresh_cron",
    "verification_code_resend_count",
    "refresh_batch_size",
    "refresh_batch_interval_minutes",
    "refresh_cooldown_hours",
    "delete_expired_accounts",
    "auto_register_enabled",
    "min_account_count",
)


def _build_refresh_settings(current_config: Any) -> dict[str, Any]:
    basic = current_config.basic
    retry = current_config.retry
    return {
        "proxy_for_auth": basic.proxy_for_auth,
        "duckmail": {
            "base_url": basic.duckmail_base_url,
            "api_key": basic.duckmail_api_key,
            "verify_ssl": basic.duckmail_verify_ssl,
        },
        "temp_mail_provider": basic.temp_mail_provider,
        "moemail": {
            "base_url": basic.moemail_base_url,
            "api_key": basic.moemail_api_key,
            "domain": basic.moemail_domain,
        },
        "freemail": {
            "base_url": basic.freemail_base_url,
            "jwt_token": basic.freemail_jwt_token,
            "verify_ssl": basic.freemail_verify_ssl,
            "domain": basic.freemail_domain,
        },
        "mail_proxy_enabled": basic.mail_proxy_enabled,
        "gptmail": {
            "base_url": basic.gptmail_base_url,
            "api_key": basic.gptmail_api_key,
            "verify_ssl": basic.gptmail_verify_ssl,
            "domain": basic.gptmail_domain,
        },
        "cfmail": {
            "base_url": basic.cfmail_base_url,
            "api_key": basic.cfmail_api_key,
            "verify_ssl": basic.cfmail_verify_ssl,
            "domain": basic.cfmail_domain,
        },
        "browser_mode": basic.browser_mode,
        "browser_headless": basic.browser_headless,
        "refresh_window_hours": basic.refresh_window_hours,
        "register_domain": basic.register_domain,
        "register_default_count": basic.register_default_count,
        "auto_refresh_accounts_seconds": retry.auto_refresh_accounts_seconds,
        "scheduled_refresh_enabled": retry.scheduled_refresh_enabled,
        "scheduled_refresh_interval_minutes": retry.scheduled_refresh_interval_minutes,
        "scheduled_refresh_cron": retry.scheduled_refresh_cron,
        "verification_code_resend_count": retry.verification_code_resend_count,
        "refresh_batch_size": retry.refresh_batch_size,
        "refresh_batch_interval_minutes": retry.refresh_batch_interval_minutes,
        "refresh_cooldown_hours": retry.refresh_cooldown_hours,
        "delete_expired_accounts": retry.delete_expired_accounts,
        "auto_register_enabled": retry.auto_register_enabled,
        "min_account_count": retry.min_account_count,
    }


def _merge_refresh_settings(
    incoming_basic: dict[str, Any],
    incoming_retry: dict[str, Any],
    incoming_refresh: dict[str, Any],
    current_config: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    merged_basic = dict(incoming_basic)
    merged_retry = dict(incoming_retry)

    for key in REFRESH_BASIC_KEYS:
        if key not in merged_basic and hasattr(current_config.basic, key):
            merged_basic[key] = getattr(current_config.basic, key)

    for key in REFRESH_RETRY_KEYS:
        if key not in merged_retry and hasattr(current_config.retry, key):
            merged_retry[key] = getattr(current_config.retry, key)

    if not incoming_refresh:
        return merged_basic, merged_retry

    merged_basic["proxy_for_auth"] = incoming_refresh.get("proxy_for_auth", merged_basic["proxy_for_auth"])

    duckmail = dict(incoming_refresh.get("duckmail") or {})
    merged_basic["duckmail_base_url"] = duckmail.get("base_url", merged_basic["duckmail_base_url"])
    merged_basic["duckmail_api_key"] = duckmail.get("api_key", merged_basic["duckmail_api_key"])
    merged_basic["duckmail_verify_ssl"] = duckmail.get("verify_ssl", merged_basic["duckmail_verify_ssl"])

    merged_basic["temp_mail_provider"] = incoming_refresh.get("temp_mail_provider", merged_basic["temp_mail_provider"])

    moemail = dict(incoming_refresh.get("moemail") or {})
    merged_basic["moemail_base_url"] = moemail.get("base_url", merged_basic["moemail_base_url"])
    merged_basic["moemail_api_key"] = moemail.get("api_key", merged_basic["moemail_api_key"])
    merged_basic["moemail_domain"] = moemail.get("domain", merged_basic["moemail_domain"])

    freemail = dict(incoming_refresh.get("freemail") or {})
    merged_basic["freemail_base_url"] = freemail.get("base_url", merged_basic["freemail_base_url"])
    merged_basic["freemail_jwt_token"] = freemail.get("jwt_token", merged_basic["freemail_jwt_token"])
    merged_basic["freemail_verify_ssl"] = freemail.get("verify_ssl", merged_basic["freemail_verify_ssl"])
    merged_basic["freemail_domain"] = freemail.get("domain", merged_basic["freemail_domain"])

    merged_basic["mail_proxy_enabled"] = incoming_refresh.get("mail_proxy_enabled", merged_basic["mail_proxy_enabled"])

    gptmail = dict(incoming_refresh.get("gptmail") or {})
    merged_basic["gptmail_base_url"] = gptmail.get("base_url", merged_basic["gptmail_base_url"])
    merged_basic["gptmail_api_key"] = gptmail.get("api_key", merged_basic["gptmail_api_key"])
    merged_basic["gptmail_verify_ssl"] = gptmail.get("verify_ssl", merged_basic["gptmail_verify_ssl"])
    merged_basic["gptmail_domain"] = gptmail.get("domain", merged_basic["gptmail_domain"])

    cfmail = dict(incoming_refresh.get("cfmail") or {})
    merged_basic["cfmail_base_url"] = cfmail.get("base_url", merged_basic["cfmail_base_url"])
    merged_basic["cfmail_api_key"] = cfmail.get("api_key", merged_basic["cfmail_api_key"])
    merged_basic["cfmail_verify_ssl"] = cfmail.get("verify_ssl", merged_basic["cfmail_verify_ssl"])
    merged_basic["cfmail_domain"] = cfmail.get("domain", merged_basic["cfmail_domain"])

    merged_basic["browser_mode"] = incoming_refresh.get("browser_mode", merged_basic["browser_mode"])
    merged_basic["browser_headless"] = incoming_refresh.get("browser_headless", merged_basic["browser_headless"])
    merged_basic["refresh_window_hours"] = incoming_refresh.get("refresh_window_hours", merged_basic["refresh_window_hours"])
    merged_basic["register_domain"] = incoming_refresh.get("register_domain", merged_basic["register_domain"])
    merged_basic["register_default_count"] = incoming_refresh.get("register_default_count", merged_basic["register_default_count"])

    for key in REFRESH_RETRY_KEYS:
        if key in incoming_refresh:
            merged_retry[key] = incoming_refresh[key]

    return merged_basic, merged_retry


def _coerce_refresh_settings_from_legacy(
    incoming_basic: dict[str, Any],
    incoming_retry: dict[str, Any],
    current_config: Any,
) -> dict[str, Any]:
    refresh_settings = _build_refresh_settings(current_config)

    if "proxy_for_auth" in incoming_basic:
        refresh_settings["proxy_for_auth"] = incoming_basic["proxy_for_auth"]
    if "duckmail_base_url" in incoming_basic:
        refresh_settings["duckmail"]["base_url"] = incoming_basic["duckmail_base_url"]
    if "duckmail_api_key" in incoming_basic:
        refresh_settings["duckmail"]["api_key"] = incoming_basic["duckmail_api_key"]
    if "duckmail_verify_ssl" in incoming_basic:
        refresh_settings["duckmail"]["verify_ssl"] = incoming_basic["duckmail_verify_ssl"]
    if "temp_mail_provider" in incoming_basic:
        refresh_settings["temp_mail_provider"] = incoming_basic["temp_mail_provider"]
    if "moemail_base_url" in incoming_basic:
        refresh_settings["moemail"]["base_url"] = incoming_basic["moemail_base_url"]
    if "moemail_api_key" in incoming_basic:
        refresh_settings["moemail"]["api_key"] = incoming_basic["moemail_api_key"]
    if "moemail_domain" in incoming_basic:
        refresh_settings["moemail"]["domain"] = incoming_basic["moemail_domain"]
    if "freemail_base_url" in incoming_basic:
        refresh_settings["freemail"]["base_url"] = incoming_basic["freemail_base_url"]
    if "freemail_jwt_token" in incoming_basic:
        refresh_settings["freemail"]["jwt_token"] = incoming_basic["freemail_jwt_token"]
    if "freemail_verify_ssl" in incoming_basic:
        refresh_settings["freemail"]["verify_ssl"] = incoming_basic["freemail_verify_ssl"]
    if "freemail_domain" in incoming_basic:
        refresh_settings["freemail"]["domain"] = incoming_basic["freemail_domain"]
    if "mail_proxy_enabled" in incoming_basic:
        refresh_settings["mail_proxy_enabled"] = incoming_basic["mail_proxy_enabled"]
    if "gptmail_base_url" in incoming_basic:
        refresh_settings["gptmail"]["base_url"] = incoming_basic["gptmail_base_url"]
    if "gptmail_api_key" in incoming_basic:
        refresh_settings["gptmail"]["api_key"] = incoming_basic["gptmail_api_key"]
    if "gptmail_verify_ssl" in incoming_basic:
        refresh_settings["gptmail"]["verify_ssl"] = incoming_basic["gptmail_verify_ssl"]
    if "gptmail_domain" in incoming_basic:
        refresh_settings["gptmail"]["domain"] = incoming_basic["gptmail_domain"]
    if "cfmail_base_url" in incoming_basic:
        refresh_settings["cfmail"]["base_url"] = incoming_basic["cfmail_base_url"]
    if "cfmail_api_key" in incoming_basic:
        refresh_settings["cfmail"]["api_key"] = incoming_basic["cfmail_api_key"]
    if "cfmail_verify_ssl" in incoming_basic:
        refresh_settings["cfmail"]["verify_ssl"] = incoming_basic["cfmail_verify_ssl"]
    if "cfmail_domain" in incoming_basic:
        refresh_settings["cfmail"]["domain"] = incoming_basic["cfmail_domain"]
    if "browser_mode" in incoming_basic:
        refresh_settings["browser_mode"] = incoming_basic["browser_mode"]
    if "browser_headless" in incoming_basic:
        refresh_settings["browser_headless"] = incoming_basic["browser_headless"]
    if "refresh_window_hours" in incoming_basic:
        refresh_settings["refresh_window_hours"] = incoming_basic["refresh_window_hours"]
    if "register_domain" in incoming_basic:
        refresh_settings["register_domain"] = incoming_basic["register_domain"]
    if "register_default_count" in incoming_basic:
        refresh_settings["register_default_count"] = incoming_basic["register_default_count"]

    for key in REFRESH_RETRY_KEYS:
        if key in incoming_retry:
            refresh_settings[key] = incoming_retry[key]

    return refresh_settings


def register_settings_routes(app: FastAPI, deps: SettingsRouteDeps) -> None:
    @app.get("/admin/settings")
    @deps.require_login()
    async def admin_get_settings(request: Request):
        current_config = deps.get_config()
        return {
            "basic": {
                "api_key": current_config.basic.api_key,
                "base_url": current_config.basic.base_url,
                "proxy_for_chat": current_config.basic.proxy_for_chat,
                "image_expire_hours": current_config.basic.image_expire_hours,
                "proxy_for_auth": current_config.basic.proxy_for_auth,
                "duckmail_base_url": current_config.basic.duckmail_base_url,
                "duckmail_api_key": current_config.basic.duckmail_api_key,
                "duckmail_verify_ssl": current_config.basic.duckmail_verify_ssl,
                "temp_mail_provider": current_config.basic.temp_mail_provider,
                "moemail_base_url": current_config.basic.moemail_base_url,
                "moemail_api_key": current_config.basic.moemail_api_key,
                "moemail_domain": current_config.basic.moemail_domain,
                "freemail_base_url": current_config.basic.freemail_base_url,
                "freemail_jwt_token": current_config.basic.freemail_jwt_token,
                "freemail_verify_ssl": current_config.basic.freemail_verify_ssl,
                "freemail_domain": current_config.basic.freemail_domain,
                "mail_proxy_enabled": current_config.basic.mail_proxy_enabled,
                "gptmail_base_url": current_config.basic.gptmail_base_url,
                "gptmail_api_key": current_config.basic.gptmail_api_key,
                "gptmail_verify_ssl": current_config.basic.gptmail_verify_ssl,
                "gptmail_domain": current_config.basic.gptmail_domain,
                "cfmail_base_url": current_config.basic.cfmail_base_url,
                "cfmail_api_key": current_config.basic.cfmail_api_key,
                "cfmail_verify_ssl": current_config.basic.cfmail_verify_ssl,
                "cfmail_domain": current_config.basic.cfmail_domain,
                "browser_mode": current_config.basic.browser_mode,
                "browser_headless": current_config.basic.browser_headless,
                "refresh_window_hours": current_config.basic.refresh_window_hours,
                "register_domain": current_config.basic.register_domain,
                "register_default_count": current_config.basic.register_default_count,
            },
            "image_generation": {
                "enabled": current_config.image_generation.enabled,
                "supported_models": current_config.image_generation.supported_models,
                "output_format": current_config.image_generation.output_format,
            },
            "video_generation": {
                "output_format": current_config.video_generation.output_format,
            },
            "retry": {
                "max_account_switch_tries": current_config.retry.max_account_switch_tries,
                "rate_limit_cooldown_seconds": current_config.retry.rate_limit_cooldown_seconds,
                "text_rate_limit_cooldown_seconds": current_config.retry.text_rate_limit_cooldown_seconds,
                "images_rate_limit_cooldown_seconds": current_config.retry.images_rate_limit_cooldown_seconds,
                "videos_rate_limit_cooldown_seconds": current_config.retry.videos_rate_limit_cooldown_seconds,
                "session_cache_ttl_seconds": current_config.retry.session_cache_ttl_seconds,
                "auto_refresh_accounts_seconds": current_config.retry.auto_refresh_accounts_seconds,
                "scheduled_refresh_enabled": current_config.retry.scheduled_refresh_enabled,
                "scheduled_refresh_interval_minutes": current_config.retry.scheduled_refresh_interval_minutes,
                "scheduled_refresh_cron": current_config.retry.scheduled_refresh_cron,
                "verification_code_resend_count": current_config.retry.verification_code_resend_count,
                "refresh_batch_size": current_config.retry.refresh_batch_size,
                "refresh_batch_interval_minutes": current_config.retry.refresh_batch_interval_minutes,
                "refresh_cooldown_hours": current_config.retry.refresh_cooldown_hours,
                "delete_expired_accounts": current_config.retry.delete_expired_accounts,
                "auto_register_enabled": current_config.retry.auto_register_enabled,
                "min_account_count": current_config.retry.min_account_count,
            },
            "refresh_settings": _build_refresh_settings(current_config),
            "quota_limits": {
                "enabled": current_config.quota_limits.enabled,
                "text_daily_limit": current_config.quota_limits.text_daily_limit,
                "images_daily_limit": current_config.quota_limits.images_daily_limit,
                "videos_daily_limit": current_config.quota_limits.videos_daily_limit,
            },
            "public_display": {
                "logo_url": current_config.public_display.logo_url,
                "chat_url": current_config.public_display.chat_url,
            },
            "session": {
                "expire_hours": current_config.session.expire_hours,
            },
        }

    @app.put("/admin/settings")
    @deps.require_login()
    async def admin_update_settings(request: Request, new_settings: dict[str, Any] = Body(...)):
        runtime_state = deps.get_runtime_state()
        current_config = deps.get_config()
        new_settings = dict(new_settings)

        try:
            incoming_basic = dict(new_settings.get("basic") or {})
            basic = {
                "api_key": incoming_basic.get("api_key", current_config.basic.api_key),
                "base_url": incoming_basic.get("base_url", current_config.basic.base_url),
                "proxy_for_chat": incoming_basic.get("proxy_for_chat", current_config.basic.proxy_for_chat),
                "image_expire_hours": incoming_basic.get("image_expire_hours", current_config.basic.image_expire_hours),
            }

            incoming_retry = dict(new_settings.get("retry") or {})
            retry = {
                "max_account_switch_tries": incoming_retry.get("max_account_switch_tries", current_config.retry.max_account_switch_tries),
                "rate_limit_cooldown_seconds": incoming_retry.get("rate_limit_cooldown_seconds", current_config.retry.rate_limit_cooldown_seconds),
                "text_rate_limit_cooldown_seconds": incoming_retry.get("text_rate_limit_cooldown_seconds", current_config.retry.text_rate_limit_cooldown_seconds),
                "images_rate_limit_cooldown_seconds": incoming_retry.get("images_rate_limit_cooldown_seconds", current_config.retry.images_rate_limit_cooldown_seconds),
                "videos_rate_limit_cooldown_seconds": incoming_retry.get("videos_rate_limit_cooldown_seconds", current_config.retry.videos_rate_limit_cooldown_seconds),
                "session_cache_ttl_seconds": incoming_retry.get("session_cache_ttl_seconds", current_config.retry.session_cache_ttl_seconds),
            }

            incoming_refresh = dict(new_settings.get("refresh_settings") or {})
            incoming_refresh = {
                **_coerce_refresh_settings_from_legacy(incoming_basic, incoming_retry, current_config),
                **incoming_refresh,
            }

            basic, retry = _merge_refresh_settings(
                basic,
                retry,
                incoming_refresh,
                current_config,
            )

            new_settings["basic"] = basic
            new_settings["retry"] = retry

            image_generation = dict(new_settings.get("image_generation") or {})
            image_generation.setdefault("enabled", current_config.image_generation.enabled)
            image_generation.setdefault("supported_models", current_config.image_generation.supported_models)
            output_format = str(image_generation.get("output_format") or deps.config_manager.image_output_format).lower()
            image_generation["output_format"] = output_format if output_format in ("base64", "url") else "base64"
            new_settings["image_generation"] = image_generation

            video_generation = dict(new_settings.get("video_generation") or {})
            video_generation.setdefault("output_format", current_config.video_generation.output_format)
            video_output_format = str(video_generation.get("output_format") or deps.config_manager.video_output_format).lower()
            video_generation["output_format"] = video_output_format if video_output_format in ("html", "url", "markdown") else "html"
            new_settings["video_generation"] = video_generation

            quota_limits = dict(new_settings.get("quota_limits") or {})
            quota_limits.setdefault("enabled", current_config.quota_limits.enabled)
            quota_limits.setdefault("text_daily_limit", current_config.quota_limits.text_daily_limit)
            quota_limits.setdefault("images_daily_limit", current_config.quota_limits.images_daily_limit)
            quota_limits.setdefault("videos_daily_limit", current_config.quota_limits.videos_daily_limit)
            new_settings["quota_limits"] = quota_limits

            public_display = dict(new_settings.get("public_display") or {})
            public_display.setdefault("logo_url", current_config.public_display.logo_url)
            public_display.setdefault("chat_url", current_config.public_display.chat_url)
            new_settings["public_display"] = public_display

            session = dict(new_settings.get("session") or {})
            session.setdefault("expire_hours", current_config.session.expire_hours)
            new_settings["session"] = session

            old_proxy_for_chat = runtime_state["proxy_for_chat"]
            old_retry_policy = runtime_state["retry_policy"]
            old_session_cache_ttl_seconds = runtime_state["session_cache_ttl_seconds"]

            deps.config_manager.save_yaml(new_settings)
            deps.config_manager.reload()

            current_config = deps.get_config()
            new_runtime_state = dict(runtime_state)
            proxy_for_chat, no_proxy_chat = deps.parse_proxy_setting(current_config.basic.proxy_for_chat)
            new_runtime_state.update({
                "api_key": current_config.basic.api_key,
                "proxy_for_chat": proxy_for_chat,
                "base_url": current_config.basic.base_url,
                "logo_url": current_config.public_display.logo_url,
                "chat_url": current_config.public_display.chat_url,
                "image_generation_enabled": current_config.image_generation.enabled,
                "image_generation_models": current_config.image_generation.supported_models,
                "max_account_switch_tries": current_config.retry.max_account_switch_tries,
                "retry_policy": deps.build_retry_policy(),
                "session_cache_ttl_seconds": current_config.retry.session_cache_ttl_seconds,
                "session_expire_hours": current_config.session.expire_hours,
            })

            no_proxy = ",".join(filter(None, {no_proxy_chat}))
            if no_proxy:
                os.environ["NO_PROXY"] = no_proxy
            else:
                os.environ.pop("NO_PROXY", None)

            if old_proxy_for_chat != new_runtime_state["proxy_for_chat"]:
                deps.logger.info("[CONFIG] Proxy configuration changed, rebuilding HTTP clients")
                await runtime_state["http_client"].aclose()
                await runtime_state["http_client_chat"].aclose()
                new_runtime_state["http_client"] = deps.create_http_client(new_runtime_state["proxy_for_chat"])
                new_runtime_state["http_client_chat"] = deps.create_http_client(new_runtime_state["proxy_for_chat"])
                deps.get_multi_account_mgr().update_http_client(new_runtime_state["http_client"])

            retry_policy = new_runtime_state["retry_policy"]
            retry_changed = (
                old_retry_policy.cooldowns.text != retry_policy.cooldowns.text
                or old_retry_policy.cooldowns.images != retry_policy.cooldowns.images
                or old_retry_policy.cooldowns.videos != retry_policy.cooldowns.videos
                or old_session_cache_ttl_seconds != new_runtime_state["session_cache_ttl_seconds"]
            )

            if retry_changed:
                deps.logger.info("[CONFIG] Retry policy changed, updating account managers")
                multi_account_mgr = deps.get_multi_account_mgr()
                multi_account_mgr.cache_ttl = new_runtime_state["session_cache_ttl_seconds"]
                for account_mgr in multi_account_mgr.accounts.values():
                    account_mgr.apply_retry_policy(retry_policy)

            deps.apply_runtime_state(new_runtime_state)
            deps.logger.info("[CONFIG] Settings updated successfully")
            return {"status": "success", "message": "Settings saved and applied"}
        except Exception as exc:
            deps.logger.error(f"[CONFIG] Failed to update settings: {exc}")
            raise HTTPException(500, f"Failed to update settings: {exc}") from exc
