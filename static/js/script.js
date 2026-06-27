'use strict';
const IMAGE_BASE = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG/";

const PREFIX_MAP = {
  "902":"Avatar","214":"Pintura Facial","101":"Habilidade Feminina","102":"Habilidade Masculina",
  "103":"Microchip","905":"Paraquedas","710":"Pacote","720":"Pacote",
  "203":"Camisa","204":"Calça","205":"Sapatos","211":"Cabeça","901":"Estandarte",
  "131":"Pet","130":"Pet/Emote","903":"Caixa de Loot","904":"Mochila",
  "906":"Prancha","907":"Outro","908":"Veículo","909":"Emote",
  "911":"Asa Delta","922":"Skin de Habilidade","912":"Skin de Arma"
};
function getItemType(id){const s=String(id);return PREFIX_MAP[s.slice(0,3)]||PREFIX_MAP[s.slice(0,2)]||"Item";}

/* ======================================================
   ANIMAÇÃO CANVAS HACKER
   ====================================================== */
(function initHack(){
  const canvas = document.getElementById('hackCanvas');
  const ctx    = canvas.getContext('2d');
  const chars  = 'アイウエオカキクケコ01アイウエオ10ABCDEF0123456789</>{}[];:#$%^&*|\\KAWSARFFINFO'.split('');
  let cols, drops, fontSize = 13;

  function resize(){
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    cols  = Math.floor(canvas.width / fontSize);
    drops = Array(cols).fill(1);
  }
  resize();
  window.addEventListener('resize', resize);

  function getColor(){
    return getComputedStyle(document.documentElement).getPropertyValue('--ac').trim() || '#00ffff';
  }

  setInterval(()=>{
    ctx.fillStyle = 'rgba(6,6,16,0.08)';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = getColor();
    ctx.font = fontSize+'px "Share Tech Mono",monospace';
    for(let i=0;i<drops.length;i++){
      const c = chars[Math.floor(Math.random()*chars.length)];
      ctx.fillText(c, i*fontSize, drops[i]*fontSize);
      if(drops[i]*fontSize > canvas.height && Math.random()>0.975) drops[i]=0;
      drops[i]++;
    }
  }, 45);
})();

/* ======================================================
   SELETOR DE CORES DO TEMA
   ====================================================== */
function hexToRgba(hex, alpha){
  const r=parseInt(hex.slice(1,3),16);
  const g=parseInt(hex.slice(3,5),16);
  const b=parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}
function setThemeColor(hex, btn){
  const root = document.documentElement;
  root.style.setProperty('--ac', hex);
  // escurecer para ac2
  root.style.setProperty('--ac2', hex);
  root.style.setProperty('--ac-glow', hexToRgba(hex, 0.22));
  root.style.setProperty('--border', hexToRgba(hex, 0.2));
  // atualizar amostra de cor ativa
  document.querySelectorAll('.swatch').forEach(s=>s.classList.remove('active'));
  if(btn) btn.classList.add('active');
  // salvar
  try{localStorage.setItem('ff_theme_color', hex);}catch(e){}
}
// Carregar cor salva
try{
  const saved = localStorage.getItem('ff_theme_color');
  if(saved){
    setThemeColor(saved);
    document.querySelectorAll('.swatch').forEach(s=>{
      if(s.dataset.color===saved) s.classList.add('active');
      else s.classList.remove('active');
    });
  }
}catch(e){}

/* ======================================================
   BANNER
   ====================================================== */
function closeBanner(){
  const b=document.getElementById('welcomeBanner');
  b.classList.add('hide');
  setTimeout(()=>{b.style.display='none';document.getElementById('mainSite').style.display='block';},800);
}

/* ======================================================
   GUIA
   ====================================================== */
function toggleGuide(){
  const g=document.getElementById('guideBox');
  g.style.display=g.style.display==='none'?'block':'none';
}

/* ======================================================
   FUNÇÕES DE FORMATAÇÃO
   ====================================================== */
