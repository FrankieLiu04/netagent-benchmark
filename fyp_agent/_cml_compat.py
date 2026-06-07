"""CML 2.7 兼容适配层 — 修补 cml-mcp 0.28 Pydantic 模型，使其兼容 CML 2.7 API。

CML 2.7.x 服务器不返回以下字段（CML 2.8+ 才有），
但 cml-mcp 0.28 的 Pydantic 模型将它们声明为必填。
此模块通过 import hook 在 cml_mcp 模块加载时，
将缺失字段的 Field(...) 改为 Field(default=xxx)，从而避免 ValidationError。

用法：python _cml_compat.py
cml-mcp 和 virl2-client 必须已安装在当前 Python 环境中。
CML 连接凭据通过环境变量传入（CML_URL, CML_USERNAME, CML_PASSWORD, CML_VERIFY_SSL）。
"""

from __future__ import annotations

import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Any

from pydantic.fields import PydanticUndefined

# ── 声明式补丁表 ─────────────────────────────────────────────────────────────
# 格式: (模块全名, 模型类名, 字段名, 默认值, 补丁原因)
# 注意：必须指向模型定义所在的 schema 模块，而非 import 它们的 tools 模块。
# schema 模块先被加载（类在此初始化），tools 模块随后 import 引用。
_PATCH_TABLE: list[tuple[str, str, str, Any, str]] = [
    (
        "cml_mcp.cml.simple_webserver.schemas.system",
        "SystemInformation",
        "allow_ssh_pubkey_auth",
        False,
        "CML 2.7 不返回 SSH 公钥认证开关（CML 2.8+ 新增）",
    ),
    (
        "cml_mcp.cml.simple_webserver.schemas.system",
        "SystemInformation",
        "oui",
        None,
        "CML 2.7 不返回 MAC OUI 前缀（CML 2.8+ 新增）",
    ),
    (
        "cml_mcp.cml.simple_webserver.schemas.system",
        "ComputeHealth",
        "docker_shim",
        None,
        "CML 2.7 不返回容器服务 docker_shim 健康状态（CML 2.8+ 新增）",
    ),
    (
        "cml_mcp.cml.simple_webserver.schemas.labs",
        "Lab",
        "effective_permissions",
        None,
        "CML 2.7 不返回当前用户的有效权限列表（CML 2.8+ 新增）",
    ),
]

# 已修补的模块集合，避免重复修补
_seen: set[str] = set()


# ── 补丁应用 ─────────────────────────────────────────────────────────────────

def _apply_patch(module: ModuleType, module_name: str) -> None:
    """对指定模块中的 Pydantic 模型应用声明式补丁。

    遍历 _PATCH_TABLE 中找到目标模块的所有补丁项，
    将对应模型中必填字段的默认值补上，然后重建模型。
    """
    if module_name in _seen:
        return
    _seen.add(module_name)

    for mod_name, model_name, field_name, default, _reason in _PATCH_TABLE:
        if mod_name != module_name:
            continue
        model = getattr(module, model_name, None)
        if model is None:
            continue
        field_info = model.model_fields.get(field_name)
        # Pydantic v2 必填字段的 default 是 PydanticUndefined，不是 Ellipsis
        if field_info is not None and field_info.default is PydanticUndefined and field_info.default_factory is None:
            field_info.default = default
            model.model_rebuild(force=True)


# ── Import Hook ──────────────────────────────────────────────────────────────

class _PatchingLoader(Loader):
    """加载器包装器 — 在目标模块 exec 后自动应用补丁。"""

    def __init__(self, orig: Loader, mod_name: str) -> None:
        self._orig = orig
        self._mod = mod_name

    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        if hasattr(self._orig, "create_module"):
            return self._orig.create_module(spec)
        return None

    def exec_module(self, module: ModuleType) -> None:
        if hasattr(self._orig, "exec_module"):
            self._orig.exec_module(module)
        _apply_patch(module, self._mod)


class _Finder(MetaPathFinder):
    """Import hook 查找器 — 拦截 _PATCH_TABLE 中列出的模块的加载。"""

    def find_spec(self, fullname: str, path, target=None) -> ModuleSpec | None:
        # 仅拦截补丁表中声明的模块
        if fullname not in {entry[0] for entry in _PATCH_TABLE}:
            return None
        # 使用 PathFinder 直接查找，绕过 sys.meta_path 避免无限递归
        from importlib.machinery import PathFinder

        spec = PathFinder.find_spec(fullname, path, target)
        if spec is not None and spec.loader is not None:
            spec.loader = _PatchingLoader(spec.loader, fullname)
        return spec


# 在模块被 import 前安装 hook（必须在其他 cml_mcp import 之前）
sys.meta_path.insert(0, _Finder())


# ── 入口 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    """启动 cml-mcp stdio MCP 服务器（延迟 import 避免副作用）。"""
    from cml_mcp.__main__ import main as cml_main

    cml_main()


if __name__ == "__main__":
    main()
