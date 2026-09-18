<script lang="ts">
  import { copyToClipboard } from '$lib/utils';
  import { toast } from 'svelte-sonner';
  import Modal from '$lib/components/common/Modal.svelte';
  import Switch from '$lib/components/common/Switch.svelte';
  import { onMount } from 'svelte';
  import { WEBUI_API_BASE_URL } from '$lib/constants';
  interface Entry { id: string; name: string; starts: number | null; ends: number | null; networks: string[]; revoked: number | null; enabled: boolean; origins: string[]; prefix: string; }
  let entries: Entry[] = [];
  let show = false;
  let copyFallback = '';
  let copyModal = false;
  let enabled = true;
  let origins = '';
  let loading = true;
  let name = '';
  let starts = '';
  let ends = '';
  let unlimited = true;
  let networks = '';
  let editing = '';
  let revealed = '';
  let busy = false;
  let error = '';
  let email = 'user@example.com';
  let username = '张三';
  let link = '';
  $: link = revealed && typeof window !== 'undefined'
    ? window.location.origin + '/api/v1/auths/embed?' + new URLSearchParams({email, username, token: revealed})
    : '';
  const field = 'w-full rounded-lg border border-gray-100/50 bg-gray-50/40 px-2 py-1.5 text-xs text-gray-700 outline-hidden placeholder:text-gray-300 focus:border-blue-400 dark:border-white/[0.04] dark:bg-white/[0.03] dark:text-gray-300 dark:placeholder:text-gray-700 dark:focus:border-blue-500';
  async function api(path = '', method = 'GET', body?: unknown) {
    const response = await fetch(`${WEBUI_API_BASE_URL}/auths/external-tokens${path}`, {
      method, headers: {Authorization: `Bearer ${localStorage.token}`, 'Content-Type':'application/json'},
      ...(body ? {body: JSON.stringify(body)} : {})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : '操作失败，请检查填写内容');
    return data;
  }
  async function refresh() { entries = await api(); }
  function reset() { editing = ''; name = ''; starts = ''; ends = ''; unlimited = true; networks = ''; origins = ''; enabled = true; }
  function localDate(value: number | null) {
    if (value === null) return '';
    const date = new Date(value * 1000);
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0,16);
  }
  function edit(entry: Entry) {
    editing = entry.id; name = entry.name; starts = localDate(entry.starts); ends = localDate(entry.ends);
    unlimited = entry.ends === null; networks = entry.networks.join('\n'); revealed = ''; error = ''; origins = entry.origins.join('\n'); enabled = entry.enabled; show = true;
  }
  function status(entry: Entry) {
    const now = Date.now() / 1000;
    if (entry.revoked !== null) return '已撤销';
    if (!entry.enabled) return '已停用';
    if (entry.starts !== null && now < entry.starts) return '未生效';
    if (entry.ends !== null && now >= entry.ends) return '已过期';
    return '有效';
  }
  async function save() {
    error = ''; busy = true;
    try {
      if (!name.trim() || (!unlimited && !ends)) throw new Error('请填写系统名称和结束时间，或选择不限时');
      const body = {name, starts: starts ? new Date(starts).toISOString() : null,
        ends: unlimited ? null : new Date(ends).toISOString(), enabled, origins: origins.split(/[\n,]+/).map(v=>v.trim()).filter(Boolean), networks: networks.split(/[\n,]+/).map(v=>v.trim()).filter(Boolean)};
      const result = await api(editing ? '/' + editing : '', editing ? 'PUT' : 'POST', body);
      revealed = result.token || ''; if (!revealed) show = false; reset(); await refresh();
    } catch (e) { error = (e as Error).message; } finally {busy = false;}
  }
  async function remove(entry: Entry) {
    if (!confirm(`删除“${entry.name}”的 Token？删除后无法恢复，已有会话不会被自动注销。`)) return;
    busy = true; error = '';
    try { await api('/'+entry.id, 'DELETE'); revealed = ''; await refresh(); }
    catch(e) {error = (e as Error).message;} finally {busy = false;}
  }
  async function copyUrl(entry: Entry) {
    error = ''; busy = true;
    try {
      const result = await api('/'+entry.id+'/credential');
      const url = window.location.origin + '/api/v1/auths/embed?email={email}&username={username}&token=' + encodeURIComponent(result.token);
      if (await copyToClipboard(url)) toast.success('嵌入 URL 已复制，请替换 {email} 和 {username}');
      else { copyFallback = url; copyModal = true; }
    } catch(e) { error = (e as Error).message; } finally { busy = false; }
  }
  async function toggle(entry: Entry, next: boolean) {
    busy = true; error = '';
    try {
      await api('/'+entry.id, 'PUT', {name:entry.name, starts:entry.starts === null ? null : new Date(entry.starts*1000).toISOString(), ends:entry.ends === null ? null : new Date(entry.ends*1000).toISOString(), networks:entry.networks, origins:entry.origins, enabled:next});
      await refresh();
    } catch(e) { error = (e as Error).message; await refresh(); } finally { busy = false; }
  }
  function create() {reset(); revealed = ''; error = ''; show = true;}
  onMount(() => { refresh().catch(e => error = e.message).finally(() => loading = false); });
