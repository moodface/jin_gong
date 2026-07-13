# ================================================================
# AI 服务 - DeepSeek 集成 (文本生成 + 情感分析)
# AI生成: API调用框架、Prompt模板、JSON响应解析
# 人工修改: 调味品行业Prompt工程优化、Markdown HTML转换引擎、
#           无API Key降级方案、结构化sections输出
# ================================================================

import httpx
import re
import json
from ..config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL


# AI生成: 情感分析Prompt基础结构
# 人工修改: JSON输出格式约束、异常处理、空Key回退
async def ai_sentiment_analysis(text: str) -> dict:
    if not DEEPSEEK_API_KEY:
        return {"sentiment": "neutral", "content_type": "other", "summary": ""}

    prompt = f"""分析以下调味品相关内容，返回JSON格式：
{{
  "sentiment": "positive/negative/neutral",
  "content_type": "测评/review/促销/promo/recipe/食谱/other",
  "summary": "15字以内摘要"
}}

内容：{text}"""

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
        )
        data = resp.json()
        content_str = data["choices"][0]["message"]["content"]
        try:
            return json.loads(content_str)
        except json.JSONDecodeError:
            return {"sentiment": "neutral", "content_type": "other", "summary": text[:15]}


def strip_md(text: str) -> str:
    """移除 Markdown 格式标记，保留纯文本"""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    return text


# AI生成: Markdown→Section解析器基础逻辑
# 人工修改: 图标映射表(各章节对应emoji)、HTML标签过滤、
#           **粗体**标记清除、空section处理
def parse_markdown_sections(md_text: str) -> list:
    """将 Markdown 文本解析为结构化 section 列表"""
    sections = []
    lines = md_text.strip().split("\n")

    current_title = ""
    current_items = []
    current_icon = ""

    icon_map = {
        "数据概览": "📊", "概览": "📊", "核心指标": "📊",
        "核心洞察": "💡", "洞察": "💡", "分析": "🔍",
        "行动建议": "🎯", "建议": "🎯", "推荐": "🎯",
        "预警": "⚠️", "风险": "⚠️", "告警": "🚨",
        "竞品": "🏪", "竞品动态": "🏪",
        "舆情": "💬", "情感": "💬",
        "流量": "📈", "趋势": "📈",
    }

    def flush_section():
        nonlocal current_title, current_items, current_icon
        if current_items:
            icon = current_icon
            for kw, ic in icon_map.items():
                if kw in current_title:
                    icon = ic
                    break
            if not icon:
                icon = "📌"
            sections.append({
                "title": current_title,
                "icon": icon,
                "items": [strip_md(item) for item in current_items],
            })
        current_title = ""
        current_items = []
        current_icon = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳过 HTML 标签行
        if line.startswith("<") and line.endswith(">"):
            continue

        # 标题行 (### / ## / #)
        if line.startswith("### ") or line.startswith("## ") or line.startswith("# "):
            flush_section()
            current_title = re.sub(r"^#+\s*", "", line)
            current_title = re.sub(r"<[^>]+>", "", current_title)
            continue

        # 列表项 (- / 1. / *)
        if re.match(r"^[\-\*\d]+[\.\)]\s", line):
            item = re.sub(r"^[\-\*\d]+[\.\)]\s*", "", line)
            current_items.append(item)
            continue

        # > 引用
        if line.startswith(">"):
            flush_section()
            quote = re.sub(r"^>\s*", "", line)
            sections.append({
                "title": "",
                "icon": "📝",
                "items": [strip_md(quote)],
            })
            continue

        # 跳过纯 HTML
        if re.match(r"^\s*<", line):
            continue

        # 普通文本
        current_items.append(line)

    flush_section()
    return sections


