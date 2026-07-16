def build_prompt_by_level(code: str, language: str, explain_level: str) -> str:
    level_map = {
        "简单解释": "simple",
        "详细解释": "normal",
        "教学式解释": "detailed",
    }
    level = level_map.get(explain_level, "normal")

    if level == "simple":
        return _build_simple_prompt(code, language)
    elif level == "normal":
        return _build_normal_prompt(code, language)
    else:
        return _build_detailed_prompt(code, language)


def _build_simple_prompt(code: str, language: str) -> str:
    return f"""你是一个编程老师。用户是初学者。

请用简洁、清楚的方式解释下面这段代码。不要写成长篇教程，只解释最重要的内容。

代码语言：{language}

代码如下：
```{language}
{code}
```

输出结构：
## 这段代码整体在做什么
## 分块解释
## 一个相似小例子
## 常见错误
"""


def _build_normal_prompt(code: str, language: str) -> str:
    return f"""你是一个循循善诱的编程老师。

请解释下面这段代码，帮助初学者真正理解。内容要比简单解释更完整，但不要过度展开。重点解释代码含义、语法和运行逻辑。

代码语言：{language}

代码如下：
```{language}
{code}
```

输出结构：
## 代码整体作用
## 代码分块解释
## 关键语法说明
## 相似例子
## 相关知识拓展
## 小练习
"""


def _build_detailed_prompt(code: str, language: str) -> str:
    return f"""你是一个非常耐心的编程导师。

请深入解释下面这段代码，帮助用户从代码理解扩展到相关知识体系。可以详细解释，但要深入浅出，不要废话。多举例，但例子要短。

代码语言：{language}

代码如下：
```{language}
{code}
```

输出结构：
## 代码整体作用
## 逐块详细解释
## 关键语法和底层逻辑
## 相似例子
## 相关知识体系
## 工程应用场景
## 常见错误
## 练习任务
"""
