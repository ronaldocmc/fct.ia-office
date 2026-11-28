"use strict";
const $=id=>document.getElementById(id);
let token="", profiles=[], tasks=[], view="dashboard", busy=false;
const root=$("view"), status=$("status");
function el(tag,text,parent){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(parent)parent.append(n);return n;}
function button(parent,label,fn){const b=el("button",label,parent);b.addEventListener("click",()=>action(fn));return b;}
async function api(path,data){const res=await fetch(path,{method:data===undefined?"GET":"POST",headers:{Authorization:"Bearer "+token,...(data===undefined?{}:{"Content-Type":"application/json"})},...(data===undefined?{}:{body:JSON.stringify(data)}),cache:"no-store"});const body=await res.json();if(!res.ok)throw Error(body.error||"Falha na API");return body;}
async function action(fn){if(busy)return;busy=true;document.querySelectorAll("button").forEach(b=>b.disabled=true);try{status.textContent="";status.className="";await fn();}catch(e){status.textContent=e.message;status.className="error";}finally{busy=false;document.querySelectorAll("button").forEach(b=>b.disabled=false);}}
function select(parent,options){const s=el("select",undefined,parent);for(const [value,label] of options){const o=el("option",label,s);o.value=value;}return s;}
function field(parent,label,value="",tag="input"){const l=el("label",label,parent),n=el(tag,undefined,l);n.value=value;return n;}
const samples={
 planejamento:{objetivo:"Evento fictício",etapas:["Preparar pauta"]},delegacao:{responsavel:"Agente fictício",atividade:"Preparar pauta"},revisao:{entregavel:"Minuta fictícia",criterios:["Clareza"]},agenda_simulada:{compromissos:["Reunião fictícia"]},briefing:{itens:["Reunião fictícia"]},minuta_email:{destinatario:"Setor fictício",assunto:"Teste",texto:"Minuta"},minuta_oficio:{destinatario:"Setor fictício",assunto:"Teste",texto:"Minuta"},minuta_ata:{reuniao:"Reunião fictícia",pautas:["Pauta"],deliberacoes:["Proposta"]},relatorio:{titulo:"Relatório fictício",observacoes:["Observação"]},classificar_solicitacao:{descricao:"Computador sem rede"},propor_ordem:{descricao:"Reparo fictício",setor:"Tecnologia"},acompanhar_prazo:{atividade:"Teste",prazo:"2027-01-03",referencia:"2027-01-01"}
};
const states={created:"Criada",assigned:"Atribuída",running:"Em execução",awaiting_review:"Aguardando revisão",approved:"Aprovada",revision_requested:"Revisão solicitada",failed:"Falha"};
async function refresh(){profiles=await api("/api/agents");tasks=await api("/api/tasks");await render();}
function taskCard(t,parent){
 const a=el("article",undefined,parent);el("h3",t.title,a);el("p",(states[t.state]||t.state)+" · "+t.skill+" · "+(profiles.find(p=>p.id===t.agent)?.name||"Sem responsável"),a);
 if(t.result)el("pre",t.result.result,a);
 if(t.review)el("p","Revisão: "+t.review.comment,a);
 const base="/api/tasks/"+encodeURIComponent(t.id)+"/";
 const mutate=async(op,payload={})=>{await api(base+op,payload);await refresh();};
 if(t.state==="created"){const options=profiles.filter(p=>p.skills.includes(t.skill)).map(p=>[p.id,p.name]);const s=select(a,options);button(a,"Atribuir",()=>mutate("assign",{agent:s.value}));}
 if(t.state==="assigned")button(a,"Executar skill Python",()=>mutate("run"));
 if(t.state==="awaiting_review"){const c=field(a,"Justificativa da revisão","Conferido no laboratório");button(a,"Aprovar tarefa",()=>mutate("review",{approve:true,comment:c.value}));button(a,"Solicitar revisão",()=>mutate("review",{approve:false,comment:c.value}));}
 if(["revision_requested","failed"].includes(t.state)){const p=field(a,"Entrada corrigida (JSON)",JSON.stringify(t.payload,null,2),"textarea");button(a,"Registrar correção",()=>mutate("revise",{payload:JSON.parse(p.value)}));}
 if(t.state==="approved")button(a,"Propor conhecimento ao Brain",async()=>{await api(base+"knowledge",{});view="brain";await refresh();});
}
async function render(){
 root.replaceChildren();el("h2",({dashboard:"Visão geral",agents:"Organização e agentes",tasks:"Tarefas e skills",reviews:"Central de aprovações",brain:"Segundo Cérebro",events:"Auditoria"})[view],root);
 if(view==="dashboard"){const g=el("div",undefined,root);g.className="grid";for(const [label,value] of [["Agentes",profiles.length],["Skills",profiles.reduce((n,p)=>n+p.skills.length,0)],["Tarefas",tasks.length],["Aguardando revisão",tasks.filter(t=>t.state==="awaiting_review").length]]){const a=el("article",undefined,g);el("p",label,a);el("div",String(value),a).className="metric";}el("p","Laboratório monousuário: execução manual, sem LLM e sem conexão com Paperclip.",root);}
 if(view==="agents"){const g=el("div",undefined,root);g.className="grid";for(const p of profiles){const a=el("article",undefined,g);el("h3",p.name,a);el("small",p.area+" · "+(p.reportsTo?"Reporta a "+(profiles.find(x=>x.id===p.reportsTo)?.name||p.reportsTo):"Coordenação principal"),a);el("p",p.mission,a);const l=el("ul",undefined,a);for(const s of p.skills)el("li",s,l);}}
 if(view==="tasks"){const a=el("article",undefined,root);el("h3","Nova tarefa fictícia",a);const title=field(a,"Título","Tarefa experimental");const s=select(a,profiles.flatMap(p=>p.skills.map(k=>[k,p.name+" — "+k])));const p=field(a,"Parâmetros da skill (JSON)","","textarea");p.rows=8;const sample=()=>p.value=JSON.stringify({synthetic:true,...samples[s.value]},null,2);s.addEventListener("change",sample);sample();button(a,"Criar tarefa",async()=>{await api("/api/tasks",{title:title.value,skill:s.value,payload:JSON.parse(p.value)});await refresh();});for(const t of tasks)taskCard(t,root);}
 if(view==="reviews"){const pending=tasks.filter(t=>t.state==="awaiting_review");if(!pending.length)el("p","Nenhuma tarefa aguardando revisão.",root);for(const t of pending)taskCard(t,root);}
 if(view==="brain"){el("h3","Propostas pendentes",root);const pending=await api("/api/brain/pending");if(!pending.length)el("p","Nenhuma proposta pendente.",root);for(const k of pending){const a=el("article",undefined,root);el("small",k.scope+" · "+k.source,a);el("pre",k.content,a);button(a,"Aprovar conhecimento",async()=>{await api("/api/brain/approve",{scope:k.scope,id:k.id});await refresh();});}
 el("h3","Conhecimentos aprovados",root);const scope=select(root,profiles.map(p=>[p.id,p.name]));const q=field(root,"Busca textual");const results=el("div",undefined,root);const search=async()=>{const rows=await api("/api/brain?"+new URLSearchParams({scope:scope.value,q:q.value}));results.replaceChildren();if(!rows.length)el("p","Nenhum conhecimento encontrado.",results);for(const k of rows){const a=el("article",undefined,results);el("small",k.scope+" · "+k.source,a);el("pre",k.content,a);el("p","Revisor: "+k.reviewer,a);}};button(root,"Buscar",search);await search();}
 if(view==="events"){const events=await api("/api/events");if(!events.length)el("p","Nenhum evento registrado.",root);for(const e of events.slice().reverse()){const a=el("article",undefined,root);el("strong",e.action+" · "+e.actor,a);el("p",e.at+" · "+e.task_id+" · "+e.state,a);}}
}
$("connect").addEventListener("click",()=>action(async()=>{token=$("token").value.trim();await refresh();$("token").value="";$("nav").hidden=false;status.textContent="Sessão local conectada.";}));
$("nav").addEventListener("click",e=>{if(e.target.matches("button[data-view]"))action(async()=>{view=e.target.dataset.view;await refresh();});});
