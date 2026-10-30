// Browser port of acezephyr/gen_bet_data.py. The input seed is the game's
// frame counter; time since reset is converted at 60 frames per second.
const RACER_NAMES = ['SAM','ELEN','BLUES','TOM','JOHN','GARY','MIKE','SANDY','JU','LY','JOEL','GREY','EDWARD','JAMES','HARVEY','DAN','RUDY','GRAHAM','FOX','CLIVE','SEAN','YOUNG','ROBIN','DARIO','ARL','SARA','MARIE','SAMMY','LIA','KNIGHT','PAULA','PAU','LE','PETER','AIMEE','TERRY','ANDY','NANCY','TIM','ROBER','GEORGE','JENNY','RICA','JULIA'];
const PRIZE_NAMES = ['Sprint Shoes','Counter Attack','Magic Counter','Precious Watch',"Cat's Bell",'Enemy Away','Sneak Attack','Chocobracelet','Ether','Elixir','Hero Drink','Bolt Plume','Fire Fang','Antarctic Wind','Swift Bolt','Fire Veil','Ice Crystal','Megalixer','Turbo Ether','Potion','Phoenix Down','Hyper','Tranquilizer','Hi-Potion'];
const PRIZE_GP_VALUES = [500,300,500,300,500,300,300,400,30,200,15,20,20,20,50,50,50,300,150,5,10,10,10,15];
const REWARD_TABLES = {
  C:[[23,0,5,1],[8,0,20,1],[21,0,10,0],[22,0,10,0],[20,0,20,0],[11,0,5,1],[12,0,5,0],[13,0,5,0],[19,0,5,1],[20,0,20,1]],
  B:[[8,0,30,0],[10,0,10,0],[20,0,20,0],[18,0,5,1],[8,0,30,0],[23,0,5,0],[21,0,10,0],[22,0,10,0],[23,0,5,0],[11,0,10,1],[12,0,10,0],[13,0,10,0],[9,0,10,1],[5,1,5,1],[23,0,5,0]],
  A:[[8,0,20,0],[10,0,10,0],[14,1,10,0],[15,1,10,0],[12,0,10,0],[16,1,10,0],[1,0,10,1],[5,1,5,1],[11,0,10,0],[12,0,10,0],[13,0,10,0],[9,0,10,1],[23,0,5,0],[8,0,20,0],[0,1,7,1],[9,0,5,1],[20,0,20,0],[12,0,10,0],[4,1,7,1],[6,1,7,1]],
  S:[[18,1,5,0],[10,0,5,0],[9,0,5,1],[1,0,5,1],[5,1,5,1],[6,1,5,1],[14,1,5,0],[15,1,5,0],[11,0,2,0],[15,1,5,0],[20,0,20,0],[16,0,5,0],[17,1,5,1],[18,0,5,0],[0,1,5,1],[14,0,5,0],[4,1,5,1],[9,0,5,1],[7,1,5,1],[16,1,5,0],[3,1,5,1],[2,1,5,1]]
};
const CHOCO_STAT_TABLE = {C:[0x09c4,0x01f4,0x06a4,0x00c8],B:[0x0bb8,0x0258,0x0898,0x012c],A:[0x0dac,0x02bc,0x0bb8,0x01f4],S:[0x1388,0x0320,0x0fa0,0x01f4]};
const AI_JOCKEY_COLORS=[
  {label:'Silver',color:'#718fca'},
  {label:'Gold',color:'#f0d43a'},
  {label:'Bronze',color:'#a96e3c'},
  {label:'Platinum',color:'#85878a'}
];
// The game's frame counter appears to wrap at 0x400000 (2^22).
const FRAME_CYCLE = 0x400000;
const form = document.querySelector('#search-form');
const rankSelect = document.querySelector('#rank');
const speedSelect = document.querySelector('#speed');
const staminaSelect = document.querySelector('#stamina');
const nameSelect = document.querySelector('#name');
const prizeSelects = [0,1,2].map(index => document.querySelector(`#prize-${index}`));
const prizeFilters = [null,null,null];
const searchButton = document.querySelector('#search-button');
const cancelButton = document.querySelector('#cancel-button');
const keepSearchingButton = document.querySelector('#keep-searching-button');
const resultBanner = document.querySelector('#result-banner');
let cancelSearch = false;
let lastFoundFrame = null;
let latestDiscoveredFrame = null;
let exactStartFrameOverride = null;