</script>

<div class="flex h-full min-h-0 flex-col text-sm">
  <div class="mb-4 flex items-center justify-between">
    <h2 class="text-sm font-medium text-gray-900 dark:text-white">Token 管理</h2>
    <button type="button" aria-label="创建 Token" title="创建 Token" on:click={create}
      class="flex size-7 items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-white/[0.04]">
      <svg aria-hidden="true" class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path stroke-linecap="round" d="M12 5v14M5 12h14" /></svg>
    </button>
  </div>
  {#if error && !show}<p role="alert" class="mb-3 text-xs text-red-500">{error}</p>{/if}
  <div class="min-h-0 flex-1 overflow-auto scrollbar-hover">
    <table class="w-full text-left text-xs">
      <thead class="text-gray-500 dark:text-gray-400"><tr class="border-y border-gray-100 dark:border-white/[0.06]">
        {#each ['API Key', '启用状态', 'IP 设置', '到期时间', '跨域设置', '操作'] as title}<th class="whitespace-nowrap px-2 py-2.5 font-normal">{title}</th>{/each}
      </tr></thead>
      <tbody>
        {#each entries as entry (entry.id)}
          <tr class="border-b border-gray-100/60 dark:border-white/[0.04] hover:bg-gray-50/40 dark:hover:bg-white/[0.02]">
            <td class="px-2 py-3"><div class="font-medium text-gray-700 dark:text-gray-200">{entry.name}</div><div class="mt-1 whitespace-nowrap text-gray-400">{entry.prefix || 'owui_ext_'}••••••</div></td>
            <td class="px-2 py-3"><fieldset disabled={busy || entry.revoked !== null}><Switch state={entry.enabled && entry.revoked === null} ariaLabel={'启用 '+entry.name} on:change={(event)=>toggle(entry,event.detail)} /></fieldset><div class="mt-1 text-gray-400">{status(entry)}</div></td>
            <td class="max-w-36 break-words px-2 py-3 text-gray-500 dark:text-gray-400">{entry.networks.join('、') || '不限'}</td>
            <td class="whitespace-nowrap px-2 py-3 text-gray-500 dark:text-gray-400">{entry.ends === null ? '不限时' : new Date(entry.ends*1000).toLocaleString()}<div class="mt-1 text-gray-400">{entry.starts === null ? '立即生效' : new Date(entry.starts*1000).toLocaleString()+' 起'}</div></td>
            <td class="max-w-40 break-all px-2 py-3 text-gray-500 dark:text-gray-400">{entry.origins.join('、') || '系统默认'}</td>
            <td class="sticky right-0 bg-white px-2 py-3 dark:bg-gray-900"><div class="flex gap-3 whitespace-nowrap">{#if entry.revoked === null}<button type="button" disabled={busy} on:click={()=>edit(entry)} class="text-gray-500 hover:text-gray-900 dark:hover:text-white">编辑</button><button type="button" disabled={busy} on:click={()=>copyUrl(entry)} class="text-gray-500 hover:text-gray-900 dark:hover:text-white">复制 URL</button>{/if}<button type="button" disabled={busy} on:click={()=>remove(entry)} class="text-gray-400 hover:text-red-500">删除</button></div></td>
          </tr>
        {:else}<tr><td colspan="6" class="py-12 text-center text-xs text-gray-400">{loading ? '加载中…' : '暂无 Token，点击右上角 ＋ 创建'}</td></tr>{/each}
      </tbody>
    </table>
  </div>
</div>

<Modal bind:show size="sm">
  <div class="p-5 text-sm">
    <div class="mb-5 flex items-center justify-between"><h3 class="text-sm font-medium">{revealed ? 'Token 已创建' : editing ? '编辑 Token' : '创建 Token'}</h3><button type="button" aria-label="关闭" class="text-gray-400 hover:text-gray-700 dark:hover:text-white" on:click={()=>{show=false;revealed='';}}>✕</button></div>
    {#if error}<p role="alert" class="mb-3 text-xs text-red-500">{error}</p>{/if}
    {#if revealed}
      <div class="space-y-4">
        <p class="text-xs text-gray-500 dark:text-gray-400">Token 已加密保存；以后可在列表中复制嵌入 URL。</p>
        <label class="block text-xs">API Key<input class={field+' mt-1'} readonly value={revealed} /></label>
        <div class="grid grid-cols-2 gap-3"><label class="text-xs">示例邮箱<input class={field+' mt-1'} bind:value={email}/></label><label class="text-xs">示例姓名<input class={field+' mt-1'} bind:value={username}/></label></div>
        <label class="block text-xs">iframe URL<textarea class={field+' mt-1'} rows="3" readonly value={link}></textarea></label>
        <div class="flex justify-end"><button type="button" class="rounded-full bg-black px-3.5 py-1.5 text-xs text-white dark:bg-white dark:text-black" on:click={()=>{show=false;revealed='';}}>已保存</button></div>
      </div>
    {:else}
      <form on:submit|preventDefault={save}>
        <fieldset disabled={busy} class="space-y-4">
          <label class="block text-xs">系统名称<input class={field+' mt-1'} bind:value={name} maxlength="100" required placeholder="例如：警务业务平台" /></label>
          <div class="flex justify-between text-xs"><span>启用状态</span><Switch bind:state={enabled} ariaLabel="启用 Token" /></div>
          <div class="grid grid-cols-2 gap-3"><label class="text-xs">开始时间<input class={field+' mt-1'} type="datetime-local" bind:value={starts}/></label><label class="text-xs">到期时间<input class={field+' mt-1'} type="datetime-local" bind:value={ends} disabled={unlimited} required={!unlimited}/></label></div>
          <div class="flex justify-between text-xs"><span>不限到期时间</span><Switch bind:state={unlimited} ariaLabel="不限到期时间" /></div>
          <label class="block text-xs">IP 设置<textarea class={field+' mt-1'} bind:value={networks} rows="2" placeholder="留空不限；单个 IP 或 CIDR 网段，每行一个"></textarea></label>
          <label class="block text-xs">跨域设置<textarea class={field+' mt-1'} bind:value={origins} rows="2" placeholder="https://portal.example.com"></textarea><span class="mt-1 block text-xs text-gray-400">允许 iframe 嵌入的网站来源，每行一个；留空使用系统默认。</span></label>
          <p class="text-xs leading-relaxed text-gray-400">仅限可信系统。持有者可指定普通用户邮箱；停用、到期及删除限制新登录，不注销已有会话。</p>
          <div class="flex justify-end gap-3 pt-1"><button type="button" class="text-xs text-gray-500" on:click={()=>show=false}>取消</button><button type="submit" class="rounded-full bg-black px-3.5 py-1.5 text-xs text-white dark:bg-white dark:text-black">{busy ? '保存中…' : editing ? '保存' : '创建'}</button></div>
        </fieldset>
      </form>
    {/if}
  </div>
</Modal>

<Modal bind:show={copyModal} size="sm">
  <div class="space-y-4 p-5 text-xs"><h3 class="text-sm font-medium">复制嵌入 URL</h3><p>浏览器未允许自动复制，请手动复制并替换邮箱、姓名占位符。</p><textarea class={field} rows="4" readonly value={copyFallback}></textarea><button type="button" on:click={()=>{copyModal=false;copyFallback='';}}>关闭</button></div>
</Modal>
