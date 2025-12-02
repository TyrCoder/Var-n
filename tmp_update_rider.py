from pathlib import Path

file_path = Path('templates/auth/signupRider.html')
tail_path = Path('tail_snippet.html')

with file_path.open('r', encoding='utf-8') as f:
    content = f.read()

with tail_path.open('r', encoding='utf-8') as f:
    tail = f.read()

marker = '<label for="riderConfirmPassword">'
marker_idx = content.find(marker)
if marker_idx == -1:
    raise SystemExit('confirm password marker not found')

start_idx = content.rfind('<div class="field-grid">', 0, marker_idx)
if start_idx == -1:
    raise SystemExit('field grid block not found')

new_content = content[:start_idx] + tail

with file_path.open('w', encoding='utf-8') as f:
    f.write(new_content)