def build_html_report(content: str, title: str) -> str:
    """将 Markdown 转为适合 rich-text 的 HTML"""
    # 简单的 Markdown → HTML 转换
    html = f'<div style="padding:8px 0;">'
    html += f'<h2 style="color:#C8102E;text-align:center;margin-bottom:16px;font-size:18px;">{title}</h2>'

    lines = content.strip().split("\n")
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html += "</ul>"
                in_list = False
            html += '<div style="height:8px;"></div>'
            continue

        # 标题
        if line.startswith("### "):
            if in_list:
                html += "</ul>"
                in_list = False
            t = line[4:].strip()
            html += f'<h3 style="color:#333;font-size:15px;margin:12px 0 6px;border-left:3px solid #C8102E;padding-left:8px;">{t}</h3>'
            continue

        if line.startswith("## "):
            if in_list:
                html += "</ul>"
                in_list = False
            t = line[3:].strip()
            html += f'<h3 style="color:#C8102E;font-size:16px;margin:14px 0 8px;">{t}</h3>'
            continue

        # 列表
        if re.match(r"^[\-\*\d]+[\.\)]\s", line):
            if not in_list:
                html += '<ul style="padding-left:16px;margin:4px 0;">'
                in_list = True
            item_text = re.sub(r"^[\-\*\d]+[\.\)]\s*", "", line)
            # 加粗
            item_text = re.sub(r"\*\*(.*?)\*\*", r'<strong>\1</strong>', item_text)
            html += f'<li style="font-size:13px;color:#555;line-height:1.8;margin-bottom:4px;">{item_text}</li>'
            continue

        # 引用
        if line.startswith(">"):
            if in_list:
                html += "</ul>"
                in_list = False
            t = line[1:].strip()
            html += f'<div style="background:#FFFBE6;border-left:4px solid #FAAD14;padding:8px 12px;margin:8px 0;font-size:12px;color:#D48806;">{t}</div>'
            continue

        # 普通文本
        if in_list:
            html += "</ul>"
            in_list = False
        line = re.sub(r"\*\*(.*?)\*\*", r'<strong>\1</strong>', line)
        html += f'<p style="font-size:13px;color:#555;line-height:1.8;margin:2px 0;">{line}</p>'

    if in_list:
        html += "</ul>"

    html += '<div style="border-top:1px solid #eee;margin-top:16px;padding-top:8px;text-align:center;font-size:11px;color:#999;">金宫味业数字营销数据中台 · AI 自动生成</div>'
    html += "</div>"
    return html


async def ai_generate_report(report_type: str, dashboard_data: dict) -> str:
    """生成报告，返回原始 Markdown 文本"""
    if not DEEPSEEK_API_KEY:
        title = "金宫味业" + ("日报" if report_type == "daily" else "周报")
        return f"""## {title}

> 当前未配置 AI API Key，以下为模板数据。

### 数据概览
- **总 GMV**: ¥{dashboard_data.get('total_gmv', 1286000):,.0f}
- **更新时间**: {dashboard_data.get('update_time', 'N/A')}

### 核心洞察
- 各平台流量分布正常，抖音为最大流量来源
- 竞品「千禾」零添加系列价格稳定在 ¥15-20 区间
- 舆情分析显示「有机酱油」话题正面率占比超 60%

### 行动建议
- 持续关注竞品「海天」的促销节奏，及时调整价格策略
- 加大对「零添加」关键词的社交媒体投放力度
- 建议在抖音平台增加 KOL 测评合作内容

### 预警提示
- 海天金标生抽在京东平台有「买二送一」促销
- 「减盐」话题近期负面舆情占比上升至 18%
"""

    title = "金宫味业" + ("日报" if report_type == "daily" else "周报")
    prompt = f"""你是金宫味业的数据分析师，请生成一份专业美观的{title}。

要求：
1. 使用 Markdown 格式（## ### -），分成以下四个章节
2. **数据概览**：用 2-3 条要点总结核心指标
3. **核心洞察**：3 条有价值的分析发现
4. **行动建议**：3 条可执行的运营建议
5. **预警提示**（如果有）：值得关注的异常信号

重要格式规则：
- 要点一律用 - 开头，每条要点前用 **关键词** 加粗
- 数值要带单位（万、%、元）
- 语言简洁专业，适合移动端阅读

数据：
{str(dashboard_data)[:3000]}"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices")
                if choices and len(choices) > 0:
                    return choices[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"[AI] DeepSeek API 调用失败: {e}，回退到模板报告")

    # 任何异常或 Key 无效时，返回本地模板报告（不走网络）
    return f"""## {title}

> 当前使用本地模板报告（无有效 AI API Key）

### 数据概览
- **总 GMV**: ¥{dashboard_data.get('total_gmv', 1286000):,.0f}
- **更新时间**: {dashboard_data.get('update_time', 'N/A')}

### 核心洞察
- 各平台流量分布正常，抖音为最大流量来源
- 竞品「千禾」零添加系列价格稳定在 ¥15-20 区间
- 舆情分析显示「有机酱油」话题正面率占比超 60%

### 行动建议
- 持续关注竞品「海天」的促销节奏，及时调整价格策略
- 加大对「零添加」关键词的社交媒体投放力度
- 建议在抖音平台增加 KOL 测评合作内容

### 预警提示
- 海天金标生抽在京东平台有「买二送一」促销
- 「减盐」话题近期负面舆情占比上升至 18%
"""


async def ai_generate_report_structured(report_type: str, dashboard_data: dict) -> dict:
    """返回结构化数据，供前端卡片式渲染"""
    markdown = await ai_generate_report(report_type, dashboard_data)
    sections = parse_markdown_sections(markdown)
    title = "金宫味业" + ("日报" if report_type == "daily" else "周报")
    html = build_html_report(markdown, title)
    return {
        "html": html,
        "sections": sections,
    }
