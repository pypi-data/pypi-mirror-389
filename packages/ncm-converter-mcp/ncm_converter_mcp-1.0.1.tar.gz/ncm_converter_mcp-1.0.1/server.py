#!/usr/bin/env python3
"""
网易云音乐 NCM 音频文件转换 MCP Server

基于 ncmdump-py，将 .ncm 文件解密为标准音频格式（mp3/flac/ape/wav 等，具体取决于源文件封装）。
- 需要先在系统环境里可用 `python -m ncmdump`（已通过 pip 安装 ncmdump-py）。
- 提供单文件转换与目录批量转换两个工具。
"""

from __future__ import annotations

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context

mcp = FastMCP("NCM Converter MCP Server")

# 关闭多余日志，仅保留 WARNING 级别（通过 ctx 输出必要信息）
logger = logging.getLogger("ncm_converter_fastmcp")
logger.propagate = False
logger.handlers.clear()
logger.setLevel(logging.WARNING)


def _resolve_path(p: str | None) -> Optional[str]:
    if not p:
        return None
    return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))


def _ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _list_files(directory: str) -> List[str]:
    try:
        return [str(p) for p in Path(directory).iterdir() if p.is_file()]
    except Exception:
        return []


def _convert_ncm_direct(input_path: str, out_folder: str, ctx: Optional[Context]) -> tuple[int, str, str]:
    """直接使用 ncmdump 库进行转换 (returncode, stdout, stderr)"""
    try:
        from ncmdump import NeteaseCloudMusicFile
    except Exception as e:
        msg = f"ImportError: {e}"
        logger.error(msg)
        if ctx:
            ctx.error(msg)
        return 1, "", msg

    try:
        src = Path(input_path)
        out_dir = Path(out_folder)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / src.with_suffix('.mp3').name
        ncmfile = NeteaseCloudMusicFile(str(src)).decrypt()
        music_path = ncmfile.dump_music(str(output_path))
        ok_msg = f"转换成功: {src.name} -> {music_path}"
        logger.info(ok_msg)
        if ctx:
            ctx.info(ok_msg)
        return 0, ok_msg, ""
    except Exception as e:
        err = f"转换异常: {e}"
        logger.exception(err)
        if ctx:
            ctx.error(err)
        return 1, "", err


def _collect_new_files(out_folder: str, before: set[str]) -> List[str]:
    after = set(_list_files(out_folder))
    new_files = sorted(list(after - before))
    return new_files


@mcp.tool()
def convert_ncm(
    file_path: str,
    out_folder: Optional[str] = None,
    ctx: Context | None = None,
) -> str:
    """
    将单个 .ncm 文件转换为标准音频文件。
    参数:
    - file_path: 绝对路径 .ncm 文件
    - out_folder: 输出目录（可选，默认与输入文件同目录的 output 子目录）

    返回 JSON 字符串，包含输出目录与新生成的文件列表。
    """
    try:
        if not file_path:
            raise ValueError("file_path 不能为空")
        src = _resolve_path(file_path)
        if not src or not os.path.isfile(src):
            raise FileNotFoundError(f"未找到文件: {file_path}")
        if not src.lower().endswith(".ncm"):
            raise ValueError("仅支持 .ncm 文件")

        if out_folder:
            out_dir = _resolve_path(out_folder)
        else:
            # 默认输出到同级目录下的 output/
            out_dir = os.path.join(os.path.dirname(src), "output")
        _ensure_dir(out_dir)

        before = set(_list_files(out_dir))
        code, out, err = _run_ncmdump(src, out_dir, ctx)
        new_files = _collect_new_files(out_dir, before)

        if code != 0:
            msg = "转换失败"
            if err:
                msg += f"\n{err}"
            raise RuntimeError(msg)

        if ctx:
            ctx.info(f"转换完成，输出目录: {out_dir}")
            for f in new_files:
                ctx.info(f"生成: {Path(f).name}")

        return json.dumps({
            "status": "success",
            "input": src,
            "output_dir": out_dir,
            "generated_files": new_files,
            "message": "NCM 转换完成"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        raise


@mcp.tool()
def batch_convert(
    input_path: str,
    out_folder: Optional[str] = None,
    recursive: bool = False,
    ctx: Context | None = None,
) -> str:
    """
    批量转换 .ncm 文件。
    - input_path: 可以是文件或目录（绝对路径）。
    - out_folder: 输出目录（可选）。
    - recursive: 若 input_path 为目录时，是否递归查找 .ncm。

    返回 JSON 字符串，包含每个条目的转换结果。
    """
    try:
        inp = _resolve_path(input_path)
        if not inp or not os.path.exists(inp):
            raise FileNotFoundError(f"路径不存在: {input_path}")

        results: List[Dict[str, Any]] = []

        # 确定输出目录
        base_out = _resolve_path(out_folder) if out_folder else None
        if base_out:
            _ensure_dir(base_out)

        def convert_one(ncm_file: str) -> Dict[str, Any]:
            out_dir = base_out or os.path.join(os.path.dirname(ncm_file), "output")
            _ensure_dir(out_dir)
            before = set(_list_files(out_dir))
            code, out, err = _convert_ncm_direct(ncm_file, out_dir, ctx)
            new_files = _collect_new_files(out_dir, before)
            ok = code == 0
            if ctx:
                ctx.info(("✅" if ok else "❌") + f" {Path(ncm_file).name}")
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
            results.append(convert_one(inp))
        else:
            pattern = "**/*.ncm" if recursive else "*.ncm"
            files = [str(p) for p in Path(inp).glob(pattern) if p.is_file()]
            if not files:
                raise FileNotFoundError("未在目录中找到 .ncm 文件")
            for f in files:
                results.append(convert_one(f))

        success_count = sum(1 for r in results if r.get("ok"))
        fail_count = len(results) - success_count

        return json.dumps({
            "status": "success" if fail_count == 0 else "partial",
            "total": len(results),
            "success": success_count,
            "failed": fail_count,
            "results": results
        }, ensure_ascii=False, indent=2)

    except Exception:
        raise


@mcp.prompt()
def ncm_convert_guide() -> str:
    return (
        """
# 网易云音乐 NCM 转换 MCP 使用指南

## 工具
- convert_ncm(file_path, out_folder?): 转换单个 .ncm 文件
- batch_convert(input_path, out_folder?, recursive=false): 批量转换（input_path 可为文件或目录）

## 先决条件
- 系统已安装并可运行：python -m ncmdump
- Windows/ macOS/ Linux 通用。

## 示例
1) 单文件：
convert_ncm(
  file_path="C:/Users/you/Downloads/song.ncm",
  out_folder="C:/Users/you/Downloads/output"
)

2) 目录批量（递归）：
batch_convert(
  input_path="C:/Users/you/Downloads/ncm_folder",
  out_folder="C:/Users/you/Downloads/output",
  recursive=true
)
        """
    ).strip()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