function makeOptions(select, values, selectedValue, label = value => value) {
  select.replaceChildren(...values.map(value => {
    const option = document.createElement('option'); option.value = value; option.textContent = label(value);
    if (String(value) === String(selectedValue)) option.selected = true;
    return option;
  }));
}
let openCustomDropdown = null;
function syncCustomDropdown(select) {
  const trigger = select._customTrigger;
  if (trigger) trigger.textContent = select.selectedOptions[0]?.textContent ?? '';
  const giftValue = select.closest('.gift-field')?.querySelector('.gift-gp');
  if (giftValue) giftValue.textContent = select.value === '' ? '' : `${PRIZE_GP_VALUES[Number(select.value)]} GP`;
  const menu = select._customMenu;
  if (!menu) return;
  const selectedValue = select.value;
  const options = Array.from(select.options);
  const isGiftMenu = Boolean(select.closest('.gift-field'));
  const anyGift = isGiftMenu ? options.filter(option => option.value === '') : [];
  const possibleGifts = isGiftMenu ? options.filter(option => option.value !== '' && option.dataset.slotPossible === 'true') : [];
  const otherGifts = isGiftMenu ? options.filter(option => option.value !== '' && option.dataset.slotPossible !== 'true') : [];
  const orderedOptions = isGiftMenu ? [...anyGift, ...possibleGifts, ...otherGifts] : options;
  const dividerAt = anyGift.length + possibleGifts.length;
  const menuItems = [];
  orderedOptions.forEach((option, index) => {
    if (isGiftMenu && index === dividerAt && possibleGifts.length && otherGifts.length) {
      const divider = document.createElement('div');
      divider.className = 'custom-select-divider';
      divider.setAttribute('role', 'separator');
      menuItems.push(divider);
    }
    const item = document.createElement('button');
    item.type = 'button'; item.className = 'custom-select-option';
    item.setAttribute('role', 'option'); item.setAttribute('aria-selected', String(option.value === selectedValue));
    item.disabled = option.disabled; item.textContent = option.textContent; item.tabIndex = -1;
    item.addEventListener('click', () => {
      select.value = option.value;
      select.dispatchEvent(new Event('change', {bubbles:true}));
      syncCustomDropdown(select); closeCustomDropdown(); trigger.focus();
    });
    menuItems.push(item);
  });
  menu.replaceChildren(...menuItems);
}
function closeCustomDropdown(restoreFocus = false) {
  if (!openCustomDropdown) return;
  const {trigger, menu} = openCustomDropdown;
  menu.hidden = true; trigger.setAttribute('aria-expanded', 'false');
  openCustomDropdown = null;
  if (restoreFocus) trigger.focus();
}
function openDropdown(select, trigger, menu) {
  closeCustomDropdown();
  const rect = trigger.getBoundingClientRect();
  const width = Math.min(Math.max(rect.width, 150), window.innerWidth - 12);
  const left = Math.max(6, Math.min(rect.left, window.innerWidth - width - 6));
  const availableBelow = window.innerHeight - rect.bottom - 28;
  const availableAbove = rect.top - 8;
  const placeAbove = Boolean(select.closest('.gift-field')) || (availableBelow < 140 && availableAbove > availableBelow);
  menu.style.width = `${width}px`; menu.style.left = `${left}px`;
  menu.style.maxHeight = `${Math.max(80, Math.min(window.innerHeight - 16, placeAbove ? availableAbove : availableBelow))}px`;
  menu.style.top = placeAbove ? 'auto' : `${rect.bottom + 3}px`;
  menu.style.bottom = placeAbove ? `${window.innerHeight - rect.top + 3}px` : 'auto';
  menu.hidden = false; trigger.setAttribute('aria-expanded', 'true');
  openCustomDropdown = {select, trigger, menu};
  const selected = menu.querySelector('[aria-selected="true"]');
  (selected || menu.querySelector('.custom-select-option:not(:disabled)'))?.focus();
  selected?.scrollIntoView({block:'nearest'});
}
function initializeCustomDropdowns() {
  document.querySelectorAll('.select-wrap select, .class-select-wrap select').forEach(select => {
    const wrapper = select.parentElement;
    const trigger = document.createElement('button');
    trigger.type = 'button'; trigger.className = 'custom-select-trigger';
    if (select.id === 'speed') trigger.classList.add('custom-select-trigger--speed');
    trigger.setAttribute('aria-haspopup', 'listbox'); trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-label', select.getAttribute('aria-label') || select.closest('.gift-field')?.querySelector('.sr-only')?.textContent || select.name || 'Choose an option');
    const menu = document.createElement('div');
    menu.className = 'custom-select-menu'; menu.setAttribute('role', 'listbox'); menu.hidden = true;
    const computed = getComputedStyle(select);
    trigger.style.font = computed.font; trigger.style.color = computed.color;
    trigger.style.textAlign = computed.textAlign; trigger.style.textShadow = computed.textShadow;
    trigger.style.letterSpacing = computed.letterSpacing;
    trigger.style.justifyContent = ['left','start'].includes(computed.textAlign) ? 'flex-start' : ['right','end'].includes(computed.textAlign) ? 'flex-end' : 'center';
    if (select.id === 'speed') {trigger.style.textAlign = 'center'; trigger.style.justifyContent = 'center';}
    select._customTrigger = trigger; select._customMenu = menu;
    select.classList.add('custom-select-source'); select.tabIndex = -1; select.setAttribute('aria-hidden','true');
    wrapper.append(trigger); document.body.append(menu);
    select.addEventListener('change', () => syncCustomDropdown(select));
    const observer = new MutationObserver(() => syncCustomDropdown(select));
    observer.observe(select, {childList:true,subtree:true,attributes:true,attributeFilter:['selected','disabled']});
    trigger.addEventListener('click', () => {
      if (openCustomDropdown?.trigger === trigger) closeCustomDropdown();
      else openDropdown(select, trigger, menu);
    });
    let typeahead = '';
    let typeaheadTimer;
    const matchingOption = prefix => Array.from(select.options).find(option => !option.disabled && option.textContent.trim().toLocaleLowerCase().startsWith(prefix));
    trigger.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault(); openDropdown(select, trigger, menu);
        if (event.key === 'ArrowUp') menu.querySelector('.custom-select-option:last-child')?.focus();
      } else if (event.key.length === 1 && !event.metaKey && !event.ctrlKey && !event.altKey) {
        typeahead += event.key.toLocaleLowerCase(); clearTimeout(typeaheadTimer);
        typeaheadTimer = setTimeout(() => {typeahead = '';}, 700);
        const match = matchingOption(typeahead) || matchingOption(event.key.toLocaleLowerCase());
        if (match) {event.preventDefault(); select.value = match.value; select.dispatchEvent(new Event('change', {bubbles:true}));}
      }
    });
    menu.addEventListener('keydown', event => {
      const items = [...menu.querySelectorAll('.custom-select-option:not(:disabled)')];
      const current = items.indexOf(document.activeElement);
      if (event.key === 'Escape') {event.preventDefault();closeCustomDropdown(true);}
      else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault(); items[(current + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
      } else if (event.key.length === 1 && !event.metaKey && !event.ctrlKey && !event.altKey) {
        typeahead += event.key.toLocaleLowerCase(); clearTimeout(typeaheadTimer);
        typeaheadTimer = setTimeout(() => {typeahead = '';}, 700);
        const match = matchingOption(typeahead) || matchingOption(event.key.toLocaleLowerCase());
        if (match) menu.querySelectorAll('.custom-select-option').forEach(item => {
          if (item.textContent === match.textContent) item.focus();
        });
      }
    });
    syncCustomDropdown(select);
  });
  document.addEventListener('pointerdown', event => {
    if (openCustomDropdown && !openCustomDropdown.menu.contains(event.target) && !openCustomDropdown.trigger.contains(event.target)) closeCustomDropdown();
  });
  document.addEventListener('keydown', event => {if (event.key === 'Escape') closeCustomDropdown(true);});
  window.addEventListener('resize', () => closeCustomDropdown());
  window.addEventListener('scroll', event => {
    if (openCustomDropdown && !openCustomDropdown.menu.contains(event.target)) closeCustomDropdown();
  }, true);
}
const BET_PAIRS=['1-2','1-3','1-4','1-5','1-6','2-3','2-4','2-5','2-6','3-4','3-5','3-6','4-5','4-6','5-6'];
const BADGE_NAMES=['i','ii','iii'];
const JOCKEY_RANKS={Bronze:1,Silver:2,Gold:3,Platinum:4};
function renderBetGrid(rank, cards = null, predictedPairs = [], bronzeChocoboNumbers = []) {
  const grid=document.querySelector('#bet-grid'); grid.replaceChildren();
  BET_PAIRS.forEach((pair,index)=>{
    const cell=document.createElement('div');cell.className='bet-cell';cell.setAttribute('aria-label',`Chocobos ${pair}`);
    const hasBronze=pair.split('-').some(number=>bronzeChocoboNumbers.includes(Number(number)));
    if(hasBronze){cell.classList.add('has-bronze');cell.setAttribute('aria-label',`Chocobos ${pair} · includes bronze jockey`);}
    if(predictedPairs.includes(pair)){
      cell.classList.add('is-predicted');
      cell.setAttribute('aria-label',`Chocobos ${pair} · suggested bet${cell.classList.contains('has-bronze')?' · includes bronze jockey':''}`);
    }
    const tile=document.createElement('img');tile.className='tile-image';tile.alt='';
    const classKey=rank.toLowerCase();
    tile.src=`assets/class-${classKey}/tiles/${pair}.png`;
    tile.onerror=()=>{tile.onerror=null;tile.src=`assets/class-${classKey==='c'?'b':'c'}/tiles/${pair}.png`;};
    cell.append(tile);
    if(cards && cards[index]!==undefined){
      const isRomanClass=rank==='C';
      const badgeNames=isRomanClass?BADGE_NAMES:['one','two','three'];
      const badgeFolder=isRomanClass?'badges':'item-icons';
      const badgeName=badgeNames[cards[index]];
      const badge=document.createElement('img');badge.className='bet-badge';badge.alt=`Prize ${cards[index]+1}`;
      badge.src=`assets/class-${classKey}/${badgeFolder}/${badgeName}.png`;
      badge.onerror=()=>{badge.onerror=null;badge.src=`assets/class-b/${badgeFolder}/${badgeName}.png`;};
      cell.append(badge);
    }
    grid.append(cell);
  });
}
function predictWinnerBets(race) {
  const racers=race.chocobos.map((choco,index)=>{
    const jockey=AI_JOCKEY_COLORS[choco.aiType];
    return {index:index+1,name:race.names[index],speed:choco.displaySpeed,jockey:jockey.label,rank:JOCKEY_RANKS[jockey.label]};
  });
  const remaining=racers.filter(racer=>racer.jockey!=='Bronze');
  remaining.sort((a,b)=>b.speed-a.speed||b.rank-a.rank);
  const topThree=remaining.slice(0,3);
  const pairs=[];
  for(let first=0;first<topThree.length;first++){
    for(let second=first+1;second<topThree.length;second++){
      pairs.push([topThree[first].index,topThree[second].index].sort((a,b)=>a-b).join('-'));
    }
  }
  return {topThree,pairs};
}
function renderPredictions(race=null) {
  return race?predictWinnerBets(race).pairs:[];
}
function possiblePrizeSlots(rank) {
  const modesByGift = new Map();
  for (const [giftId, , , moveToLast] of REWARD_TABLES[rank]) {
    if (!modesByGift.has(giftId)) modesByGift.set(giftId, new Set());
    modesByGift.get(giftId).add(moveToLast !== 0);
  }
  const regularGifts = [...modesByGift]
    .filter(([, modes]) => modes.has(false))
    .map(([giftId]) => giftId)
    .sort((a, b) => a - b);
  const specialGifts = [...modesByGift]
    .filter(([, modes]) => modes.has(true))
    .map(([giftId]) => giftId);
  const possible = [new Set(), new Set(), new Set()];

  // With no move-to-last reward, the three selected gifts sort by gift ID.
  for (let first = 0; first < regularGifts.length; first++) {
    for (let second = first + 1; second < regularGifts.length; second++) {
      for (let third = second + 1; third < regularGifts.length; third++) {
        possible[0].add(regularGifts[first]);
        possible[1].add(regularGifts[second]);
        possible[2].add(regularGifts[third]);
      }
    }
  }

  // A move-to-last reward is placed in slot III; the other two sort normally.
  for (const finalGift of specialGifts) {
    const others = regularGifts.filter(giftId => giftId !== finalGift);
    for (let first = 0; first < others.length; first++) {
      for (let second = first + 1; second < others.length; second++) {
        possible[0].add(others[first]);
        possible[1].add(others[second]);
        possible[2].add(finalGift);
      }
    }
  }
  return possible;
}
function rankOptions(rank) {
  const [dashBase,dashRange] = CHOCO_STAT_TABLE[rank];
  const staminaBase = dashBase;
  const speeds = [...new Set(Array.from({length:dashRange},(_,n)=>Math.trunc((dashBase+n)/34)))].sort((a,b)=>a-b);
  const stamina = [...new Set(Array.from({length:300},(_,n)=>Math.trunc((staminaBase+n)/10)))].sort((a,b)=>a-b);
  makeOptions(speedSelect,speeds,speeds[0]);
  makeOptions(staminaSelect,stamina,stamina[0]);
  const gifts = [...new Set(REWARD_TABLES[rank].map(item=>item[0]))].sort((a,b)=>PRIZE_NAMES[a].localeCompare(PRIZE_NAMES[b]));
  const possibleBySlot = possiblePrizeSlots(rank);
  prizeSelects.forEach((select,index)=>{
    const any=document.createElement('option');any.value='';any.textContent='Any gift';any.selected=true;
    const options=gifts.map(id=>{const option=document.createElement('option');option.value=id;option.textContent=PRIZE_NAMES[id];option.dataset.slotPossible=String(possibleBySlot[index].has(id));return option;});
    select.replaceChildren(any,...options);prizeFilters[index]=null;
  });
}
// The source generator shuffles range(43), so JULIA (the final display-name
// entry in its table) is not part of the generated field.
makeOptions(nameSelect,RACER_NAMES.slice(0,43).sort((a,b)=>a.localeCompare(b)), 'SAM');
rankOptions(rankSelect.value);
initializeCustomDropdowns();
rankSelect.addEventListener('change',()=>{lastFoundFrame=null;keepSearchingButton.hidden=true;rankOptions(rankSelect.value);renderDefaultClass();});
prizeSelects.forEach((select,index)=>select.addEventListener('change',()=>{prizeFilters[index]=select.value===''?null:Number(select.value);}));

