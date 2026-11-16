"""正则安全审查器与隔离执行器（日志过滤服务用）。

模块组成：
- parser       支持子集的正则解析器（字面量/字符类/连接/分支/捕获组/*+?）
- analyzer     可解释的重叠重复（回溯爆炸）静态风险分析
- nfa          不回溯的 Thompson NFA 匹配器（fullmatch 语义）
- runner       独立子进程中执行标准库 re 的隔离执行器（墙钟超时+长度上限）
- equivalence  NFA 与 re 的有界穷举语义一致性验证
- cli          python -m solution 入口
"""

__version__ = "1.0.0"
SCHEMA_VERSION = 1
