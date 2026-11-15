"""Compare two observations per SKU and write a price/availability report."""
import argparse, csv, json
from collections import defaultdict
from pathlib import Path

def compare(path: Path):
    grouped=defaultdict(list)
    with path.open(newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f): grouped[row['sku']].append(row)
    changes=[]
    for sku, rows in grouped.items():
        rows.sort(key=lambda r:r['observed_at'])
        if len(rows)<2: continue
        old,new=rows[-2],rows[-1]
        before,after=float(old['price']),float(new['price'])
        changes.append({'sku':sku,'product_name':new['product_name'],'previous_price':f'{before:.2f}','current_price':f'{after:.2f}','change_amount':f'{after-before:.2f}','change_percent':f'{((after-before)/before*100):.2f}' if before else '', 'previous_availability':old['availability'],'current_availability':new['availability'],'observed_at':new['observed_at'],'source_url':new['source_url']})
    return changes

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=Path(__file__).parent/'data'/'price_history.csv');p.add_argument('--output-dir',type=Path,default=Path(__file__).parent/'output');a=p.parse_args()
    rows=compare(a.input);a.output_dir.mkdir(parents=True,exist_ok=True)
    if rows:
        with (a.output_dir/'price-changes.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        (a.output_dir/'price-changes.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    summary=['# Demonstration price-change report','', '> Synthetic sample history for workflow testing; not live market prices.','',f'- SKUs compared: **{len(rows)}**',f'- Price decreases: **{sum(float(r["change_amount"])<0 for r in rows)}**',f'- Price increases: **{sum(float(r["change_amount"])>0 for r in rows)}**',f'- Availability changes: **{sum(r["previous_availability"]!=r["current_availability"] for r in rows)}**','','| Product | Previous | Current | Change | Availability |','|---|---:|---:|---:|---|']
    for r in rows: summary.append(f"| {r['product_name']} | {r['previous_price']} | {r['current_price']} | {r['change_amount']} ({r['change_percent']}%) | {r['previous_availability']} → {r['current_availability']} |")
    (a.output_dir/'price-report.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')
    print(f'Compared {len(rows)} SKUs. Wrote price-change report to {a.output_dir}')
if __name__=='__main__': main()