function rng(seed) {
  let state = seed >>> 0;
  return () => { state = (Math.imul(0x41c64e6d,state) + 0x3039) >>> 0; return (state >>> 16) & 0x7fff; };
}
function generateRaceData(seed, rank) {
  const random = rng(seed);
  for(let i=0;i<0x28;i++){random();random();}
  const [dashBase,dashRange] = CHOCO_STAT_TABLE[rank];
  const chocobos=[];
  for(let i=0;i<6;i++) {
    const dashSpeed=dashBase+(random()%dashRange);
    const speed=CHOCO_STAT_TABLE[rank][2]+(random()%CHOCO_STAT_TABLE[rank][3]);
    const aiType=random()%4;
    const stamina=CHOCO_STAT_TABLE[rank][0]+(random()%300);
    const runningAnimation=(random()&7)===0?2:0;
    const unknown=((random()&1)*50)+50;
    chocobos.push({dashSpeed,speed,aiType,stamina,runningAnimation,unknown,displaySpeed:Math.trunc(dashSpeed/34),displayStamina:Math.trunc(stamina/10)});
  }
  const names=Array.from({length:43},(_,i)=>i);
  for(let i=0;i<0xc8;i++){const a=random()%43,b=random()%43;[names[a],names[b]]=[names[b],names[a]];}
  const rewardTable=REWARD_TABLES[rank];
  const pool=[255,255,255]; let itemsIn=0,s2=0,s3=0xffffffff;
  while(itemsIn!==3) {
    const item=rewardTable[random()%rewardTable.length];
    if(pool.includes(item[0])) continue;
    if(item[1]!==0) {
      if(s2!==0 && item[3]!==0) continue;
      pool[itemsIn++]=item[0];
      if(item[3]===0) continue;
      s3=item[0]; s2=0xffffffff; continue;
    }
    if(s2!==0 && item[3]!==0) continue;
    pool[itemsIn++]=item[0];
    if(item[3]===0) continue;
    s3=item[0]; s2=0xffffffff;
  }
  pool.sort((a,b)=>a-b);
  if(s3!==0xffffffff) {
    if(pool[0]===s3)[pool[0],pool[2]]=[pool[2],pool[0]];
    else if(pool[1]===s3)[pool[1],pool[2]]=[pool[2],pool[1]];
  }
  const tileItems=[],tileCards=[];
  for(let i=0;i<7;i++){tileItems.push(pool[0]);tileCards.push(0);}
  for(let i=0;i<5;i++){tileItems.push(pool[1]);tileCards.push(1);}
  for(let i=0;i<3;i++){tileItems.push(pool[2]);tileCards.push(2);}
  for(let i=0;i<50;i++) for(let j=0;j<2;j++) {const a=random()%15,b=random()%15;[tileItems[a],tileItems[b]]=[tileItems[b],tileItems[a]];[tileCards[a],tileCards[b]]=[tileCards[b],tileCards[a]];}
  return {items:pool,tileCards,names:names.slice(0,6).map(index=>RACER_NAMES[index]),chocobos};
}
function startFrameFromTime() {
  if(exactStartFrameOverride!==null)return exactStartFrameOverride;
  const hours=Math.max(0,Number(document.querySelector('#hours').value)||0);
  const minutes=Math.min(59,Math.max(0,Number(document.querySelector('#minutes').value)||0));
  const seconds=Math.min(59,Math.max(0,Number(document.querySelector('#seconds').value)||0));
  return Math.floor((hours*3600+minutes*60+seconds)*60) % FRAME_CYCLE;
}
['hours','minutes','seconds'].forEach(id=>document.querySelector(`#${id}`).addEventListener('input',()=>{exactStartFrameOverride=null;}));
function formatClock(frame) {const totalSeconds=Math.floor(frame/60),h=Math.floor(totalSeconds/3600),m=Math.floor(totalSeconds%3600/60),s=totalSeconds%60;return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;}
function formatSearchEstimate(frames) {const totalMinutes=Math.floor(frames/3600),hours=Math.floor(totalMinutes/60),minutes=totalMinutes%60;return hours?`${hours}h ${String(minutes).padStart(2,'0')}m`:`${minutes}m`;}
function setBanner(kind,title,detail){resultBanner.className=`result-banner ${kind?`is-${kind}`:''}`;document.querySelector('#result-status').textContent=title;document.querySelector('#result-detail').textContent=detail;document.querySelector('#banner-mark').textContent=kind==='searching'?'◌':kind==='success'?'✓':kind==='error'?'!':'↳';}
function renderDefaultClass(){
  document.body.dataset.rank=rankSelect.value;
  renderBetGrid(rankSelect.value);
  renderPredictions();
  const rankKey=rankSelect.value.toLowerCase();
  document.querySelectorAll('.gift-field img').forEach((icon,index)=>{
    icon.src=`assets/class-${rankKey}/item-icons/${['one','two','three'][index]}.png`;
    icon.onerror=()=>{icon.onerror=null;icon.src=`assets/class-${rankKey==='c'?'b':'c'}/item-icons/${['one','two','three'][index]}.png`;};
  });
  renderPreviewField(rankSelect.value);
  document.querySelector('#frame-value').innerHTML='—<small>FRAME</small>';
  document.querySelector('#frame-time').innerHTML='SINCE RESET <span>00:00:00</span>';
  setBanner('', 'Ready when you are', 'Enter the race menu details to search.');
}
renderDefaultClass();
function renderPreviewField(rank){
  const list=document.querySelector('#race-list');list.replaceChildren();
  for(let index=0;index<6;index++){
    const card=document.createElement('article');card.className='racer-card';
    const markers=document.createElement('div');markers.className='racer-markers';
    const avatar=document.createElement('img');avatar.className=`racer-avatar${index===1?' racer-avatar--2':''}`;avatar.src=`assets/racer-icons/${index+1}.png`;avatar.alt=`Chocobo ${index+1}`;
    const swatch=document.createElement('span');swatch.className='jockey-swatch';swatch.setAttribute('aria-label','Jockey color not found yet');
    markers.append(avatar,swatch);
    const copy=document.createElement('div');copy.className='racer-copy';
    const top=document.createElement('div');top.className='racer-top';
    const no=document.createElement('span');no.className='racer-number';no.textContent=String(index+1).padStart(2,'0');
    const name=document.createElement('span');name.className='racer-name';name.textContent='—';
    const stats=document.createElement('div');stats.className='racer-stats';stats.innerHTML='<span>SPD <b>—</b></span><span>STA <b>—</b></span>';
    const ai=document.createElement('span');ai.className='ai-tag';ai.textContent='—';
    const sprint=document.createElement('span');sprint.className='sprint-tag';sprint.textContent='SPRINT —';
    top.append(no,name);copy.append(top,stats,ai,sprint);card.append(markers,copy);list.append(card);
  }
}
function renderRace(race,frame,rank){
  const predictedPairs=renderPredictions(race);
  const bronzeChocoboNumbers=race.chocobos.flatMap((choco,index)=>AI_JOCKEY_COLORS[choco.aiType].label==='Bronze'?[index+1]:[]);
  renderBetGrid(rank,race.tileCards,predictedPairs,bronzeChocoboNumbers);
  const list=document.querySelector('#race-list'); list.replaceChildren();
  race.chocobos.forEach((choco,index)=>{const card=document.createElement('article');card.className='racer-card';
    const jockey=AI_JOCKEY_COLORS[choco.aiType];
    const avatar=document.createElement('img');avatar.className=`racer-avatar${index===1?' racer-avatar--2':''}`;avatar.src=`assets/racer-icons/${index+1}.png`;avatar.alt=`Chocobo ${index+1}`;
    const swatch=document.createElement('span');swatch.className='jockey-swatch';swatch.style.setProperty('--jockey-color',jockey.color);swatch.setAttribute('aria-label',`${jockey.label} jockey color`);
    const markers=document.createElement('div');markers.className='racer-markers';markers.append(avatar,swatch);
    const copy=document.createElement('div');copy.className='racer-copy';
    const top=document.createElement('div');top.className='racer-top';
    const no=document.createElement('span');no.className='racer-number';no.textContent=String(index+1).padStart(2,'0');
    const name=document.createElement('span');name.className='racer-name';name.textContent=race.names[index];
    const ai=document.createElement('span');ai.className='ai-tag';ai.textContent=jockey.label.toUpperCase();
    top.append(no,name);copy.append(top);
    const stats=document.createElement('div');stats.className='racer-stats';stats.innerHTML=`<span>SPD <b>${choco.displaySpeed}</b></span><span>STA <b>${choco.displayStamina}</b></span>`;
    const sprint=document.createElement('span');sprint.className=`sprint-tag${choco.runningAnimation===2?' is-sprinting':''}`;sprint.textContent=choco.runningAnimation===2?'SPRINTING':'NOT SPRINTING';
    copy.append(stats,ai,sprint);card.append(markers,copy);list.append(card);
  });
  document.querySelector('#frame-value').innerHTML=`${frame.toLocaleString()}<small>FRAME</small>`;
  document.querySelector('#frame-time').innerHTML=`SINCE RESET <span>${formatClock(frame)}</span>`;
}
function matches(race,criteria) {
  const first=race.chocobos[0];
  const matchesChocobo=race.names[0]===criteria.name && first.displaySpeed===criteria.speed && first.displayStamina===criteria.stamina;
  return matchesChocobo && criteria.prizes.every((prize,index)=>prize===null || race.items[index]===prize);
}
function yieldFrame(){return new Promise(resolve=>requestAnimationFrame(()=>setTimeout(resolve,0)));}
function collectCriteria(){
  return {name:nameSelect.value,speed:Number(speedSelect.value),stamina:Number(staminaSelect.value),prizes:prizeFilters.slice()};
}
function confirmGiftSelection(criteria){
  const selected=criteria.prizes.filter(prize=>prize!==null);
  if(new Set(selected).size!==selected.length && !window.confirm('Some gifts are selected more than once. Are you sure you have the right gifts? Continue scanning?')){
    setBanner('error','Check selected gifts','Duplicate gifts found. Search cancelled.');
    return false;
  }
  return true;
}
async function scanFrom(start,criteria,rank){
  cancelSearch=false;searchButton.disabled=true;searchButton.setAttribute('aria-label','Searching');searchButton.textContent='…';cancelButton.hidden=false;
  keepSearchingButton.hidden=true;lastFoundFrame=null;
  document.querySelector('#race-list').innerHTML='<div class="empty-state"><span class="empty-orbit">✳</span><strong>Scanning generated race data</strong><span>Starting at frame '+start.toLocaleString()+'</span></div>';
  const hasGiftFilters=criteria.prizes.some(prize=>prize!==null);
  setBanner('searching','Searching from frame '+start.toLocaleString(),hasGiftFilters?'Checking chocobo details and selected gifts.':'Checking chocobo details; gifts will be filled from each match.');
  let frame=start,attempts=0,found=null;
  while(!cancelSearch && frame<FRAME_CYCLE) {
    const batchStart=performance.now();
    do {
      const race=generateRaceData(frame,rank);
      if(matches(race,criteria)){found={race,frame};break;}
      frame++;attempts++;
    } while(performance.now()-batchStart<14 && !cancelSearch && frame<FRAME_CYCLE);
    if(found||cancelSearch)break;
    if(attempts>0&&attempts%2400<180) setBanner('searching',`${attempts.toLocaleString()} frames checked`,`Currently at frame ${frame.toLocaleString()} · ${formatClock(frame)} since reset.`);
    await yieldFrame();
  }
  searchButton.disabled=false;searchButton.setAttribute('aria-label','Find matching frame');searchButton.textContent='▶';cancelButton.hidden=true;
  if(found){
    renderRace(found.race,found.frame,rank);
    latestDiscoveredFrame=found.frame;
    document.querySelector('#new-race-button').disabled=false;
    huntFrameInput.value=String(found.frame);
    huntRankSelect.value=rank;
    updateHuntPrizes();
    found.race.items.forEach((item,index)=>{prizeSelects[index].value=String(item);syncCustomDropdown(prizeSelects[index]);});
    lastFoundFrame=found.frame;keepSearchingButton.hidden=found.frame+1>=FRAME_CYCLE;
    setBanner('success','Race data matched',`${found.race.names[0]} · ${PRIZE_NAMES[found.race.items[0]]} / ${PRIZE_NAMES[found.race.items[1]]} / ${PRIZE_NAMES[found.race.items[2]]}`);
  }
  else if(cancelSearch){setBanner('',`Search stopped`,`Checked ${attempts.toLocaleString()} frames. Adjust your start time or race details and try again.`);}
  else {
    document.querySelector('#race-list').innerHTML='<div class="empty-state"><strong>No matching frame found</strong><span>Check the PlayStation class, chocobo stats, prizes, and time since power reset.</span></div>';
    setBanner('error','No match found',`Scanned ~${formatSearchEstimate(attempts)} · Check PS data.`);
  }
}
form.addEventListener('submit',event=>{
  event.preventDefault();
  const criteria=collectCriteria();
  if(!confirmGiftSelection(criteria))return;
  scanFrom(startFrameFromTime(),criteria,rankSelect.value);
});
keepSearchingButton.addEventListener('click',()=>{
  if(lastFoundFrame===null)return;
  const criteria=collectCriteria();
  if(!confirmGiftSelection(criteria))return;
  scanFrom(lastFoundFrame+1,criteria,rankSelect.value);
});
cancelButton.addEventListener('click',()=>{cancelSearch=true;cancelButton.disabled=true;cancelButton.textContent='Stopping…';setTimeout(()=>{cancelButton.disabled=false;cancelButton.textContent='Stop search';},200);});

