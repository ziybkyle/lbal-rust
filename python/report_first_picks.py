"""Render the imported external first-offer rates, grouped by kind and rarity."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RARE = [("common", "普通"), ("uncommon", "非凡"), ("rare", "稀有"),
        ("very_rare", "非常稀有"), ("none", "无品质/其他"), ("unknown", "未知")]
KIND = [("symbol", "符号"), ("item", "物品"), ("essence", "精华")]


def render(destination=ROOT / "data" / "首次选择率排名.html"):
    data = json.loads((ROOT / "data" / "external_stats.json").read_text(encoding="utf-8"))
    labels = json.loads((ROOT / "data" / "association_rules.json").read_text(encoding="utf-8"))["names"]
    groups = {}
    for name, row in data["rows"].items():
        kind = row["kind"]
        rarity = "essence" if kind == "essence" else row["rarity"]
        groups.setdefault((kind, rarity), []).append((name, row))
    sections, links = [], []
    for kind, kind_label in KIND:
        order = [("essence", "全部精华")] if kind == "essence" else RARE
        for rarity, rarity_label in order:
            entries = groups.get((kind, rarity), [])
            if not entries:
                continue
            section_id = kind + "-" + rarity
            title = f"{kind_label} · {rarity_label}" if kind != "essence" else rarity_label
            links.append(f'<a href="#{section_id}">{html.escape(title)}</a>')
            def key(entry):
                name, row = entry
                n = row.get("first_offer_n", 0) or 0
                k = row.get("first_pick_n", 0) or 0
                return (not bool(n), -(k / n if n else 0), -n, name)
            table = []
            for rank, (name, row) in enumerate(sorted(entries, key=key), 1):
                n, k = row.get("first_offer_n", 0) or 0, row.get("first_pick_n", 0) or 0
                label = labels.get(name, {}).get("display") or name
                rate = f"{100*k/n:.2f}%" if n else "—"
                rank_label = str(rank) if n else "—"
                table.append(f"<tr><td>{rank_label}</td><td>{html.escape(label)} <small>{html.escape(name)}</small></td>"
                             f"<td>{rate}</td><td>{k}</td><td>{n}</td></tr>")
            sections.append(f'<section id="{section_id}"><h2>{html.escape(title)}</h2>'
                            '<table><tr><th>组内排名</th><th>名称</th><th>首次选择率</th>'
                            '<th>首次选中</th><th>首次出现</th></tr>' + "".join(table) + "</table></section>")
    page = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>外部首次选择率排名</title>'
            '<style>body{font:15px/1.6 system-ui,"Microsoft YaHei";max-width:1000px;margin:24px auto;'
            'padding:0 20px;background:#10151d;color:#dfe8f2}a{color:#8cc8ff;margin-right:1em}'
            'table{border-collapse:collapse;width:100%;background:#19222e}th,td{border:1px solid #344253;'
            'padding:6px;text-align:left}th{background:#233348}small{color:#aab9c9}.note{background:#263241;padding:12px}</style>'
            '<body><h1>外部首次选择率排名</h1><p class="note">来源：用户提供的 94% 胜率报告中的进阶 20 汇总。'
            '首次选择率 = 某候选在每局首次出现时被选中的次数 ÷ 首次出现次数。'
            '符号和普通物品分别按品质分组，精华作为同一组；排名只在各组内有意义。'
            '此表是原始选择率，不包含本局正负关联、喂食或筛选调整；无样本显示“—”。'
            '数字是另一个策略的选择倾向，并不表示拿到该候选后的胜率。</p>'
            + "<nav>" + " ".join(links) + "</nav>" + "".join(sections) + "</body></html>")
    destination.write_text(page, encoding="utf-8")
    print(f"Wrote {len(data['rows'])} rows in {len(sections)} groups to {destination}")


if __name__ == "__main__":
    render()
