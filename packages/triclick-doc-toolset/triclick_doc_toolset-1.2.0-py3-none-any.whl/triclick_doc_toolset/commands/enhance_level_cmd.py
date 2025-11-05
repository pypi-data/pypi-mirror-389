from __future__ import annotations

from typing import Any

# 框架依赖
from triclick_doc_toolset.framework import Command, Context, CommandRegistry


class EnhanceLevelCommand(Command):
    """
    规范化 sections 的 level：
    - 若所有 section 的 level 均为 0，则将它们统一调整为 1；
    - 仅在 context.sections 非空时生效；
    - 不区分 doc_type，作为解析后的泛用后处理。
    """

    def is_satisfied(self, context: Context) -> bool:
        return bool(context.sections)

    def execute(self, context: Context) -> Context:
        sections = context.sections or []
        if not sections:
            # 不作为错误，仅记录摘要
            context.processing_summary["section_level_enhancement"] = {
                "applied": False,
                "reason": "no_sections"
            }
            return context

        def _to_int_level(val: Any) -> int:
            try:
                return int(val)
            except Exception:
                return 0

        levels = [_to_int_level(s.get("level", 0)) for s in sections]
        if sections and all(l == 0 for l in levels):
            for s in sections:
                s["level"] = 1
            context.processing_summary["section_level_enhancement"] = {
                "applied": True,
                "updated_count": len(sections),
                "rule": "all_zero->set_one",
            }
        else:
            context.processing_summary["section_level_enhancement"] = {
                "applied": False,
                "reason": "mixed_or_non_zero_levels",
            }
        return context

# 注册到命令注册表
CommandRegistry.register("EnhanceLevelCommand", EnhanceLevelCommand)