document.querySelector('#new-race-button').addEventListener('click',()=>{
  if(latestDiscoveredFrame===null)return;
  const frame=latestDiscoveredFrame;
  const totalSeconds=frame/60;
  const hours=Math.floor(totalSeconds/3600);
  const minutes=Math.floor((totalSeconds-hours*3600)/60);
  const seconds=totalSeconds-hours*3600-minutes*60;
  document.querySelector('#hours').value=String(hours);
  document.querySelector('#minutes').value=String(minutes);
  document.querySelector('#seconds').value=seconds.toFixed(6);
  exactStartFrameOverride=frame;
  makeOptions(speedSelect,Array.from(speedSelect.options,option=>Number(option.value)),speedSelect.options[0]?.value);
  makeOptions(staminaSelect,Array.from(staminaSelect.options,option=>Number(option.value)),staminaSelect.options[0]?.value);
  makeOptions(nameSelect,Array.from(nameSelect.options,option=>option.value),nameSelect.options[0]?.value);
  [speedSelect,staminaSelect,nameSelect].forEach(syncCustomDropdown);
  prizeSelects.forEach((select,index)=>{select.value='';prizeFilters[index]=null;syncCustomDropdown(select);});
  keepSearchingButton.hidden=true;
  renderBetGrid(rankSelect.value,null,[],[]);
  document.querySelectorAll('#bet-grid .bet-badge').forEach(badge=>badge.remove());
  document.querySelectorAll('#bet-grid .bet-cell').forEach(cell=>cell.classList.remove('has-bronze','is-predicted'));
  renderPreviewField(rankSelect.value);
  setBanner('', 'Ready when you are', 'Inputs are set for the next race.');
});


