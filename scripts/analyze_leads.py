#!/usr/bin/env python3
"""Analyze leads in Convex for cleanup."""
import json, subprocess, sys
from urllib.parse import urlparse

# Fetch paginated
all_leads = []
cursor = None
while True:
    args = {}
    if cursor:
        args['cursor'] = cursor
    result = subprocess.run(
        ['npx', 'convex', 'run', 'leads:listPaginated', json.dumps(args)],
        capture_output=True, text=True, cwd='/Users/manfredbellmann/.openclaw/workspace/mannileads'
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr[:500]}")
        break
    data = json.loads(result.stdout)
    if isinstance(data, dict):
        all_leads.extend(data.get('leads', data.get('page', [])))
        cursor = data.get('cursor') or data.get('continueCursor')
        if not cursor or data.get('isDone'):
            break
    elif isinstance(data, list):
        all_leads.extend(data)
        break
    else:
        break

print(f'Total leads fetched: {len(all_leads)}')

no_email = [l for l in all_leads if not l.get('email') or l['email'].strip() == '']
with_email = [l for l in all_leads if l.get('email') and l['email'].strip()]
print(f'With email: {len(with_email)}')
print(f'Without email: {len(no_email)}')

# Domain analysis
domain_data = {}
for l in all_leads:
    url = l.get('website', '')
    if url:
        try:
            d = urlparse(url if url.startswith('http') else 'https://'+url).netloc.replace('www.','')
            if d not in domain_data:
                domain_data[d] = {'total': 0, 'no_email': 0, 'ids_no_email': []}
            domain_data[d]['total'] += 1
            if not l.get('email') or l['email'].strip() == '':
                domain_data[d]['no_email'] += 1
                domain_data[d]['ids_no_email'].append(l['_id'])
        except:
            pass

# Domains with no-email leads
sorted_d = sorted(domain_data.items(), key=lambda x: -x[1]['no_email'])
deletable_ids = []
print(f'\n--- Domains with no-email leads ---')
for d, v in sorted_d:
    if v['no_email'] > 0:
        print(f'  {d}: {v["no_email"]}/{v["total"]} ohne Email')
        deletable_ids.extend(v['ids_no_email'])

print(f'\nTotal leads deletable (no email): {len(deletable_ids)}')

# Save deletable IDs
with open('/tmp/leads_to_delete.json', 'w') as f:
    json.dump(deletable_ids, f)
print(f'Saved to /tmp/leads_to_delete.json')

# Save all domain data for blocklist
with open('/tmp/domain_analysis.json', 'w') as f:
    json.dump({d: {'total': v['total'], 'no_email': v['no_email']} for d, v in sorted_d}, f, indent=2)
print(f'Domain analysis saved to /tmp/domain_analysis.json')