function fmtTime(ts){
  if(!ts||ts==='0') return '—';
  try{return new Date(parseInt(ts)*1000).toLocaleDateString('pt-BR',{day:'2-digit',month:'short',year:'numeric'});}
  catch{return ts;}
}
function fmtNum(n){if(!n||n==='0') return '0'; return parseInt(n).toLocaleString('pt-BR');}

/* ======================================================
   CRIAR LISTA HORIZONTAL DE INFORMAÇÕES
   ====================================================== */
function buildRows(containerId, rows){
  const c = document.getElementById(containerId);
  c.innerHTML='';
  rows.forEach(([key,val,hl])=>{
    const d=document.createElement('div');
    d.className='info-row';
    d.innerHTML=`<span class="info-key">${key}</span><span class="info-val${hl?' hl':''}">${val||'—'}</span>`;
    c.appendChild(d);
  });
}

/* ======================================================
   CRIAR GRADE DE ITENS (roupas, armas)
   ====================================================== */
function buildItemGrid(containerId, ids, emptyMsg){
  const c=document.getElementById(containerId);
  c.innerHTML='';
  const arr=Array.isArray(ids)?ids:[];
  if(!arr.length){c.innerHTML=`<div class="empty-msg">${emptyMsg}</div>`;return;}
  arr.forEach(id=>{
    const sid=String(id);
    const type=getItemType(sid);
    const card=document.createElement('div');
    card.className='item-card';
    card.innerHTML=`
      <img class="item-img" src="${IMAGE_BASE}${sid}.png" alt="${sid}" loading="lazy"
           onerror="this.style.opacity='0.25';this.src='${IMAGE_BASE}902001.png'"/>
      <div class="item-type">${type}</div>`;
    c.appendChild(card);
  });
}

/* ======================================================
   CRIAR LISTA DE HABILIDADES (texto simples — sem PNG)
   ====================================================== */
function buildSkillList(containerId, skills, emptyMsg){
  const c=document.getElementById(containerId);
  c.innerHTML='';
  const arr=Array.isArray(skills)?skills:[];
  if(!arr.length){c.innerHTML=`<div class="empty-msg">${emptyMsg}</div>`;return;}
  arr.forEach((s,i)=>{
    const item=document.createElement('div');
    item.className='skill-item';
    // s pode ser o objeto {skillId, skillLevel} ou um número simples
    if(typeof s==='object' && s!==null){
      const sid  = s.skillId   || s.skill_id   || s.id || '—';
      const slvl = s.skillLevel|| s.skill_level || s.level || '—';
      item.innerHTML=`
        <span class="skill-name">Habilidade ${i+1}</span>
        <span class="skill-id">ID: ${sid}</span>
        <span class="skill-lvl">Nível: ${slvl}</span>`;
    } else {
      item.innerHTML=`
        <span class="skill-name">Habilidade ${i+1}</span>
        <span class="skill-id">ID: ${s}</span>`;
    }
    c.appendChild(item);
  });
}

/* ======================================================
   RENDERIZAR RESULTADO COMPLETO
   ====================================================== */
