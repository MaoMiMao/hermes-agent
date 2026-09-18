"""Install the local embed extension into an Open WebUI source checkout."""
import shutil
import sys
from pathlib import Path

source = Path(__file__).resolve().parent
backend = Path(sys.argv[1]).resolve() / 'backend/open_webui'
auths = backend / 'routers/auths.py'
text = auths.read_text(encoding='utf-8')
for filename, target in [('external_tokens.py', 'utils'), ('embed_auth.py', 'routers'), ('embed_login.html', 'routers')]:
    shutil.copyfile(source / filename, backend / target / filename)
old_marker = '# Local iframe ticket login (password login remains unchanged).'
marker = '# Local iframe external token login (password login remains unchanged).'
text = text.replace('# Local iframe signed URL login (password login remains unchanged).', marker)
if old_marker in text:
    text = text.replace(old_marker, marker)
    auths.write_text(text, encoding='utf-8', newline='\n')
auths.write_text(text, encoding='utf-8', newline='\n')
if marker not in text:
    with auths.open('a', encoding='utf-8', newline='\n') as file:
        file.write('\n\n' + marker + '\nfrom open_webui.routers.embed_auth import router as embed_router\nrouter.include_router(embed_router)\n')
print('Installed embed login into', backend)

ui = backend.parent.parent / 'src/lib/components/admin/Settings'
shutil.copyfile(source / 'ExternalTokens.svelte', ui / 'ExternalTokens.svelte')
settings_file = ui / 'Authentication.svelte'
settings_text = settings_file.read_text(encoding='utf-8')
settings_text = settings_text.replace('\timport ExternalTokens from "./ExternalTokens.svelte";\n', '').replace('\t\t<ExternalTokens />\n','').replace('\n\n<ExternalTokens />','')
settings_file.write_text(settings_text, encoding='utf-8', newline='\n')
modal = ui.parents[1] / 'chat/SettingsModal.svelte'
text = modal.read_text(encoding='utf-8')
if "id: 'admin:access-control'" not in text:
    text = text.replace('<script lang="ts">', '<script lang="ts">\n\timport ExternalTokens from "$lib/components/admin/Settings/ExternalTokens.svelte";', 1)
    text = text.replace("'admin:authentication': 'System',", "'admin:authentication': 'System',\n\t\t'admin:access-control': 'System',", 1)
    text = text.replace("\t\t{\n\t\t\tid: 'admin:connections',", "\t\t{id: 'admin:access-control', title: '访问控制', keywords: ['token', 'apikey', 'ip', '访问控制', '跨域']},\n\t\t{\n\t\t\tid: 'admin:connections',", 1)
    text = text.replace("{:else if selectedTab === 'admin:connections'}", "{:else if selectedTab === 'admin:access-control'}\n\t\t\t\t<ExternalTokens />\n\t\t\t{:else if selectedTab === 'admin:connections'}", 1)
    modal.write_text(text, encoding='utf-8', newline='\n')
icon = ui / 'AdminTabIcon.svelte'
text = icon.read_text(encoding='utf-8')
if "id === 'access-control'" not in text:
    text = text.replace("id === 'authentication'", "id === 'authentication' || id === 'access-control'")
icon.write_text(text, encoding='utf-8', newline='\n')
