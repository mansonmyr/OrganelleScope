"""Render private, owner-reviewed channel annotations alongside numerical results."""
from html import escape
from pathlib import Path


def validated_review(review, centers):
    """Acceptance applies only to the exact source-bound candidate positions reviewed."""
    if not review or review.get('candidate_centers_zyx') != centers: return None
    accepted = set(review.get('accepted_candidates', [])); rejected = set(review.get('rejected_candidates', []))
    if accepted & rejected or not (accepted | rejected) <= {int(key) for key in centers}:
        raise ValueError('Owner review contains invalid or contradictory candidate IDs.')
    return review


def render_review(report, output):
    def e(value): return escape(str(value), quote=True)
    def number(value): return 'Undefined' if value is None else f'{value:.4f}'
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>OrganelleScope sample-control review</title><style>body{font:16px system-ui;max-width:1400px;margin:32px auto;padding:24px;background:#FDF0D5;color:#173747}img{max-width:100%;border:1px solid #6DB1BF}table{border-collapse:collapse;width:100%}td,th{padding:8px;text-align:left;border-bottom:1px solid #6DB1BF}section{background:#FFEAEC;padding:24px;margin:24px 0}code{overflow-wrap:anywhere}.table-scroll{overflow-x:auto}</style><body><h1>Owner-supplied sample-control review</h1>']
    parts += [f'<p>{e(report[key])}</p>' for key in ('scope', 'protocol')]
    parts.append('<p>All proposed regions are retained. Regions are not independent cells or experiments. Maximum projections are contrast-stretched for review only; coefficients use raw single-plane pixels. Different acquisitions are not a matched population experiment. Filenames retain their original names; owner-confirmed stored-channel assignments take precedence over filenames and dye names.</p>')
    for file in report['files']:
        labels = file['channel_labels']; a, b = [labels[c-1] for c in file['primary_pair_1based']]
        parts += [f'<section><h2>{e(file["filename"])}</h2><p>{e(file["expected_context"])}</p>', f'<p>Source SHA-256: <code>{e(file["source_sha256"])}</code></p>']
        if file.get('annotation_correction'): parts.append(f'<p><strong>Owner correction:</strong> {e(file["annotation_correction"])}</p>')
        parts.append('<p>Stored channels: ' + '; '.join(f'C{i+1}: {e(label)}' for i, label in enumerate(labels)) + '.</p>')
        review = file.get('owner_roi_review') or {}
        accepted = set(review.get('accepted_candidates', [])); rejected = set(review.get('rejected_candidates', []))
        if review: parts.append(f'<p><strong>Owner ROI review:</strong> {e(review.get("note",""))} Accepted: {e(sorted(accepted))}; rejected: {e(sorted(rejected))}.</p>')
        parts.append(f'<p>Reference-channel candidate selection: C{file["reference_channel_1based"]} · {e(labels[file["reference_channel_1based"]-1])}. ROI review: {e(file.get("roi_review_status", "pending"))}. No control classification is imposed on coefficients.</p>')
        parts.append(f'<img alt="Selected channel projections and proposed ROIs" src="{e(file["review_image"])}">')
        parts.append(f'<p>A: {e(a)}; B: {e(b)}. Direction follows native stored-channel order. M1 is the fraction of A intensity where B exceeds its threshold, divided by total A intensity; M2 reverses A/B. Neither is a shared-volume fraction.</p>')
        parts.append('<div class="table-scroll"><table><thead><tr><th>Candidate / native Z index</th><th>Owner review</th><th>Diameter</th><th>Threshold</th><th>Pearson</th><th>Spearman</th><th>M1</th><th>M2</th></tr></thead><tbody>')
        for row in file['results']:
            pair = row['pair']; mode = 'Whole-volume Otsu (provided)' if row['threshold_mode'] == 'manual' else 'Zero'
            status = 'Accepted for testing' if row['candidate'] in accepted else 'Rejected; technical result only' if row['candidate'] in rejected else 'Pending'
            fields = [f'{row["candidate"]} / {row["center_zyx"][0]}', status, f'{row["diameter"]} {row["diameter_unit"]}', mode] + [number(pair.get(key)) for key in ('pcc', 'spearman', 'thresholded_m1', 'thresholded_m2')]
            parts.append('<tr>' + ''.join(f'<td>{e(value)}</td>' for value in fields) + '</tr>')
        parts.append('</tbody></table></div></section>')
    parts.append('</body></html>')
    (Path(output)/'REVIEW.html').write_text('\n'.join(parts)+'\n', encoding='utf-8')