const huntFrameInput=document.querySelector('#hunt-frame');
const huntRankSelect=document.querySelector('#hunt-rank');
const huntPrizeSelect=document.querySelector('#hunt-prize');
const huntButton=document.querySelector('#hunt-button');
const huntStatus=document.querySelector('#hunt-status');
const huntResults=document.querySelector('#hunt-results');
let huntRunning=false,huntCancel=false;
function updateHuntPrizes(){
  const prizes=[...new Set(REWARD_TABLES[huntRankSelect.value].map(([giftId])=>giftId))]
    .sort((a,b)=>PRIZE_NAMES[a].localeCompare(PRIZE_NAMES[b]));
  makeOptions(huntPrizeSelect,prizes,prizes[0],giftId=>PRIZE_NAMES[giftId]);
}
updateHuntPrizes();
huntRankSelect.addEventListener('change',updateHuntPrizes);
rankSelect.addEventListener('change',()=>{huntRankSelect.value=rankSelect.value;updateHuntPrizes();});
huntButton.addEventListener('click',async()=>{
  if(huntRunning){huntCancel=true;huntButton.disabled=true;huntButton.textContent='Stopping…';return;}
  const start=Number(huntFrameInput.value);
  if(!Number.isInteger(start)||start<0||start>=FRAME_CYCLE){
    huntStatus.textContent=`Enter a frame from 0 to ${(FRAME_CYCLE-1).toLocaleString()}.`;
    huntFrameInput.focus();return;
  }
  const rank=huntRankSelect.value,targetPrize=Number(huntPrizeSelect.value),initialWaitFrames=Number(document.querySelector('#hunt-step').value)*60,wanted=10;
  huntCancel=false;huntRunning=true;huntResults.replaceChildren();
  huntButton.textContent='Stop search';huntRankSelect.disabled=huntPrizeSelect.disabled=huntFrameInput.disabled=document.querySelector('#hunt-step').disabled=true;
  huntStatus.textContent=`Waiting ${document.querySelector('#hunt-step').value} seconds, then searching for ${PRIZE_NAMES[targetPrize]}…`;
  let checked=0,found=0;
  while(checked<FRAME_CYCLE&&found<wanted&&!huntCancel){
    const batchStart=performance.now();
    do{
      const currentOffset=initialWaitFrames+checked;
      const frame=(start+currentOffset)%FRAME_CYCLE;
      const race=generateRaceData(frame,rank);
      const slot=race.items.indexOf(targetPrize);
      checked++;
      if(slot!==-1){
        const winningPairs=predictWinnerBets(race).pairs.filter(pair=>race.tileCards[BET_PAIRS.indexOf(pair)]===slot);
        if(winningPairs.length){
          found++;
          const elapsedLabel=formatClock(currentOffset);
          const row=document.createElement('li');
          const frameLabel=document.createElement('strong');frameLabel.textContent=`Frame ${frame.toLocaleString()}`;
          latestDiscoveredFrame=frame;
          document.querySelector('#new-race-button').disabled=false;
          huntFrameInput.value=String(frame);
          row.append(frameLabel,document.createTextNode(` · ${formatClock(frame)} · +${elapsedLabel} after starting frame · Prize: ${PRIZE_NAMES[targetPrize]} · Green bet`));
          winningPairs.forEach(pair=>{const bet=document.createElement('span');bet.className='hunt-bet';bet.textContent=pair;row.append(bet);});
          huntResults.append(row);
        }
      }
    }while(performance.now()-batchStart<14&&checked<FRAME_CYCLE&&found<wanted&&!huntCancel);
    huntStatus.textContent=`${found}/${wanted} found · checked ${checked.toLocaleString()} frames · next scan at ${((start+initialWaitFrames+checked)%FRAME_CYCLE).toLocaleString()}`;
    if(checked<FRAME_CYCLE&&found<wanted&&!huntCancel)await yieldFrame();
  }
  huntRunning=false;huntRankSelect.disabled=huntPrizeSelect.disabled=huntFrameInput.disabled=document.querySelector('#hunt-step').disabled=false;
  huntButton.disabled=false;huntButton.textContent='Find next 10';
  if(huntCancel)huntStatus.textContent=`Stopped · found ${found} · checked ${checked.toLocaleString()} frames.`;
  else if(found===wanted)huntStatus.textContent=`Found the next ${wanted} potentially winnable frames with your prize`;
  else huntStatus.textContent=`Searched a full frame cycle after the initial wait · found ${found} tryable frame${found===1?'':'s'} after checking ${checked.toLocaleString()} frames.`;
});

