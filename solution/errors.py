"""错误码定义。

错误码一览（同时写入 result.json 的 error.code 字段）：

- E_PARSE                模式不符合正则语法（括号未闭合、量词无目标等）
- E_UNSUPPORTED_FEATURE  语法合法但超出可分析子集（反向引用、前后查找、
                         \\d \\w \\s 等预定义类、{m,n} 量词、锚点、'.' 等）
- E_INPUT_TOO_LONG       候选/指定输入超过配置的长度上限，未送入子进程
- E_TIMEOUT              子进程超过墙钟超时，已被终止并回收
- E_RE_COMPILE           标准库 re 在子进程内编译失败（与本工具解析器不一致时上报）
- E_CASE_SCHEMA          cases.json 结构不合法
- E_CASE_IO              引用的模式/输入文件读取失败
- E_INTERNAL             未预期内部错误（含子进程异常退出）
"""

E_PARSE = "E_PARSE"
E_UNSUPPORTED_FEATURE = "E_UNSUPPORTED_FEATURE"
E_INPUT_TOO_LONG = "E_INPUT_TOO_LONG"
E_TIMEOUT = "E_TIMEOUT"
E_RE_COMPILE = "E_RE_COMPILE"
E_CASE_SCHEMA = "E_CASE_SCHEMA"
E_CASE_IO = "E_CASE_IO"
E_INTERNAL = "E_INTERNAL"


class ParseError(Exception):
    """解析/子集检查错误。code 为 E_PARSE 或 E_UNSUPPORTED_FEATURE。"""

    def __init__(self, code, message, pos=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.pos = pos

    def to_dict(self):
        return {"code": self.code, "message": self.message, "position": self.pos}