function renderResult(data){
  const ai = data.AccountInfo       || {};
  const ap = data.AccountProfileInfo|| {};
  const gi = data.GuildInfo         || {};
  const pet= data.petInfo           || {};
  const cr = data.creditScoreInfo   || {};

  // Cabeçalho do jogador
  const avatarId = ai.AccountAvatarId||'902001';
  document.getElementById('playerAvatar').src = `${IMAGE_BASE}${avatarId}.png`;
  document.getElementById('playerName').textContent = ai.AccountName||'Desconhecido';
  document.getElementById('tagRegion').textContent  = ai.AccountRegion||'—';
  document.getElementById('tagLevel').textContent   = `NV ${ai.AccountLevel||'—'}`;
  document.getElementById('tagGuild').textContent   = gi.GuildName||'Sem Guilda';
  document.getElementById('statLikes').textContent  = fmtNum(ai.AccountLikes);
  document.getElementById('statEXP').textContent    = fmtNum(ai.AccountEXP);
  document.getElementById('statBPBadge').textContent= fmtNum(ai.AccountBPBadges);

  // Linhas de informações da conta (horizontal)
  buildRows('accountInfoList',[
    ['Nome',         ai.AccountName,             true],
    ['UID',          data.socialinfo?.accountId||'—', true],
    ['Região',       ai.AccountRegion],
    ['Nível',        ai.AccountLevel],
    ['Tipo de Conta', ai.AccountType],
    ['ID da Temporada', ai.AccountSeasonId],
    ['Criada em',      fmtTime(ai.AccountCreateTime)],
    ['Último Login',   fmtTime(ai.AccountLastLogin)],
    ['Versão',      ai.ReleaseVersion],
    ['Pontuação de Crédito', cr.creditScore||'—'],
  ]);

  // Linhas de informações da guilda
  buildRows('guildInfoList',[
    ['Nome da Guilda',  gi.GuildName,  true],
    ['ID da Guilda',    gi.GuildID],
    ['Nível',       gi.GuildLevel],
    ['Membros',     `${gi.GuildMember} / ${gi.GuildCapacity}`],
    ['ID do Líder',    gi.GuildOwner],
  ]);

  // Linhas de informações de patente
  buildRows('rankInfoList',[
    ['Pontos Rank BR', fmtNum(ai.BrRankPoint), true],
    ['Patente Máx BR',    ai.BrMaxRank],
    ['Mostrar Rank BR',   ai.ShowBrRank==='1'?'✅ Sim':'❌ Não'],
    ['Pontos Rank CS', fmtNum(ai.CsRankPoint), true],
    ['Patente Máx CS',    ai.CsMaxRank],
    ['Mostrar Rank CS',   ai.ShowCsRank==='1'?'✅ Sim':'❌ Não'],
    ['ID do Passe',          ai.AccountBPID],
  ]);

  // Linhas de informações do pet
  buildRows('petInfoList',[
    ['Nome do Pet',   pet.name||'—',         true],
    ['ID do Pet',     pet.id||'—'],
    ['Nível do Pet',  pet.level||'—'],
    ['EXP do Pet',    fmtNum(pet.exp)],
    ['Selecionado',   pet.isSelected?'✅ Sim':pet.id?'❌ Não':'—'],
    ['ID da Habilidade',   pet.selectedSkillId||'—'],
  ]);

  // Roupas equipadas → imagens
  buildItemGrid('outfitGrid',  ap.EquippedOutfit||[],  '👗 Sem dados de roupa');

  // Armas equipadas → imagens
  buildItemGrid('weaponGrid',  ai.EquippedWeapon||[],  '🔫 Sem dados de skin de arma');

  // Habilidades equipadas → TEXTO SIMPLES (sem PNG)
  buildSkillList('skillList',  ap.EquippedSkills||[],  '⚡ Sem dados de habilidade');
}

/* ======================================================
   BUSCA
   ====================================================== */
async function searchPlayer(){
  const uid    = document.getElementById('uidInput').value.trim();
  const region = document.getElementById('regionSelect').value;
  if(!uid){showError('Por favor, insira um UID');return;}
  if(!/^\d{5,15}$/.test(uid)){showError('UID inválido — apenas números');return;}

  setLoading(true);
  hideError();
  document.getElementById('resultSection').style.display='none';

  try{
    let url=`/get?uid=${encodeURIComponent(uid)}`;
    if(region) url+=`&region=${encodeURIComponent(region)}`;
    const res  = await fetch(url);
    const data = await res.json();
    if(!res.ok||data.error){showError(data.error||'Jogador não encontrado');return;}
    renderResult(data);
    document.getElementById('resultSection').style.display='block';
    document.getElementById('resultSection').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(err){
    showError('Erro de rede');
    console.error(err);
  }finally{setLoading(false);}
}

function setLoading(on){
  document.getElementById('searchBtn').disabled=on;
  document.getElementById('btnText').style.display   =on?'none':'inline';
  document.getElementById('btnLoader').style.display =on?'inline-block':'none';
}
function showError(msg){
  document.getElementById('errorMsg').textContent=msg;
  document.getElementById('errorBox').style.display='flex';
}
function hideError(){document.getElementById('errorBox').style.display='none';}

document.getElementById('uidInput').addEventListener('keydown',e=>{if(e.key==='Enter')searchPlayer();});
