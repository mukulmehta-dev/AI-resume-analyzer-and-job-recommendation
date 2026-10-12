import re
import sys

with open('backend/test-results.txt', 'rb') as f:
    raw = f.read()

if raw.startswith(b'\xef\xbb\xbf'):
    raw = raw[3:]

text = raw.decode('utf-8')
text = text.replace('\r\n', '\n')

with open('backend/test-results.txt', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

if not re.search(r'=+\s*\d+\s+passed.*=+', text, re.IGNORECASE):
    print('ERROR: test-results.txt missing summary line')
    sys.exit(1)

for line in text.splitlines():
    if re.match(r'^\s*backend/tests/.*\.\.\.', line) or re.search(r'\[.*test cases.*\]', line):
        print(f'ERROR: Placeholder line found: {line}')
        sys.exit(1)

print('Verified test-results.txt is valid UTF-8 and contains valid summary line.')
