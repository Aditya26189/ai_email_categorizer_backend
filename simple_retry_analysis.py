import yaml

with open('crashlens_retry_policy.yaml', 'r', encoding='utf-8') as f:
    policy = yaml.safe_load(f)

print("=== Retry Policy Analysis ===")
for rule in policy.get('rules', []):
    if rule.get('id') == 'excessive_retry_pattern':
        print('Found retry limit rule:')
        print(f'  ID: {rule["id"]}')
        print(f'  Match condition: {rule["match"]}')
        print(f'  Action: {rule["action"]}')
        print(f'  Severity: {rule["severity"]}')
        print(f'  Retry limit: {rule["match"]["retry_count"]}')
        break

print("\n=== Workflow Configuration ===")
try:
    with open('.github/workflows/crashlens-scan.yml', 'r', encoding='utf-8') as f:
        workflow_content = f.read()
    
    if 'CRASHLENS_FAIL_ON_VIOLATIONS: "false"' in workflow_content:
        print("Build breaking: DISABLED")
    elif 'CRASHLENS_FAIL_ON_VIOLATIONS: "true"' in workflow_content:
        print("Build breaking: ENABLED")
    
    continue_count = workflow_content.count('continue-on-error: true')
    print(f"Steps with continue-on-error: {continue_count}")
    
except Exception as e:
    print(f"Error reading workflow: {e}")
