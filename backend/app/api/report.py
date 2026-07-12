from fastapi import APIRouter
from datetime import datetime
from ..database import get_db
from ..models.schemas import ReportRequest, ReportResponse
from ..services.ai_service import ai_generate_report, ai_generate_report_structured
from ..config import COMPETITOR_BRANDS

router = APIRouter(prefix="/api/report", tags=["report"])


def _get_dashboard_data():
    conn = get_db()
    data = {
        "total_gmv": 1286000,
        "update_time": datetime.now().isoformat(),
    }
    rows = conn.execute(
        "SELECT platform, COUNT(*) as cnt FROM platform_data GROUP BY platform"
    ).fetchall()
    for r in rows:
        data[f"{r['platform']}_count"] = r["cnt"]

    # 竞品数据
    comp_rows = conn.execute(
        "SELECT brand, COUNT(*) as cnt, AVG(price) as avg_price FROM competitor_monitor GROUP BY brand"
    ).fetchall()
    data["competitors"] = [dict(r) for r in comp_rows]

    # 舆情数据
    sent_rows = conn.execute(
        "SELECT keyword, SUM(mention_count) as total FROM sentiment_trend GROUP BY keyword ORDER BY total DESC LIMIT 5"
    ).fetchall()
    data["sentiments"] = [dict(r) for r in sent_rows]

    conn.close()
    return data


@router.post("/generate")
async def generate_report(req: ReportRequest):
    dashboard_data = _get_dashboard_data()
    result = await ai_generate_report_structured(req.report_type, dashboard_data)
    import json
    sections_str = json.dumps(result["sections"], ensure_ascii=False)

    conn = get_db()
    conn.execute(
        "INSERT INTO report_history (report_type, content, sections_json) VALUES (?,?,?)",
        (req.report_type, result["html"], sections_str)
    )
    conn.commit()
    conn.close()

    return {
        "content": result["html"],
        "sections": result["sections"],
        "report_type": req.report_type,
        "generated_time": datetime.now().isoformat(),
    }


@router.get("/history")
def get_report_history():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM report_history ORDER BY generated_time DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "type": r["report_type"], "content": r["content"][:200], "time": r["generated_time"]} for r in rows]


@router.get("/{report_id}")
def get_report_detail(report_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM report_history WHERE id=?", (report_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {"error": "报告不存在"}

    import json
    sections = []
    if row["sections_json"]:
        try:
            sections = json.loads(row["sections_json"])
        except:
            pass

    return {
        "id": row["id"],
        "type": row["report_type"],
        "content": row["content"],
        "sections": sections,
        "generated_time": row["generated_time"],
    }
