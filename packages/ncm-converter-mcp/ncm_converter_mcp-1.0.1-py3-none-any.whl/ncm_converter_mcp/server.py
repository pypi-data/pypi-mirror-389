#!/usr/bin/env python3
"""
网易云音乐 NCM 音频文件转换 MCP Server (stdio 版)

使用标准 mcp.server.stdio Server，以确保与 Cherry 等 stdio 客户端兼容。
提供两个工具：convert_ncm、batch_convert。
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# ---------- 日志配置（关闭多余输出，避免干扰 stdio） ----------
logger = logging.getLogger("ncm_converter_mcp")
logger.propagate = False
logger.handlers.clear()
logger.setLevel(logging.WARNING)

# -------------- 通用工具函数 --------------

def _resolve_path(p: str | None) -> Optional[str]:
    if not p:
        return None
    return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))


def _ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _list_files(directory: str) -> List[str]:
    try:
        return [str(p) for p in Path(directory).iterdir() if p.is_file()]
    except Exception as e:
        logger.error(f"List files failed for directory={directory}: {e}")
        return []


def _convert_ncm_direct(input_path: str, out_folder: str) -> tuple[int, str, str]:
    """直接使用 ncmdump 库进行解密转换，返回 (returncode, stdout, stderr)"""
    logger.info(f"Direct convert start: src={input_path}, out={out_folder}")
    try:
        from ncmdump import NeteaseCloudMusicFile
    except Exception as e:
        logger.exception("Import ncmdump failed")
        return 1, "", f"ImportError: {e}"

    try:
        src = Path(input_path)
        out_dir = Path(out_folder)
        out_dir.mkdir(parents=True, exist_ok=True)
        # 初始输出名以 .mp3 结尾，库会自动纠正为真实后缀
        output_path = out_dir / src.with_suffix('.mp3').name
        ncmfile = NeteaseCloudMusicFile(str(src)).decrypt()
        music_path = ncmfile.dump_music(str(output_path))
        logger.info(f"Direct convert ok: {src} -> {music_path}")
        return 0, f"Output: {music_path}", ""
    except Exception as e:
        logger.exception(f"Direct convert failed: {e}")
        return 1, "", str(e)


def _collect_new_files(out_folder: str, before: set[str]) -> List[str]:
    after = set(_list_files(out_folder))
    new_files = sorted(list(after - before))
    logger.info(f"Generated files: {new_files}")
    return new_files

# -------------- MCP Server --------------
server = Server("ncm-converter-mcp")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    logger.info("List tools requested")
    return [
        types.Tool(
            name="convert_ncm",
            description="将单个 .ncm 文件转换为标准音频文件（mp3/flac/ape/wav 等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要转换的 .ncm 文件绝对路径"},
                    "out_folder": {"type": "string", "description": "输出目录（可选）"},
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="batch_convert",
            description="批量转换 .ncm 文件（文件或目录；目录可递归）",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {"type": "string", "description": "文件或目录绝对路径"},
                    "out_folder": {"type": "string", "description": "输出目录（可选）"},
                    "recursive": {"type": "boolean", "description": "目录是否递归查找 .ncm"},
                },
                "required": ["input_path"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    arguments = arguments or {}
    logger.info(f"Call tool: name={name}, arguments={arguments}")

    def as_text(payload: Dict[str, Any]) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]

    try:
        if name == "convert_ncm":
            file_path = arguments.get("file_path")
            out_folder = arguments.get("out_folder")

            if not file_path:
                raise ValueError("file_path is required")
            src = _resolve_path(file_path)
            if not src or not os.path.isfile(src):
                raise FileNotFoundError(f"未找到文件: {file_path}")
            if not src.lower().endswith(".ncm"):
                raise ValueError("仅支持 .ncm 文件")

            out_dir = _resolve_path(out_folder) if out_folder else os.path.join(os.path.dirname(src), "output")
            _ensure_dir(out_dir)
            logger.info(f"Converting: src={src}, out_dir={out_dir}")

            before = set(_list_files(out_dir))
            # 在线程中执行，避免阻塞事件循环
            code, out, err = await asyncio.to_thread(_convert_ncm_direct, src, out_dir)
            new_files = _collect_new_files(out_dir, before)

            if code != 0:
                raise RuntimeError(f"转换失败\n{err}")

            return as_text({
                "status": "success",
                "input": src,
                "output_dir": out_dir,
                "generated_files": new_files,
                "message": "NCM 转换完成"
            })

        elif name == "batch_convert":
            input_path = arguments.get("input_path")
            out_folder = arguments.get("out_folder")
            recursive = bool(arguments.get("recursive", False))

            if not input_path:
                raise ValueError("input_path is required")
            inp = _resolve_path(input_path)
            if not inp or not os.path.exists(inp):
                raise FileNotFoundError(f"路径不存在: {input_path}")

            results: List[Dict[str, Any]] = []
            base_out = _resolve_path(out_folder) if out_folder else None
            if base_out:
                _ensure_dir(base_out)
            logger.info(f"Batch convert: base_out={base_out}, recursive={recursive}")

            def convert_one(ncm_file: str) -> Dict[str, Any]:
                out_dir = base_out or os.path.join(os.path.dirname(ncm_file), "output")
                _ensure_dir(out_dir)
                before = set(_list_files(out_dir))
                code, out, err = _convert_ncm_direct(ncm_file, out_dir)
                new_files = _collect_new_files(out_dir, before)
                ok = code == 0
                if not ok:
                    logger.error(f"Convert failed for {ncm_file}: {err}")
                return {
                    "input": ncm_file,
                    "ok": ok,
                    "output_dir": out_dir,
                    "generated_files": new_files,
                    "stdout": out,
                    "stderr": err,
                }

            if os.path.isfile(inp):
                if not inp.lower().endswith(".ncm"):
                    raise ValueError("当 input_path 为文件时，必须是 .ncm 文件")
                results.append(await asyncio.to_thread(convert_one, inp))
            else:
                pattern = "**/*.ncm" if recursive else "*.ncm"
                files = [str(p) for p in Path(inp).glob(pattern) if p.is_file()]
                if not files:
                    raise FileNotFoundError("未在目录中找到 .ncm 文件")
                # 顺序执行，避免同时写同一输出目录带来的冲突
                for f in files:
                    results.append(await asyncio.to_thread(convert_one, f))

            success_count = sum(1 for r in results if r.get("ok"))
            fail_count = len(results) - success_count
            status = "success" if fail_count == 0 else ("partial" if success_count > 0 else "failed")

            return as_text({
                "status": status,
                "total": len(results),
                "success": success_count,
                "failed": fail_count,
                "results": results
            })

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        # 让客户端看到明确的错误文本，同时写 ERROR 日志
        logger.exception(f"Tool '{name}' failed: {e}")
        return [types.TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def run():
    logger.info("Starting stdio server...")
    logger.info(f"Environment PYTHONPATH={os.getenv('PYTHONPATH')}")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Streams established, running MCP server...")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ncm-converter-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt: server stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
